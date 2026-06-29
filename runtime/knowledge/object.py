"""Knowledge Object -- the intermediate representation between Artifact and output.

Per user Principle 1 (Sprint 4): Markdown is always just a View. The
Builder produces a Knowledge Object, not Markdown directly. The Writer
(MarkdownWriter, future SQLiteWriter, etc.) renders the Object.

    Artifact -> KnowledgeObject -> Markdown / HTML / JSON / ...

This separation means the same Knowledge can be rendered to multiple
formats without re-running the LLM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from runtime.knowledge.provenance import KnowledgeProvenance
from runtime.knowledge.conflict import Conflict


@dataclass
class KnowledgeObject:
    """The intermediate representation of a career entity.

    Produced by the Builder pipeline (Planner -> Retriever -> LLM ->
    Validator -> Merger).  Consumed by a KnowledgeWriter (Markdown,
    SQLite, etc.).

    Fields:
        entity_type: "project", "skill", "award", etc.
        entity_id: kebab-case slug, e.g. "yolo-detection".
        fields: the entity data (title, status, timeline, role, stack, ...).
            These are the frontmatter fields that the Writer renders.
        provenance: how this was generated (LLM, prompt, artifact hash, time).
        conflicts: fields where existing and new values differ (kept existing).
        previous_values: old values for changed fields (for history/user review).
        version: entity version number (ADR-0015, starts at 1).
        is_new: True if this is a new entity (no prior version in KB).
    """

    entity_type: str = ""
    entity_id: str = ""
    fields: Dict[str, Any] = field(default_factory=dict)
    provenance: KnowledgeProvenance = field(default_factory=KnowledgeProvenance)
    conflicts: List[Conflict] = field(default_factory=list)
    previous_values: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    is_new: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "fields": self.fields,
            "provenance": self.provenance.to_dict(),
            "conflicts": [c.to_dict() for c in self.conflicts],
            "previous_values": self.previous_values,
            "version": self.version,
            "is_new": self.is_new,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "KnowledgeObject":
        return cls(
            entity_type=d.get("entity_type", ""),
            entity_id=d.get("entity_id", ""),
            fields=d.get("fields", {}),
            provenance=KnowledgeProvenance.from_dict(d.get("provenance", {})),
            conflicts=[Conflict.from_dict(c) for c in d.get("conflicts", [])],
            previous_values=d.get("previous_values", {}),
            version=d.get("version", 1),
            is_new=d.get("is_new", True),
        )

    @property
    def has_conflicts(self) -> bool:
        """True if any field conflicts were detected."""
        return len(self.conflicts) > 0
