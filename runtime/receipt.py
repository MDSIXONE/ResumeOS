"""ImportReceipt — the auditable record of one import operation.

Every file processed by the Inbox Orchestrator (Sprint 3) produces
exactly one ImportReceipt. The receipt is the SINGLE source of truth
for "what happened to this file" — it records the artifact produced,
events fired, duration, warnings, and status.

Use cases (user directive, Sprint 3 review):
    - Dashboard: count receipts by status (queued / importing / archived).
    - Replay: ``resume replay --from receipt.json`` re-runs the workflow.
    - Audit: every import is traceable end-to-end.
    - Debug: warnings + error fields surface extractor issues.

No ADR — this is an implementation detail of ADR-0019 + ADR-0014,
encoded in code and tests.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ImportReceipt:
    """Auditable record of one import operation."""

    receipt_id: str = ""
    """Unique ID (UUID4 hex). Auto-generated if empty."""

    artifact_id: str = ""
    """ID of the Artifact produced (empty if failed before artifact creation)."""

    source_path: str = ""
    """Original file path where the user dropped it (relative to vault root, forward slashes)."""

    archived_path: str = ""
    """Where the original was moved after archiving (archive_dir/<type>/<filename>).
    Empty if not archived (e.g. duplicate_skipped) or failed before archive.
    Replay uses this to locate the file for re-import."""

    source_hash: str = ""
    """SHA-256 of the source file (dedup key)."""

    detected_type: str = ""
    """The detected_type from the Detector (13-type enum)."""

    extractor: str = ""
    """Name of the extractor that ran."""

    duration_ms: int = 0
    """Wall-clock duration of the import in milliseconds."""

    warnings: List[str] = field(default_factory=list)
    """Non-fatal issues (e.g. 'OCR low confidence', 'no EXIF date')."""

    confidence: str = "inferred"
    """ADR-0007 confidence: confirmed | inferred | missing."""

    created_events: List[str] = field(default_factory=list)
    """Event types fired during this import (e.g. ['ArtifactImported'])."""

    workflow_id: str = ""
    """Workflow triggered by this import (empty if none)."""

    status: str = "success"
    """success | failed | duplicate_skipped."""

    error: str = ""
    """Error message if status == 'failed', else empty."""

    timestamp: str = ""
    """ISO 8601 of when the receipt was finalized. Auto-filled if empty."""

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def __post_init__(self):
        if not self.receipt_id:
            self.receipt_id = uuid.uuid4().hex
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def serialize(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ImportReceipt":
        return cls(
            receipt_id=d.get("receipt_id", ""),
            artifact_id=d.get("artifact_id", ""),
            source_path=d.get("source_path", ""),
            archived_path=d.get("archived_path", ""),
            source_hash=d.get("source_hash", ""),
            detected_type=d.get("detected_type", ""),
            extractor=d.get("extractor", ""),
            duration_ms=d.get("duration_ms", 0),
            warnings=d.get("warnings", []),
            confidence=d.get("confidence", "inferred"),
            created_events=d.get("created_events", []),
            workflow_id=d.get("workflow_id", ""),
            status=d.get("status", "success"),
            error=d.get("error", ""),
            timestamp=d.get("timestamp", ""),
        )

    @classmethod
    def deserialize(cls, raw: str) -> "ImportReceipt":
        return cls.from_dict(json.loads(raw))

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        """Save receipt as JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.serialize(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "ImportReceipt":
        """Load receipt from JSON file."""
        return cls.deserialize(path.read_text(encoding="utf-8"))
