"""DummyLLMProvider -- deterministic provider for tests and golden tests.

Returns fixed responses based on the artifact data in the prompt. NO
real API calls. This makes the Builder pipeline fully testable without
a real LLM.

For Golden Tests: same Artifact -> same Draft, every time.

Prompt format (expected by generate()):
    The prompt MUST contain a section delimited by "ARTIFACT_JSON:" that
    contains the artifact serialized as JSON. The dummy parses this block
    and produces a YAML draft mapped from artifact fields to entity fields.

    Example prompt excerpt:
        ARTIFACT_JSON:
        {"artifact_type": "project", "title": "YOLO", "tech_stack": ["Python"], ...}
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List

import yaml

from runtime.llm_provider import LLMProvider


class DummyLLMProvider(LLMProvider):
    """Deterministic LLM provider for testing.

    generate(): parses artifact JSON from the prompt (delimited by
        "ARTIFACT_JSON:") and returns a YAML draft with fields mapped
        from artifact -> entity schema. Deterministic: same input ->
        same output, every time.
    embed(): returns a deterministic 32-dim hash-based vector.
    summarize(): returns the first N characters.
    """

    @property
    def name(self) -> str:
        return "dummy"

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        artifact = self._extract_artifact_json(prompt)
        if not artifact:
            return "entity_type: unknown\ntitle: Untitled\n"

        atype = artifact.get("artifact_type", "")
        return self._build_draft_yaml(artifact, atype)

    def embed(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255.0 for b in h[:32]]

    def summarize(self, text: str, *, max_length: int = 500) -> str:
        return text[:max_length]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_artifact_json(prompt: str) -> Dict[str, Any]:
        """Extract the artifact JSON block from the prompt.

        Looks for a line starting with "ARTIFACT_JSON:" and parses
        everything after it as JSON (until the next blank line or
        section marker).
        """
        # Try delimited block: ARTIFACT_JSON:\n{...}\n
        m = re.search(
            r"ARTIFACT_JSON:\s*\n(.*?)(?:\n\n|\n[A-Z_]+:|\Z)",
            prompt,
            re.DOTALL,
        )
        if m:
            raw = m.group(1).strip()
            try:
                data = json.loads(raw)
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass

        # Fallback: look for any JSON object containing "artifact_type"
        m = re.search(r'\{[^{}]*"artifact_type"[^{}]*\}', prompt, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(0))
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass

        return {}

    @staticmethod
    def _build_draft_yaml(artifact: Dict[str, Any], atype: str) -> str:
        """Build a YAML draft from artifact fields, mapped to entity schema."""
        prov = artifact.get("provenance", {})
        sha = prov.get("sha256", "")
        source = prov.get("source_path", "")

        # Map artifact type -> entity type
        entity_map = {
            "project": "project",
            "certificate": "award",
            "competition": "competition",
            "research_paper": "research",
        }
        etype = entity_map.get(atype, atype)

        if etype == "project":
            title = artifact.get("title", "Untitled Project")
            tech = artifact.get("tech_stack", [])
            if not isinstance(tech, list):
                tech = [tech] if tech else []
            desc = artifact.get("description", "")
            repo = artifact.get("repo_url", "")

            # Determine source kind from path/repo
            source_kind = "readme"
            if repo and ("github" in repo or "git" in repo):
                source_kind = "github"
            elif ".git" in source:
                source_kind = "github"

            draft: Dict[str, Any] = {
                "entity_type": "project",
                "title": title,
                "status": "completed",
                "role": "Developer",
                "timeline": {
                    "start": "2024-01-01",
                    "end": "2024-06-01",
                    "ongoing": False,
                },
                "stack": {
                    "hardware": [],
                    "software": tech,
                    "protocol": [],
                    "algorithm": [],
                    "dataset": [],
                },
                "tags": [t.lower().replace(" ", "-") for t in tech],
                "confidence": "inferred",
                "sources": [{"kind": source_kind, "ref": source or repo or "unknown"}],
            }
            if desc:
                draft["description"] = desc
            return yaml.dump(draft, default_flow_style=False, sort_keys=False)

        # Minimal draft for non-project types
        title = artifact.get("title", "Untitled")
        return yaml.dump(
            {
                "entity_type": etype,
                "title": title,
                "sources": [{"kind": "readme", "ref": source or "unknown"}],
            },
            default_flow_style=False,
            sort_keys=False,
        )
