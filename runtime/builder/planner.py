"""Planner — derives a plan from an Artifact for the Builder pipeline.

The Planner maps artifact types to entity types, generates a stable slug
from the artifact title, and determines which schema to validate against.
"""
from __future__ import annotations

import re
from typing import Any, Dict

from runtime.artifacts.base import Artifact


# Artifact type -> Knowledge entity type mapping.
_ENTITY_TYPE_MAP: Dict[str, str] = {
    "project": "project",
    "certificate": "award",
    "competition": "competition",
    "research_paper": "research",
}


def _slugify(text: str) -> str:
    """Convert text to a kebab-case slug.

    Rules: lowercase, spaces -> hyphens, strip non-[a-z0-9-], collapse
    multiple hyphens, strip leading/trailing hyphens.
    """
    slug = text.lower()
    slug = slug.replace(" ", "-")
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug


class Planner:
    """Derives a plan from an Artifact.

    The plan determines:
        - entity_type: what kind of knowledge entity to produce
        - entity_id: stable slug identifier
        - artifact_type: the original artifact type (for provenance)
        - schema_name: which JSON schema to validate against
    """

    def plan(self, artifact: Artifact) -> Dict[str, Any]:
        """Derive a plan from an Artifact.

        Returns:
            dict with keys: entity_type, entity_id, artifact_type, schema_name.
        """
        atype = artifact.artifact_type
        entity_type = _ENTITY_TYPE_MAP.get(atype, atype)

        # Derive entity_id from the artifact title.
        title = getattr(artifact, "title", "")
        if not title:
            # Fallback: try competition_name, issuer, etc.
            title = (
                getattr(artifact, "competition_name", "")
                or getattr(artifact, "issuer", "")
                or f"untitled-{atype}"
            )

        entity_id = _slugify(title) or f"untitled-{atype}"

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "artifact_type": atype,
            "schema_name": f"{entity_type}.schema.json",
        }
