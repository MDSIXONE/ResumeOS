"""Event Bus -- domain event infrastructure (ADR-0014).

Provides in-process publish/subscribe event delivery with persistence
to ``vault/.library/events.jsonl`` (append-only JSONL audit log).

Per ADR-0014:
    - Events are facts, not commands.
    - Six built-in event types (extensible by community Skills).
    - Persistence: append to events.jsonl (JSONL, one event per line).
    - In-process synchronous delivery in v1.
    - Wildcard ``*`` subscribes to all events (Rule 4).
    - Event schema: ``{type, time, source_skill, payload, entity_refs}``.

Conforms to ``schemas/runtime/event.schema.json``.
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Handler signature: receives an event dict, returns None.
Handler = Callable[[Dict[str, Any]], None]


class EventBus:
    """In-process event bus with JSONL persistence (ADR-0014).

    Events are published by type string.  Handlers register for specific
    event types.  Wildcard ``'*'`` subscribes to **all** events.

    Every ``publish()`` call:
        1. Delivers the event synchronously to matching handlers.
        2. Appends the event to ``events.jsonl`` (durable audit log).

    Args:
        events_log: Path to the ``events.jsonl`` file.  Parent directories
            are created automatically if they do not exist.
    """

    def __init__(self, events_log: Path) -> None:
        self._events_log = Path(events_log)
        self._subscribers: Dict[str, List[Handler]] = defaultdict(list)
        # Ensure parent directory exists for persistence.
        self._events_log.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def subscribe(self, event_type: str, handler: Handler) -> None:
        """Register *handler* for *event_type*.

        Args:
            event_type: Event type string (e.g. ``"ProjectImported"``).
                Use ``"*"`` to receive **all** events (ADR-0014 Rule 4).
            handler: Callable ``dict -> None`` invoked synchronously on
                every matching ``publish()``.
        """
        self._subscribers[event_type].append(handler)

    def publish(
        self,
        event_type: str,
        payload: dict,
        source_skill: str = "",
        entity_refs: Optional[list] = None,
    ) -> None:
        """Publish an event.

        Delivers to all matching subscribers (in-process, synchronous)
        and appends to ``events.jsonl`` (persistent audit log).

        Args:
            event_type: The domain event type (e.g. ``"KnowledgeUpdated"``).
            payload: Per-type payload object per ``event-catalog.md``.
            source_skill: Skill id that emitted the event (or ``"runtime"``
                for runtime-generated events).
            entity_refs: Vault entity references (default ``[]``).
        """
        event: Dict[str, Any] = {
            "type": event_type,
            "time": datetime.now(timezone.utc).isoformat(),
            "source_skill": source_skill,
            "payload": payload,
            "entity_refs": entity_refs if entity_refs is not None else [],
        }

        # 1. In-process delivery (ADR-0014 Rule 5).
        self._deliver(event)

        # 2. Persist to JSONL audit log (ADR-0014 Rule 4).
        self._persist(event)

    def events(self) -> List[dict]:
        """Read back all persisted events from ``events.jsonl``.

        Returns:
            Ordered list of event dicts, oldest first.  Returns an empty
            list if the log does not exist or is empty.
        """
        if not self._events_log.exists():
            return []
        text = self._events_log.read_text(encoding="utf-8").strip()
        if not text:
            return []
        result: List[dict] = []
        for line in text.split("\n"):
            line = line.strip()
            if line:
                result.append(json.loads(line))
        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _deliver(self, event: Dict[str, Any]) -> None:
        """Deliver *event* to matching handlers.

        Collects handlers subscribed to the event's specific type **and**
        handlers subscribed to ``'*'`` (wildcard).  A handler that raises
        is logged but does not prevent other handlers from running.
        """
        event_type = event["type"]
        handlers: List[Handler] = []
        handlers.extend(self._subscribers.get(event_type, []))
        # Wildcard subscribers receive every event (ADR-0014 Rule 4).
        # Avoid double-adding when the event type is itself "*" (the
        # wildcard bucket was already included above).
        if event_type != "*":
            handlers.extend(self._subscribers.get("*", []))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Event handler %r raised for event type '%s'",
                    handler,
                    event_type,
                )

    def _persist(self, event: Dict[str, Any]) -> None:
        """Append *event* to ``events.jsonl`` as a single JSON line."""
        line = json.dumps(event, ensure_ascii=False, default=str)
        with open(self._events_log, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
