"""Knowledge Provenance -- traceability for every generated KB entry.

Per user directive (Sprint 4 review): every piece of knowledge in the
Career KB must be traceable. Provenance records WHO generated it, with
WHAT LLM, from WHICH artifact, using WHICH prompt.

This is the metadata that makes Knowledge rebuildable and auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict


@dataclass
class KnowledgeProvenance:
    """Records how a Knowledge Object was generated.

    Fields:
        generated_by: Skill that generated this (e.g. "career_builder").
        llm: LLM provider name (e.g. "claude", "dummy", "openai").
        prompt: Prompt identifier/version (e.g. "career.project.v2").
        artifact: SHA-256 of the source artifact (links back to Importer).
        time: ISO 8601 timestamp of generation (auto-filled if empty).
    """

    generated_by: str = ""
    llm: str = ""
    prompt: str = ""
    artifact: str = ""
    """SHA-256 of the source Artifact's provenance.sha256."""

    time: str = ""

    def __post_init__(self) -> None:
        if not self.time:
            self.time = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "KnowledgeProvenance":
        return cls(
            generated_by=d.get("generated_by", ""),
            llm=d.get("llm", ""),
            prompt=d.get("prompt", ""),
            artifact=d.get("artifact", ""),
            time=d.get("time", ""),
        )
