"""Unit tests for InboxOrchestrator — Sprint 3.

Tests beyond the acceptance suite in ``tests/integration/``:
    - Scan filtering (files only, no dirs, no hidden)
    - Failure handling (failed receipt generation)
    - Archive organisation by detected_type
    - State transition history
    - Hash index updates
    - Duplicate side-effect isolation (no archive, no event)
    - Empty inbox edge case
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

# Ensure repo root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from runtime.event_bus import EventBus
from runtime.importer.pipeline import ImporterPipeline
from runtime.inbox.orchestrator import InboxOrchestrator, InboxState
from runtime.receipt import ImportReceipt

FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mini_inbox(tmp_path):
    """Minimal inbox with a single readme file."""
    inbox_dir = tmp_path / "inbox"
    archive_dir = tmp_path / "archive"
    receipt_dir = tmp_path / "receipts"
    events_log = tmp_path / "events.jsonl"
    hash_index = tmp_path / "hash-index.jsonl"

    inbox_dir.mkdir()
    archive_dir.mkdir()
    receipt_dir.mkdir()

    shutil.copy(
        FIXTURES_ROOT / "readme" / "sample-readme.md",
        inbox_dir / "readme.md",
    )

    return {
        "inbox_dir": inbox_dir,
        "archive_dir": archive_dir,
        "receipt_dir": receipt_dir,
        "events_log": events_log,
        "hash_index": hash_index,
    }


def _make_orchestrator(cfg):
    """Build an InboxOrchestrator from a mini_inbox config dict."""
    bus = EventBus(events_log=cfg["events_log"])
    pipeline = ImporterPipeline()
    return InboxOrchestrator(
        inbox_dir=cfg["inbox_dir"],
        archive_dir=cfg["archive_dir"],
        pipeline=pipeline,
        bus=bus,
        receipt_dir=cfg["receipt_dir"],
        hash_index_path=cfg["hash_index"],
    )


# ---------------------------------------------------------------------------
# Scan behaviour
# ---------------------------------------------------------------------------

class TestScanBehavior:
    """scan() must find only regular, non-hidden files."""

    def test_scan_finds_only_files_not_dirs(self, mini_inbox):
        # Create a subdirectory next to the readme
        (mini_inbox["inbox_dir"] / "subdir").mkdir()
        orch = _make_orchestrator(mini_inbox)
        files = orch.scan()
        assert len(files) == 1
        assert files[0].name == "readme.md"

    def test_scan_ignores_hidden_files(self, mini_inbox):
        # Create a hidden file that must be skipped
        (mini_inbox["inbox_dir"] / ".gitkeep").touch()
        orch = _make_orchestrator(mini_inbox)
        files = orch.scan()
        assert len(files) == 1
        assert all(f.name != ".gitkeep" for f in files)

    def test_empty_inbox_returns_empty_list(self, mini_inbox):
        # Remove the only file
        (mini_inbox["inbox_dir"] / "readme.md").unlink()
        orch = _make_orchestrator(mini_inbox)
        files = orch.scan()
        assert files == []


# ---------------------------------------------------------------------------
# process_one — success / failure / transitions
# ---------------------------------------------------------------------------

class TestProcessOne:
    """process_one() state machine and edge cases."""

    def test_process_one_failure_generates_failed_receipt(self, mini_inbox):
        # A file with an unsupported extension causes pipeline to raise
        bad_file = mini_inbox["inbox_dir"] / "unknown.xyz"
        bad_file.write_text("this has no extractor", encoding="utf-8")
        orch = _make_orchestrator(mini_inbox)
        receipt = orch.process_one(bad_file)
        assert receipt.status == "failed"
        assert receipt.error != ""
        assert orch.get_state(bad_file) == InboxState.IMPORT_FAILED
        # Receipt must still be persisted
        receipt_files = list(mini_inbox["receipt_dir"].glob("*.json"))
        assert len(receipt_files) == 1

    def test_archive_organized_by_detected_type(self, mini_inbox):
        orch = _make_orchestrator(mini_inbox)
        readme_path = mini_inbox["inbox_dir"] / "readme.md"
        receipt = orch.process_one(readme_path)
        assert receipt.status == "success"
        assert receipt.detected_type == "readme"
        # Original should be at archive_dir/readme/readme.md
        archived = mini_inbox["archive_dir"] / "readme" / "readme.md"
        assert archived.exists()
        # Original must be gone from inbox
        assert not readme_path.exists()

    def test_state_transitions_recorded_in_history(self, mini_inbox):
        orch = _make_orchestrator(mini_inbox)
        readme_path = mini_inbox["inbox_dir"] / "readme.md"
        orch.process_one(readme_path)
        history = orch.state_history[readme_path]
        # Direct process_one call: IMPORTING → IMPORTED → PUBLISHED → ARCHIVED
        assert InboxState.IMPORTING in history
        assert InboxState.IMPORTED in history
        assert InboxState.PUBLISHED in history
        assert InboxState.ARCHIVED in history
        # Verify ordering (first is IMPORTING, last is ARCHIVED)
        assert history[0] == InboxState.IMPORTING
        assert history[-1] == InboxState.ARCHIVED

    def test_hash_index_updated_after_import(self, mini_inbox):
        orch = _make_orchestrator(mini_inbox)
        readme_path = mini_inbox["inbox_dir"] / "readme.md"
        receipt = orch.process_one(readme_path)
        assert receipt.source_hash != ""
        # Hash index file must exist and contain the hash
        assert mini_inbox["hash_index"].exists()
        content = mini_inbox["hash_index"].read_text(encoding="utf-8")
        assert receipt.source_hash in content
        # Verify it's valid JSONL with expected fields
        for line in content.strip().split("\n"):
            entry = json.loads(line)
            assert "sha256" in entry
            assert "filename" in entry
            assert "first_seen" in entry


# ---------------------------------------------------------------------------
# Duplicate isolation
# ---------------------------------------------------------------------------

class TestDuplicateBehavior:
    """Duplicates must NOT archive, must NOT publish events."""

    def test_duplicate_does_not_archive(self, mini_inbox):
        orch = _make_orchestrator(mini_inbox)

        # First import — succeeds, file archived
        readme_path = mini_inbox["inbox_dir"] / "readme.md"
        receipt1 = orch.process_one(readme_path)
        assert receipt1.status == "success"
        assert (mini_inbox["archive_dir"] / "readme" / "readme.md").exists()

        # Re-add same content under a different name
        dup_name = "readme-again.md"
        shutil.copy(
            FIXTURES_ROOT / "readme" / "sample-readme.md",
            mini_inbox["inbox_dir"] / dup_name,
        )
        dup_path = mini_inbox["inbox_dir"] / dup_name

        receipt2 = orch.process_one(dup_path)
        assert receipt2.status == "duplicate_skipped"
        # The duplicate must NOT have been moved to archive
        assert not (mini_inbox["archive_dir"] / "readme" / dup_name).exists()
        # The duplicate file should still be in inbox (not moved)
        assert dup_path.exists()

    def test_duplicate_does_not_publish_event(self, mini_inbox):
        orch = _make_orchestrator(mini_inbox)

        # First import — publishes one event
        readme_path = mini_inbox["inbox_dir"] / "readme.md"
        orch.process_one(readme_path)
        events_after_first = len(orch.bus.events())
        assert events_after_first >= 1

        # Re-add same content
        shutil.copy(
            FIXTURES_ROOT / "readme" / "sample-readme.md",
            mini_inbox["inbox_dir"] / "readme-copy.md",
        )
        dup_path = mini_inbox["inbox_dir"] / "readme-copy.md"
        orch.process_one(dup_path)

        # No new events should have been published for the duplicate
        events_after_second = len(orch.bus.events())
        assert events_after_second == events_after_first


# ---------------------------------------------------------------------------
# Batch via process_batch — transition through QUEUED
# ---------------------------------------------------------------------------

class TestBatchTransitions:
    """process_batch() adds DETECTED + QUEUED before process_one states."""

    def test_batch_full_state_history(self, mini_inbox):
        orch = _make_orchestrator(mini_inbox)
        readme_path = mini_inbox["inbox_dir"] / "readme.md"
        receipts = orch.process_batch()
        assert len(receipts) == 1
        assert receipts[0].status == "success"
        history = orch.state_history[readme_path]
        # Full lifecycle: DETECTED → QUEUED → IMPORTING → IMPORTED → PUBLISHED → ARCHIVED
        expected = [
            InboxState.DETECTED,
            InboxState.QUEUED,
            InboxState.IMPORTING,
            InboxState.IMPORTED,
            InboxState.PUBLISHED,
            InboxState.ARCHIVED,
        ]
        assert history == expected
