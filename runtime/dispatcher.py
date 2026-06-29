"""Dispatcher module — in-process event delivery (ADR-0014).

This module provides the in-process delivery mechanism used by the Event
Bus.  It wraps the subscriber registry logic and is importable independently
of the persistence layer for tests and lightweight usages.

The runtime dispatcher never imports any LLM SDK.  It is the local-only,
synchronous delivery half of the event bus described in ADR-0014 Rules 4–5.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

# Handler signature: receives an event dict, returns None.
Handler = Callable[[Dict[str, Any]], None]


class SubscriberRegistry:
    """Topic-based subscriber registry (ADR-0014).

    A lightweight in-process fan-out mechanism.  Handlers subscribe
    to a named topic and are invoked synchronously for each
    matching dispatch.  The wildcard topic ``'*'`` matches every event.

    This class is intentionally delivery-only; it does not persist
    events.  For the persisted event bus, use :class:`runtime.event_bus.EventBus`
    which composes a :class:`SubscriberRegistry` with JSONL append.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def subscribe(self, topic: str, handler: Handler) -> None:
        """Register *handler* for *topic*.

        Args:
            topic: Event type string (e.g. ``"ProjectImported"``).
                Use ``'*'`` to match every dispatched event
                (ADR-0014 Rule 4).
            handler: Callable ``dict -> None``.
        """
        self._handlers[topic].append(handler)

    def unsubscribe(self, topic: str, handler: Handler) -> None:
        """Remove *handler* from *topic* if registered.

        Safe to call with an unregistered handler — it is a no-op.
        """
        if topic in self._handlers:
            try:
                self._handlers[topic].remove(handler)
            except ValueError:
                pass

    def dispatch(self, topic: str, event: Dict[str, Any]) -> None:
        """Deliver *event* to matching handlers synchronously.

        Handlers subscribed to the specific ``topic`` **and** to the
        wildcard ``'*'`` are invoked.  A handler that raises is caught,
        logged, and does not prevent subsequent handlers from running.

        Args:
            topic: The event type that was published.
            event: The event dict conforming to the event schema.
        """
        targets: List[Handler] = []
        targets.extend(self._handlers.get(topic, []))
        if topic != "*":
            targets.extend(self._handlers.get("*", []))
        for handler in targets:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Subscriber registry handler %r raised for topic '%s'",
                    handler,
                    topic,
                )

    def has_subscribers(self, topic: str) -> bool:
        """Return True if any handler is registered for *topic* or ``'*'``.

        Useful for pre-flight checks (e.g. the workflow engine may want
        to log a warning if no one is listening to an on_success_event).
        """
        return bool(self._handlers.get(topic) or self._handlers.get("*"))


# Convenience: re-export the EventBus so callers can import either from
# ``runtime.event_bus`` or ``runtime.dispatcher``.
from runtime.event_bus import EventBus  # noqa: E402,F401

__all__ = ["SubscriberRegistry", "EventBus"]
