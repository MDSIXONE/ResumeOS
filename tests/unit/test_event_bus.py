"""Unit tests for :mod:`runtime.event_bus`.

These tests complement the acceptance tests in
``tests/integration/test_runtime_smoke.py::TestEventBus`` by exercising
edge cases:
    - Multiple subscribers for the same event type all receive the event.
    - A handler that raises does not crash the bus or other handlers.
    - ``entity_refs`` flows through to the persisted event.
    - Events are persisted in chronological order.
    - Wildcard + specific-topic subscriptions both fire for the same event.
    - ``events()`` returns [] on a fresh log that was never written to.
    - ``Entity refs`` defaults to [] when not provided.

Per ADR-0014 (Event Bus) + schemas/runtime/event.schema.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.event_bus import EventBus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def log_path(tmp_path):
    """Fresh events.jsonl path under a temp directory."""
    return tmp_path / ".library" / "events.jsonl"


@pytest.fixture
def bus(log_path):
    """EventBus wired to a temp events.jsonl."""
    return EventBus(events_log=log_path)


# ---------------------------------------------------------------------------
# Multiple subscribers
# ---------------------------------------------------------------------------


class TestMultipleSubscribers:
    """All handlers subscribed to a topic receive the event."""

    def test_two_handlers_same_topic(self, bus):
        a, b = [], []
        bus.subscribe("ProjectImported", lambda e: a.append(e))
        bus.subscribe("ProjectImported", lambda e: b.append(e))
        bus.publish("ProjectImported", payload={"x": 1}, source_skill="t")
        assert len(a) == 1
        assert len(b) == 1
        assert a[0]["type"] == "ProjectImported"
        assert b[0]["type"] == "ProjectImported"

    def test_wildcard_and_specific_both_fire(self, bus):
        """Wildcard + topic-specific for the same event both fire."""
        specific, wildcard = [], []
        bus.subscribe("ProjectImported", lambda e: specific.append(e))
        bus.subscribe("*", lambda e: wildcard.append(e))
        bus.publish("ProjectImported", payload={}, source_skill="t")
        assert len(specific) == 1
        assert len(wildcard) == 1

    def test_handler_identity_preserved(self, bus):
        """The event dict is the same object passed to both handlers
        within a single publish (no deep copy)."""
        received = []
        bus.subscribe("X", lambda e: received.append(e))
        bus.subscribe("*", lambda e: received.append(e))
        bus.publish("X", payload={"k": 1}, source_skill="s")
        assert received[0] is received[1]


# ---------------------------------------------------------------------------
# Handler exceptions
# ---------------------------------------------------------------------------


class TestHandlerExceptions:
    """A failing handler must not crash the bus."""

    def test_raising_handler_does_not_break_bus(self, bus):
        def bad(_evt):
            raise ValueError("boom")

        after = []
        bus.subscribe("E", bad)
        bus.subscribe("E", lambda e: after.append(e))
        bus.publish("E", payload={}, source_skill="s")  # must not raise
        assert len(after) == 1

    def test_raising_handler_does_not_block_persistence(self, bus, log_path):
        """Even if a handler raises, the event is still persisted."""

        def bad(_evt):
            raise RuntimeError("nope")

        bus.subscribe("E", bad)
        bus.publish("E", payload={"persisted": True}, source_skill="s")
        events = bus.events()
        assert len(events) == 1
        assert events[0]["payload"]["persisted"] is True

    def test_multiple_raising_handlers(self, bus):
        """Several bad handlers + one good one: good still runs."""

        def bad(_evt):
            raise RuntimeError("handler error")

        good = []
        bus.subscribe("E", bad)
        bus.subscribe("E", bad)
        bus.subscribe("E", lambda e: good.append(e))
        bus.publish("E", payload={}, source_skill="s")
        assert len(good) == 1


# ---------------------------------------------------------------------------
# Payload / entity_refs
# ---------------------------------------------------------------------------


class TestPayloadAndEntityRefs:
    """Event shape per schemas/runtime/event.schema.json."""

    def test_entity_refs_default_empty(self, bus):
        bus.publish("X", payload={}, source_skill="s")
        events = bus.events()
        assert events[0]["entity_refs"] == []

    def test_entity_refs_roundtrip(self, bus):
        refs = [{"entity_type": "project", "entity_id": "demo"}]
        bus.publish(
            "ProjectImported",
            payload={},
            source_skill="s",
            entity_refs=refs,
        )
        evts = bus.events()
        assert evts[0]["entity_refs"] == refs

    def test_event_has_required_schema_fields(self, bus):
        bus.publish("X", payload={"k": 1}, source_skill="s1")
        event = bus.events()[0]
        # Required by event.schema.json.
        assert "type" in event
        assert "time" in event
        assert "source_skill" in event
        assert "payload" in event
        assert "entity_refs" in event

    def test_source_skill_empty_string_default(self, bus):
        bus.publish("X", payload={})
        event = bus.events()[0]
        assert event["source_skill"] == ""

    def test_payload_preserved_exactly(self, bus):
        payload = {
            "entity_id": "proj-1",
            "nested": {"a": [1, 2, 3]},
            "flag": True,
            "nothing": None,
        }
        bus.publish("P", payload=payload, source_skill="s")
        assert bus.events()[0]["payload"] == payload


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


class TestEventOrdering:
    """Events are persisted in chronological (publish) order."""

    def test_order_matches_publish_order(self, bus):
        for i in range(5):
            bus.publish(
                "E",
                payload={"i": i},
                source_skill="s",
            )
        events = bus.events()
        assert [e["payload"]["i"] for e in events] == [0, 1, 2, 3, 4]

    def test_time_is_monotonic_or_equal(self, bus):
        for i in range(3):
            bus.publish("E", payload={"i": i}, source_skill="s")
        events = bus.events()
        times = [e["time"] for e in events]
        assert times == sorted(times)


# ---------------------------------------------------------------------------
# Persistence edge cases
# ---------------------------------------------------------------------------


class TestPersistenceEdgeCases:
    """events.jsonl append-only behaviour."""

    def test_events_empty_when_no_publishes(self, bus):
        assert bus.events() == []

    def test_events_empty_when_log_file_does_not_exist_yet(self, tmp_path):
        # Construct with a path whose parent exists but file does not.
        bus = EventBus(events_log=tmp_path / "events.jsonl")
        assert bus.events() == []

    def test_append_only_multiple_publishes(self, bus, log_path):
        bus.publish("A", payload={}, source_skill="s")
        bus.publish("B", payload={}, source_skill="s")
        # Raw file line count should equal event count.
        lines = [
            line for line in log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(lines) == 2

    def test_parent_dirs_created_automatically(self, tmp_path):
        deep = tmp_path / "a" / "very" / "deep" / "nested" / "events.jsonl"
        assert not deep.parent.exists()
        EventBus(events_log=deep)
        assert deep.parent.exists()

    def test_non_subscribed_events_still_persist(self, bus):
        bus.publish("Ignored", payload={}, source_skill="s")
        assert len(bus.events()) == 1


# ---------------------------------------------------------------------------
# Wildcard + namespacing sanity
# ---------------------------------------------------------------------------


class TestWildcardAndNamespacing:
    """Wildcard receives events from all specific types."""

    def test_wildcard_receives_once_when_wildcard_published(self, bus):
        """When the event type itself is '*', a wildcard handler fires
        exactly once (not duplicated by specific + wildcard buckets)."""
        got = []
        bus.subscribe("*", lambda e: got.append(e))
        bus.publish("*", payload={}, source_skill="s")
        assert len(got) == 1

    def test_community_namespaced_event_delivered(self, bus):
        """Community events 'plugin-name:EventName' flow normally."""
        got = []
        bus.subscribe("linkedin_importer:ProfileSynced", lambda e: got.append(e))
        bus.publish(
            "linkedin_importer:ProfileSynced",
            payload={"uid": "42"},
            source_skill="linkedin_importer",
        )
        assert len(got) == 1

    def test_wildcard_catches_namespaced(self, bus):
        got = []
        bus.subscribe("*", lambda e: got.append(e))
        bus.publish("com_author:CustomEvent", payload={}, source_skill="c")
        assert len(got) == 1
