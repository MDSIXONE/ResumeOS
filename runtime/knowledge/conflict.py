"""Conflict detection -- Builder never silently overwrites existing KB values.

Per user directive (Sprint 4, Principle: Builder not allowed to overwrite):
If a field exists in the KB with a non-null value and the LLM draft
proposes a DIFFERENT value, the Builder must NOT overwrite. It produces a
Conflict, keeps the existing value, and surfaces the conflict for user
resolution.

ResumeOS never silently changes knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Set


# System/infrastructure fields that are never conflict-checked.
# These are managed by the runtime, not by LLM drafts.
SYSTEM_FIELDS: Set[str] = {
    "history",
    "relations",
    "provenance",
    "conflicts",
    "$resumeos",
}


@dataclass
class Conflict:
    """A field where existing and new values differ.

    The Builder keeps the existing value and records the conflict.
    Resolution is "pending" until the user (or a review skill) decides.
    """

    field: str
    existing_value: Any
    new_value: Any
    resolution: str = "pending"
    """pending | keep_existing | accept_new | merged"""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Conflict":
        return cls(
            field=d["field"],
            existing_value=d.get("existing_value"),
            new_value=d.get("new_value"),
            resolution=d.get("resolution", "pending"),
        )


class ConflictDetector:
    """Detects conflicts between existing KB fields and a new draft.

    Rules:
        1. Only compare fields present in BOTH existing and new.
        2. Skip system fields (history, relations, provenance, $resumeos).
        3. If existing value is None/empty and new has a value: NOT a
           conflict (filling a gap is always allowed).
        4. If existing == new: NOT a conflict (no change).
        5. If existing != new and both non-empty: CONFLICT.
    """

    @staticmethod
    def detect(
        existing: Dict[str, Any],
        new: Dict[str, Any],
        skip_fields: Set[str] | None = None,
    ) -> List[Conflict]:
        skip = SYSTEM_FIELDS | (skip_fields or set())
        conflicts: List[Conflict] = []

        for key, new_val in new.items():
            if key in skip:
                continue
            if key not in existing:
                continue  # new field, no conflict

            existing_val = existing[key]

            # Rule 3: filling a gap is not a conflict
            if _is_empty(existing_val):
                continue

            # Rule 4: same value, no conflict
            if existing_val == new_val:
                continue

            # Rule 5: different non-empty values -> conflict
            conflicts.append(
                Conflict(
                    field=key,
                    existing_value=existing_val,
                    new_value=new_val,
                )
            )

        return conflicts


def _is_empty(val: Any) -> bool:
    """True if val is None, empty string, empty list, or empty dict."""
    if val is None:
        return True
    if isinstance(val, str) and val == "":
        return True
    if isinstance(val, (list, dict)) and len(val) == 0:
        return True
    return False
