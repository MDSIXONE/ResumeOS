"""Inbox Orchestrator — Sprint 3, ADR-0019.

ORCHESTRATES the Inbox → Importer → Artifact → Event → Archive → Receipt
workflow.  This module NEVER parses files; file parsing is the sole
responsibility of ``runtime.importer.pipeline.ImporterPipeline``.

Hard constraints enforced by ``test_inbox_constraints.py`` (CI):
    - NO pypdf / docx / PIL / Pillow / fitz / pdfplumber imports.
    - NO skills/ imports.
    - NO LLM SDK imports.
"""

from __future__ import annotations

import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from runtime.artifacts.base import ArtifactProvenance
from runtime.inbox.state import InboxState
from runtime.receipt import ImportReceipt


class InboxOrchestrator:
    """Orchestrates Inbox → Importer → Artifact → Event → Archive → Receipt.

    This is the Inbox Skill (ADR-0019).  It ORCHESTRATES — it never
    parses files.  File parsing is the Importer's job
    (``runtime/importer/``).

    Lifecycle per file:
        DETECTED → QUEUED → IMPORTING → IMPORTED → PUBLISHED → ARCHIVED
        (or IMPORT_FAILED on error; duplicate → no archive / no event)

    Args:
        inbox_dir: Directory to scan for incoming files.
        archive_dir: Directory to move originals after successful import.
        pipeline: ``ImporterPipeline`` instance — the ONLY file processor.
        bus: ``EventBus`` instance for publishing domain events.
        receipt_dir: Directory for saving ``ImportReceipt`` JSON files.
        hash_index_path: JSONL file tracking previously-seen SHA-256 hashes
            for deduplication.
    """

    def __init__(
        self,
        inbox_dir: Path,
        archive_dir: Path,
        pipeline: Any,
        bus: Any,
        receipt_dir: Path,
        hash_index_path: Path,
    ) -> None:
        self.inbox_dir = Path(inbox_dir)
        self.archive_dir = Path(archive_dir)
        self.pipeline = pipeline
        self.bus = bus
        self.receipt_dir = Path(receipt_dir)
        self.hash_index_path = Path(hash_index_path)

        # State tracking: path → current InboxState
        self._states: Dict[Path, InboxState] = {}
        # Full transition history: path → [InboxState, ...]
        self.state_history: Dict[Path, List[InboxState]] = {}
        # In-memory set of known hashes for O(1) dedup lookups
        self._hash_set: Set[str] = set()

        # Load existing hash index from disk (JSONL)
        self._load_hash_index()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self) -> List[Path]:
        """List all non-hidden files in ``inbox_dir`` (no subdirectories).

        Each discovered file is transitioned to ``DETECTED`` and recorded
        in ``state_history``.

        Returns:
            Sorted list of file paths found in the inbox.
        """
        files: List[Path] = []
        if not self.inbox_dir.exists():
            return files
        for p in sorted(self.inbox_dir.iterdir()):
            if p.is_file() and not p.name.startswith("."):
                files.append(p)
                self._set_state(p, InboxState.DETECTED)
        return files

    def process_batch(self, max_workers: int = 4) -> List[ImportReceipt]:
        """Scan the inbox and process every file in one call.

        Args:
            max_workers: Accepted for forward-compatibility (parallel
                processing is a future optimisation).  Sprint 3 uses
                sequential execution.

        Returns:
            One ``ImportReceipt`` per file scanned.
        """
        # 1. Scan → DETECTED
        files = self.scan()

        # 2. Transition all to QUEUED
        for f in files:
            self._set_state(f, InboxState.QUEUED)

        # 3. Process each file sequentially
        receipts: List[ImportReceipt] = []
        for f in files:
            receipt = self.process_one(f)
            receipts.append(receipt)
        return receipts

    def process_one(self, path: Path) -> ImportReceipt:
        """Process a single file through the full pipeline.

        State transitions: QUEUED → IMPORTING → IMPORTED → PUBLISHED → ARCHIVED
        On failure:         … → IMPORT_FAILED
        On duplicate:       … → (duplicate_skipped, no archive / no event)

        Args:
            path: Path to the file to process (must exist in inbox).

        Returns:
            ``ImportReceipt`` recording the outcome.
        """
        path = Path(path)
        start_time = time.monotonic()
        sha256 = ""

        try:
            # → IMPORTING
            self._set_state(path, InboxState.IMPORTING)

            # 1. Compute SHA-256
            sha256 = ArtifactProvenance.hash_file(path)

            # 2. Check for duplicate
            if self._is_duplicate(sha256):
                duration_ms = int((time.monotonic() - start_time) * 1000)
                receipt = ImportReceipt(
                    source_path=str(path),
                    source_hash=sha256,
                    duration_ms=duration_ms,
                    confidence="inferred",
                    status="duplicate_skipped",
                )
                receipt.save(self.receipt_dir / f"{receipt.receipt_id}.json")
                return receipt

            # 3. Run the Importer pipeline → Artifact
            artifact = self.pipeline.run(path)
            self._set_state(path, InboxState.IMPORTED)

            # 4. Publish ArtifactImported event → PUBLISHED
            self.bus.publish(
                "ArtifactImported",
                payload={
                    "artifact_type": artifact.artifact_type,
                    "source_hash": sha256,
                },
                source_skill="inbox_ingest",
                entity_refs=[{
                    "entity_type": artifact.artifact_type,
                    "entity_id": artifact.provenance.source_path,
                }],
            )
            self._set_state(path, InboxState.PUBLISHED)

            # 5. Archive original: archive_dir / <detected_type> / <filename>
            detected_type = artifact.provenance.detected_type
            archive_subdir = self.archive_dir / detected_type
            archive_subdir.mkdir(parents=True, exist_ok=True)
            dest = archive_subdir / path.name
            shutil.move(str(path), str(dest))
            self._set_state(path, InboxState.ARCHIVED)

            # 6. Build and save receipt
            duration_ms = int((time.monotonic() - start_time) * 1000)
            receipt = ImportReceipt(
                artifact_id=sha256,
                source_path=str(path),
                archived_path=str(dest),
                source_hash=sha256,
                detected_type=detected_type,
                extractor=artifact.provenance.extractor,
                duration_ms=duration_ms,
                warnings=[],
                confidence="inferred",
                created_events=["ArtifactImported"],
                status="success",
            )
            receipt.save(self.receipt_dir / f"{receipt.receipt_id}.json")

            # 7. Append hash to index (dedup for future runs)
            self._append_hash(sha256, path.name)

            return receipt

        except Exception as exc:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            self._set_state(path, InboxState.IMPORT_FAILED)

            receipt = ImportReceipt(
                source_path=str(path),
                source_hash=sha256,
                duration_ms=duration_ms,
                status="failed",
                error=str(exc),
                confidence="inferred",
            )
            receipt.save(self.receipt_dir / f"{receipt.receipt_id}.json")
            return receipt

    def get_state(self, path: Path) -> Optional[InboxState]:
        """Return current state for a tracked path, or ``None``."""
        return self._states.get(path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_state(self, path: Path, state: InboxState) -> None:
        """Update state and record transition in history."""
        self._states[path] = state
        self.state_history.setdefault(path, []).append(state)

    def _is_duplicate(self, sha256: str) -> bool:
        """Check if a SHA-256 hash has been seen before."""
        return sha256 in self._hash_set

    def _append_hash(self, sha256: str, filename: str) -> None:
        """Record a hash in the index (in-memory set + JSONL file)."""
        self._hash_set.add(sha256)
        self.hash_index_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "sha256": sha256,
            "filename": filename,
            "first_seen": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.hash_index_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _load_hash_index(self) -> None:
        """Load existing hash index from JSONL into in-memory set."""
        if not self.hash_index_path.exists():
            return
        with open(self.hash_index_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    self._hash_set.add(entry["sha256"])
