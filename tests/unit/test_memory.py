"""Unit tests for runtime.memory (beyond acceptance tests).

Per ADR-0020: These tests verify Memory is append-only, stores only confirmed
answers, includes proper timestamps, and handles multiple entities/topics.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from runtime.memory import Memory


@pytest.fixture
def store_path(tmp_path: Path) -> Path:
    """Return a path to a conversation.jsonl file."""
    return tmp_path / ".library" / "memory" / "conversation.jsonl"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMemoryUnit:
    """Unit tests covering ADR-0020 rules."""

    def test_confidence_always_confirmed(self, store_path: Path) -> None:
        """Every entry stored has confidence='confirmed'."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "Team size?", "5")
        mem.remember("proj-2", "metrics", "FPS?", "30")

        entries = mem.recall()
        assert all(e["confidence"] == "confirmed" for e in entries)

    def test_timestamp_is_iso_format(self, store_path: Path) -> None:
        """Every entry includes a valid ISO 8601 timestamp."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "Team size?", "5")

        entries = mem.recall()
        assert len(entries) == 1
        # Parse the timestamp to verify it's valid ISO format.
        dt = datetime.fromisoformat(entries[0]["timestamp"])
        assert isinstance(dt, datetime)

    def test_recall_all_when_no_filters(self, store_path: Path) -> None:
        """recall() with no filters returns all entries."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "Team size?", "5")
        mem.remember("proj-2", "metrics", "FPS?", "30")
        mem.remember("award-1", "issuer", "Who issued?", "Robotics Org")

        entries = mem.recall()
        assert len(entries) == 3

    def test_multiple_entries_same_entity_different_topics(
        self, store_path: Path
    ) -> None:
        """Multiple entries for the same entity but different topics are all stored."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "Team size?", "5")
        mem.remember("proj-1", "metrics", "FPS?", "30")
        mem.remember("proj-1", "role", "Your role?", "Lead")

        proj1_entries = mem.recall(entity_id="proj-1")
        assert len(proj1_entries) == 3

        # Filter by topic.
        team_entries = mem.recall(entity_id="proj-1", topic="team")
        assert len(team_entries) == 1
        assert team_entries[0]["answer"] == "5"

        metrics_entries = mem.recall(entity_id="proj-1", topic="metrics")
        assert len(metrics_entries) == 1
        assert metrics_entries[0]["answer"] == "30"

    def test_append_only(self, store_path: Path) -> None:
        """Multiple remember() calls append entries; nothing is overwritten."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "Old team?", "3")
        mem.remember("proj-1", "team", "New team?", "5")

        entries = mem.recall(entity_id="proj-1", topic="team")
        assert len(entries) == 2
        # Both entries are preserved in insertion order.
        assert entries[0]["answer"] == "3"
        assert entries[1]["answer"] == "5"

    def test_recall_nonexistent_entity(self, store_path: Path) -> None:
        """recall() returns [] when filtering by a nonexistent entity."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "Team size?", "5")

        entries = mem.recall(entity_id="nonexistent")
        assert entries == []

    def test_recall_nonexistent_topic(self, store_path: Path) -> None:
        """recall() returns [] when filtering by a nonexistent topic."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "Team size?", "5")

        entries = mem.recall(entity_id="proj-1", topic="nonexistent")
        assert entries == []

    def test_entries_stored_in_insertion_order(self, store_path: Path) -> None:
        """recall() returns entries in the order they were stored."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "a", "Q1?", "A1")
        mem.remember("proj-1", "b", "Q2?", "A2")
        mem.remember("proj-1", "c", "Q3?", "A3")

        entries = mem.recall(entity_id="proj-1")
        assert len(entries) == 3
        assert entries[0]["topic"] == "a"
        assert entries[1]["topic"] == "b"
        assert entries[2]["topic"] == "c"

    def test_jsonl_format(self, store_path: Path) -> None:
        """Store file is valid JSON Lines format."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "Team size?", "5")
        mem.remember("proj-2", "metrics", "FPS?", "30")

        lines = store_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            entry = json.loads(line)
            assert isinstance(entry, dict)
            assert "timestamp" in entry
            assert "entity_id" in entry
            assert "topic" in entry
            assert "question" in entry
            assert "answer" in entry
            assert "confidence" in entry

    def test_parent_directories_created(self, store_path: Path) -> None:
        """Parent directories are created if they don't exist."""
        # Ensure the path doesn't exist yet.
        assert not store_path.exists()
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "Team size?", "5")
        # Now the file and parents should exist.
        assert store_path.exists()
        assert store_path.parent.exists()

    def test_recall_empty_store(self, store_path: Path) -> None:
        """recall() returns [] when the store file doesn't exist yet."""
        mem = Memory(store=store_path)
        assert not store_path.exists()
        entries = mem.recall()
        assert entries == []

    def test_required_fields_present(self, store_path: Path) -> None:
        """Every entry has all required fields per ADR-0020."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "Team size?", "5")

        entries = mem.recall()
        assert len(entries) == 1
        entry = entries[0]
        assert "timestamp" in entry
        assert "entity_id" in entry
        assert "topic" in entry
        assert "question" in entry
        assert "answer" in entry
        assert "confidence" in entry
        assert entry["entity_id"] == "proj-1"
        assert entry["topic"] == "team"
        assert entry["question"] == "Team size?"
        assert entry["answer"] == "5"
        assert entry["confidence"] == "confirmed"

    def test_unicode_support(self, store_path: Path) -> None:
        """Unicode characters in questions/answers are preserved."""
        mem = Memory(store=store_path)
        mem.remember("proj-1", "team", "团队规模?", "5人")
        mem.remember("proj-2", "metrics", "帧率?", "30fps")

        entries = mem.recall()
        assert len(entries) == 2
        assert entries[0]["question"] == "团队规模?"
        assert entries[0]["answer"] == "5人"
        assert entries[1]["question"] == "帧率?"
        assert entries[1]["answer"] == "30fps"
