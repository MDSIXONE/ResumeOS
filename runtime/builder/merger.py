"""Merger -- merges a validated Draft with an existing entity.

Per the "no silent overwrite" principle: if the existing entity has
non-empty values that conflict with the draft, the existing values are
preserved and Conflicts are recorded. Non-conflicting fields from the
draft are merged in (filling gaps, adding new fields).
"""
from __future__ import annotations

from typing import Any, Dict, List

from runtime.knowledge.object import KnowledgeObject
from runtime.knowledge.conflict import Conflict, ConflictDetector
from runtime.knowledge.draft import Draft
from runtime.knowledge.provenance import KnowledgeProvenance


class Merger:
    """Merges a validated Draft with an existing entity (if any).

    Produces a KnowledgeObject with conflict detection:
        - New entity: version=1, is_new=True, no conflicts.
        - Existing entity: ConflictDetector finds fields that differ.
          Existing values are preserved, conflicts recorded.
    """

    def merge(
        self, draft: Draft, existing: Dict[str, Any] | None, plan: dict
    ) -> KnowledgeObject:
        """Merge validated draft with existing entity.

        Args:
            draft: The validated Draft with fields to merge.
            existing: Existing entity frontmatter dict, or None if new.
            plan: The plan dict from the Planner stage.

        Returns:
            A new KnowledgeObject ready for writing.
        """
        if existing is None:
            return self._merge_new(draft, plan)
        return self._merge_existing(draft, existing, plan)

    def _merge_new(self, draft: Draft, plan: dict) -> KnowledgeObject:
        """Create a KnowledgeObject for a brand-new entity."""
        return KnowledgeObject(
            entity_type=draft.entity_type,
            entity_id=plan["entity_id"],
            fields=dict(draft.fields),
            provenance=draft.provenance,
            conflicts=[],
            previous_values={},
            version=1,
            is_new=True,
        )

    def _merge_existing(
        self,
        draft: Draft,
        existing: Dict[str, Any],
        plan: dict,
    ) -> KnowledgeObject:
        """Merge draft into an existing entity, detecting conflicts."""
        # Detect conflicts between existing fields and draft fields.
        conflicts = ConflictDetector.detect(existing, draft.fields)
        conflicted_field_names = {c.field for c in conflicts}

        # Build merged fields: start with existing, overlay non-conflicting.
        merged_fields = dict(existing)
        for key, value in draft.fields.items():
            if key in conflicted_field_names:
                # Conflict: keep existing value (already in merged_fields).
                continue
            merged_fields[key] = value

        # Record previous_values for conflicts.
        previous_values: Dict[str, Any] = {}
        for c in conflicts:
            previous_values[c.field] = c.existing_value

        # Compute version from existing history.
        history = existing.get("history", [])
        if history:
            version = len(history) + 1
        else:
            version = 2  # existing was version 1, this is version 2

        return KnowledgeObject(
            entity_type=draft.entity_type,
            entity_id=plan["entity_id"],
            fields=merged_fields,
            provenance=draft.provenance,
            conflicts=conflicts,
            previous_values=previous_values,
            version=version,
            is_new=False,
        )
