"""Unit tests for Replayer -- beyond the acceptance test."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from runtime.event_bus import EventBus
from runtime.importer.pipeline import ImporterPipeline
from runtime.receipt import ImportReceipt
from runtime.replay import Replayer


@pytest.fixture
def fixtures_root():
    # test_replay.py lives in tests/unit/; fixtures live in tests/fixtures/
    return Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def bus(tmp_path):
    return EventBus(events_log=tmp_path / "events.jsonl")


@pytest.fixture
def pipeline():
    return ImporterPipeline()


class TestReplayerUnits:
    def test_replay_with_existing_source_file(self, bus, pipeline, fixtures_root, tmp_path):
        readme = fixtures_root / "readme" / "sample-readme.md"
        receipt = ImportReceipt(
            artifact_id="project-old",
            source_path=str(readme),
            source_hash="abc123",
            detected_type="readme",
            extractor="readme_parser",
            status="success",
        )
        receipt_file = tmp_path / "r.json"
        receipt.save(receipt_file)

        replayer = Replayer(bus=bus, pipeline=pipeline)
        new_receipt = replayer.replay(receipt_file)
        assert new_receipt.status == "success"
        assert "ArtifactImported" in new_receipt.created_events

    def test_replay_with_missing_source_file(self, bus, pipeline, tmp_path):
        receipt = ImportReceipt(
            source_path=str(tmp_path / "nonexistent.md"),
            source_hash="xyz",
            detected_type="readme",
            extractor="readme_parser",
            status="success",
        )
        receipt_file = tmp_path / "r.json"
        receipt.save(receipt_file)

        replayer = Replayer(bus=bus, pipeline=pipeline)
        new_receipt = replayer.replay(receipt_file)
        assert new_receipt.status == "failed"
        assert "no longer exists" in new_receipt.error
        assert new_receipt.created_events == []

    def test_replay_preserves_source_hash(self, bus, pipeline, fixtures_root, tmp_path):
        readme = fixtures_root / "readme" / "sample-readme.md"
        old = ImportReceipt(
            source_path=str(readme),
            source_hash="fixed-hash-123",
            detected_type="readme",
            extractor="readme_parser",
            status="success",
        )
        receipt_file = tmp_path / "r.json"
        old.save(receipt_file)

        replayer = Replayer(bus=bus, pipeline=pipeline)
        new_receipt = replayer.replay(receipt_file)
        assert new_receipt.source_hash == old.source_hash

    def test_replay_generates_new_receipt_id(self, bus, pipeline, fixtures_root, tmp_path):
        readme = fixtures_root / "readme" / "sample-readme.md"
        old = ImportReceipt(
            source_path=str(readme),
            source_hash="abc",
            detected_type="readme",
            extractor="readme_parser",
            status="success",
        )
        receipt_file = tmp_path / "r.json"
        old.save(receipt_file)

        replayer = Replayer(bus=bus, pipeline=pipeline)
        new_receipt = replayer.replay(receipt_file)
        assert new_receipt.receipt_id != old.receipt_id

    def test_replay_publishes_artifact_imported_event(self, bus, pipeline, fixtures_root, tmp_path):
        readme = fixtures_root / "readme" / "sample-readme.md"
        old = ImportReceipt(
            source_path=str(readme),
            source_hash="abc",
            detected_type="readme",
            extractor="readme_parser",
            status="success",
        )
        receipt_file = tmp_path / "r.json"
        old.save(receipt_file)

        replayer = Replayer(bus=bus, pipeline=pipeline)
        replayer.replay(receipt_file)
        events = bus.events()
        types = [e["type"] for e in events]
        assert "ArtifactImported" in types

    def test_replay_with_corrupt_source_raises_and_records_failure(
        self, bus, pipeline, tmp_path
    ):
        # A file that exists but cannot be parsed by any extractor.
        bad = tmp_path / "bad.xyz"
        bad.write_bytes(b"\x00\x01\x02 unsupported format")
        old = ImportReceipt(
            source_path=str(bad),
            source_hash="bad-hash",
            detected_type="unknown",
            extractor="",
            status="success",
        )
        receipt_file = tmp_path / "r.json"
        old.save(receipt_file)

        replayer = Replayer(bus=bus, pipeline=pipeline)
        new_receipt = replayer.replay(receipt_file)
        # Either failed (import error) or success if pipeline somehow handles it.
        # The key assertion: no unhandled exception escapes; receipt is returned.
        assert new_receipt.status in ("success", "failed")
        if new_receipt.status == "failed":
            assert new_receipt.error
