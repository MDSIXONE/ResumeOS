"""Unit tests for EventTransaction -- beyond the acceptance test."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.event_bus import EventBus
from runtime.transaction import EventTransaction


@pytest.fixture
def bus(tmp_path):
    return EventBus(events_log=tmp_path / "events.jsonl")


class TestEventTransactionUnits:
    def test_empty_commit_returns_empty_list(self, bus):
        tx = EventTransaction(bus)
        delivered = tx.commit()
        assert delivered == []

    def test_multiple_publishes_then_commit_delivers_all_in_order(self, bus):
        received = []
        bus.subscribe("*", lambda e: received.append(e["type"]))
        tx = EventTransaction(bus)
        tx.publish("A", payload={}, source_skill="t")
        tx.publish("B", payload={}, source_skill="t")
        tx.publish("C", payload={}, source_skill="t")
        delivered = tx.commit()
        assert [e["type"] for e in delivered] == ["A", "B", "C"]
        assert received == ["A", "B", "C"]

    def test_rollback_clears_staged_events(self, bus):
        received = []
        bus.subscribe("*", lambda e: received.append(e))
        tx = EventTransaction(bus)
        tx.publish("A", payload={}, source_skill="t")
        tx.rollback()
        tx.commit()  # nothing to commit
        assert received == []

    def test_commit_clears_staged_so_second_commit_is_empty(self, bus):
        received = []
        bus.subscribe("*", lambda e: received.append(e))
        tx = EventTransaction(bus)
        tx.publish("A", payload={}, source_skill="t")
        tx.commit()
        # second commit with no new staging
        second = tx.commit()
        assert second == []
        assert len(received) == 1

    def test_commit_persists_to_events_jsonl(self, bus, tmp_path):
        tx = EventTransaction(bus)
        tx.publish("A", payload={"x": 1}, source_skill="t")
        tx.publish("B", payload={"y": 2}, source_skill="t")
        tx.commit()
        events = bus.events()
        assert len(events) == 2
        assert events[0]["type"] == "A"
        assert events[1]["type"] == "B"

    def test_rollback_does_not_persist(self, bus):
        tx = EventTransaction(bus)
        tx.publish("A", payload={}, source_skill="t")
        tx.publish("B", payload={}, source_skill="t")
        tx.rollback()
        assert bus.events() == []

    def test_can_rollback_after_partial_failure(self, bus):
        """Publish 3, rollback, publish 1, commit -> only 1 delivered."""
        received = []
        bus.subscribe("*", lambda e: received.append(e["type"]))
        tx = EventTransaction(bus)
        tx.publish("A", payload={}, source_skill="t")
        tx.publish("B", payload={}, source_skill="t")
        tx.publish("C", payload={}, source_skill="t")
        tx.rollback()
        tx.publish("D", payload={}, source_skill="t")
        tx.commit()
        assert received == ["D"]
        assert len(bus.events()) == 1

    def test_entity_refs_carried_through_commit(self, bus):
        received = []
        bus.subscribe("*", lambda e: received.append(e))
        refs = [{"entity_type": "project", "entity_id": "demo"}]
        tx = EventTransaction(bus)
        tx.publish("A", payload={}, source_skill="t", entity_refs=refs)
        tx.commit()
        assert received[0]["entity_refs"] == refs

    def test_time_field_is_iso8601(self, bus):
        tx = EventTransaction(bus)
        tx.publish("A", payload={}, source_skill="t")
        delivered = tx.commit()
        # ISO 8601 contains 'T' and timezone offset
        assert "T" in delivered[0]["time"]
