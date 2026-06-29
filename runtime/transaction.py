"""EventTransaction -- atomic event staging with commit/rollback semantics.

User directive (Sprint 3): if an import chain fires multiple events
(ArtifactImported -> KnowledgeUpdated -> IndexUpdated) and any step
fails mid-way, rollback() undoes the staged events so no partial
state leaks into the EventBus or events.jsonl.

Usage::

    tx = EventTransaction(bus)
    tx.publish("ArtifactImported", payload={"id": "a1"}, source_skill="inbox")
    tx.publish("KnowledgeUpdated", payload={"id": "a1"}, source_skill="inbox")
    tx.commit()    # both events delivered + persisted
    # -- OR --
    tx.rollback()  # discarded; nothing published, nothing persisted

Conforms to the EventBus event schema:
    {type, time, source_skill, payload, entity_refs}
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from runtime.event_bus import EventBus


class EventTransaction:
    """Stages events; commit() delivers + persists, rollback() discards.

    Wraps an EventBus. ``publish()`` stages events in memory. ``commit()``
    delivers all staged events to subscribers AND persists them to
    ``events.jsonl`` via the bus. ``rollback()`` discards all staged
    events -- they are never delivered or persisted.

    The transaction is single-use per logical unit of work: after a
    commit or rollback the staged list is empty and new events can be
    staged for the next commit pass.
    """

    def __init__(self, bus: EventBus) -> None:
        """Create a new transaction bound to *bus*.

        Args:
            bus: The EventBus that will deliver/persist events on commit.
        """
        self._bus = bus
        self._staged: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def publish(
        self,
        event_type: str,
        payload: dict,
        source_skill: str = "",
        entity_refs: Optional[list] = None,
    ) -> None:
        """Stage an event for later delivery.

        The event is recorded with the same schema as ``EventBus.publish``
        (``type``, ``time``, ``source_skill``, ``payload``, ``entity_refs``),
        but it is NOT delivered to subscribers and NOT persisted to
        ``events.jsonl`` until ``commit()`` is called.

        Args:
            event_type: Domain event type (e.g. ``"ArtifactImported"``).
            payload: Per-type payload dict.
            source_skill: Skill that emitted the event.
            entity_refs: Vault entity references (default ``[]``).
        """
        event: Dict[str, Any] = {
            "type": event_type,
            "time": datetime.now(timezone.utc).isoformat(),
            "source_skill": source_skill,
            "payload": payload,
            "entity_refs": entity_refs if entity_refs is not None else [],
        }
        self._staged.append(event)

    def commit(self) -> List[dict]:
        """Deliver and persist all staged events.

        Each staged event is handed to ``EventBus.publish()``, which
        performs synchronous in-process delivery to matching subscribers
        AND appends the event to ``events.jsonl``.

        Returns:
            A shallow copy of the delivered event dicts.  The internal
            staged list is cleared after commit.
        """
        delivered: List[dict] = []
        for event in self._staged:
            # Delegate to bus.publish() which handles both subscriber
            # delivery and JSONL persistence in one call.
            self._bus.publish(
                event_type=event["type"],
                payload=event["payload"],
                source_skill=event["source_skill"],
                entity_refs=event["entity_refs"],
            )
            delivered.append(event)
        self._staged.clear()
        return delivered

    def rollback(self) -> None:
        """Discard all staged events.

        Staged events are silently dropped -- they are never delivered
        to subscribers and never persisted to ``events.jsonl``.  After
        rollback the transaction is clean and ready for new staging.
        """
        self._staged.clear()
