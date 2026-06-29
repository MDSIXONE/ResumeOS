"""Sprint 3 Inbox State Machine — ADR-0019.

Defines the finite states a file transitions through during Inbox processing:

    DETECTED → QUEUED → IMPORTING → IMPORTED → PUBLISHED → ARCHIVED
                                                              ↗
    (failure path) → IMPORT_FAILED
"""

from __future__ import annotations

from enum import Enum


class InboxState(Enum):
    """Lifecycle states for a file in the Inbox pipeline."""

    DETECTED = "detected"
    QUEUED = "queued"
    IMPORTING = "importing"
    IMPORTED = "imported"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    IMPORT_FAILED = "import_failed"
