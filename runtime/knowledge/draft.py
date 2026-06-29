"""Draft -- LLM output before validation.

Per user Principle 3 (Sprint 4, ★★★★★): LLM always outputs Draft,
never direct Knowledge. The Draft is validated against the entity
schema before it can enter the KB. If validation fails, the LLM is
re-prompted with the error feedback. The KB is never polluted with
invalid data.

    LLM -> Draft -> Validator -> Knowledge -> Writer
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from runtime.knowledge.provenance import KnowledgeProvenance


@dataclass
class Draft:
    """Unvalidated LLM output, awaiting schema validation.

    Fields:
        entity_type: "project", "skill", etc.
        entity_id: proposed entity slug.
        fields: parsed from LLM output (YAML/JSON).
        raw_output: the raw LLM response string (for debugging/replay).
        provenance: partial provenance (has llm, prompt, artifact, time).
        validation_errors: filled by Validator if schema check fails.
        attempt: which LLM call attempt (1 = first, 2+ = retries).
    """

    entity_type: str = ""
    entity_id: str = ""
    fields: Dict[str, Any] = field(default_factory=dict)
    raw_output: str = ""
    provenance: KnowledgeProvenance = field(default_factory=KnowledgeProvenance)
    validation_errors: List[str] = field(default_factory=list)
    attempt: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "fields": self.fields,
            "raw_output": self.raw_output,
            "provenance": self.provenance.to_dict(),
            "validation_errors": self.validation_errors,
            "attempt": self.attempt,
        }

    @property
    def is_valid(self) -> bool:
        """True if no validation errors."""
        return len(self.validation_errors) == 0
