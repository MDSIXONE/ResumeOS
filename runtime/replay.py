"""Replayer -- re-run an import from a saved ImportReceipt.

User directive (Sprint 3, ★★★★★):
    resume replay --from receipt.json

Replays are the Event Bus's most valuable feature for debugging. If an
import failed today, the user does not need to re-upload the file --
they replay from the receipt. The Replayer:

    1. Loads the old ImportReceipt from disk.
    2. If the original source file still exists, re-imports it through
       the ImporterPipeline to produce a fresh Artifact.
    3. Publishes ``ArtifactImported`` via the EventBus.
    4. Returns a NEW ImportReceipt with a fresh ``receipt_id`` and
       ``timestamp`` but the same ``source_hash`` (content-addressed).

If the source file is gone, the replayer cannot re-import; it returns a
receipt with ``status="failed"`` and an explanatory ``error`` field.
No exception is raised -- the failure is recorded in the receipt so the
caller (CLI / dashboard) can surface it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from runtime.event_bus import EventBus
from runtime.importer.pipeline import ImporterPipeline
from runtime.receipt import ImportReceipt


class Replayer:
    """Re-run an import from a saved ImportReceipt.

    Args:
        bus: EventBus to publish the replayed ``ArtifactImported`` event.
        pipeline: ImporterPipeline used to re-import the source file.
    """

    def __init__(self, bus: EventBus, pipeline: ImporterPipeline) -> None:
        self._bus = bus
        self._pipeline = pipeline

    def replay(self, receipt_path: Path) -> ImportReceipt:
        """Replay the import recorded in ``receipt_path``.

        Args:
            receipt_path: Path to a saved ImportReceipt JSON file.

        Returns:
            A new ImportReceipt. ``status="success"`` if the source file
            was found and re-imported; ``status="failed"`` if the source
            file is gone; ``status="duplicate_skipped"`` is never
            produced by replay (the hash-index check is the
            Orchestrator's responsibility, not the Replayer's).
        """
        old = ImportReceipt.load(Path(receipt_path))

        # Attempt to locate the original source file.
        # Try archived_path first (where the file permanently lives after
        # processing), then the original source_path, then CWD-relative.
        candidates = []
        if old.archived_path:
            candidates.append(Path(old.archived_path))
        candidates.append(Path(old.source_path))
        candidates.append(Path.cwd() / old.source_path)
        source: Optional[Path] = None
        for cand in candidates:
            if cand.exists() and cand.is_file():
                source = cand
                break

        if source is None:
            return ImportReceipt(
                artifact_id="",
                source_path=old.source_path,
                source_hash=old.source_hash,
                detected_type=old.detected_type,
                extractor=old.extractor,
                confidence="missing",
                created_events=[],
                status="failed",
                error=(
                    f"source file no longer exists: {old.source_path} "
                    "(replay requires the original file)"
                ),
            )

        # Re-import through the pipeline.
        try:
            artifact = self._pipeline.run(source)
            artifact_id = getattr(artifact, "artifact_type", "") + "-" + old.source_hash[:12]
            extractor = (
                getattr(artifact.provenance, "extractor", "") or old.extractor
            )
            detected = (
                getattr(artifact.provenance, "detected_type", "") or old.detected_type
            )
        except Exception as exc:  # noqa: BLE001 - record, don't crash
            return ImportReceipt(
                artifact_id="",
                source_path=old.source_path,
                source_hash=old.source_hash,
                detected_type=old.detected_type,
                extractor=old.extractor,
                confidence="missing",
                created_events=[],
                status="failed",
                error=f"re-import failed: {exc}",
            )

        # Publish the replayed event.
        self._bus.publish(
            "ArtifactImported",
            payload={
                "artifact_id": artifact_id,
                "source_hash": old.source_hash,
                "replay_of": old.receipt_id,
            },
            source_skill="replayer",
            entity_refs=[
                {"entity_type": detected, "entity_id": old.source_hash[:12]}
            ],
        )

        return ImportReceipt(
            artifact_id=artifact_id,
            source_path=old.source_path,
            source_hash=old.source_hash,
            detected_type=detected,
            extractor=extractor,
            confidence="inferred",
            created_events=["ArtifactImported"],
            status="success",
        )
