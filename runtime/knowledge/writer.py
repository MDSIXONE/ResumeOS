"""Knowledge Writer -- renders Knowledge Objects to a backend.

Per user Principle 2 (Sprint 4): Builder never directly writes files.
It uses a KnowledgeWriter. The default is MarkdownWriter; future
backends include SQLite, Notion, GitHub, Obsidian Canvas.

This is the View layer -- the same KnowledgeObject can be rendered to
multiple formats without re-running the LLM.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from runtime.knowledge.object import KnowledgeObject


# Entity type -> plural folder name (matches knowledge_index.py mapping).
_TYPE_TO_FOLDER: Dict[str, str] = {
    "project": "projects",
    "award": "awards",
    "research": "research",
    "skill": "skills",
    "job": "jobs",
    "education": "education",
    "competition": "competitions",
    "internship": "internships",
    "opensource": "opensource",
}

# Frontmatter regex (same pattern as knowledge_index.py).
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class KnowledgeWriter(ABC):
    """Abstract writer -- renders KnowledgeObject to a backend."""

    @abstractmethod
    def write(self, obj: KnowledgeObject, vault_root: Path) -> Path:
        """Write the knowledge object, return the path written."""
        ...

    @abstractmethod
    def read(
        self, entity_type: str, entity_id: str, vault_root: Path
    ) -> Optional[Dict[str, Any]]:
        """Read an existing entity's frontmatter, or None if not found."""
        ...


class MarkdownWriter(KnowledgeWriter):
    """Writes Knowledge Objects as Markdown files with YAML frontmatter.

    Path: vault_root/career/<plural>/<entity_id>.md

    Frontmatter includes:
        - id, entity_type
        - All entity fields from KnowledgeObject.fields
        - provenance: {generated_by, llm, prompt, artifact, time}
        - conflicts: [...] (if any, per Sprint 4 conflict principle)

    Body includes rendered sections (title, description, stack, metrics, ...).
    The Writer is pure rendering -- no business logic, no merge, no conflict
    detection. Those are the Merger's job.
    """

    def write(self, obj: KnowledgeObject, vault_root: Path) -> Path:
        folder = _TYPE_TO_FOLDER.get(obj.entity_type, obj.entity_type + "s")
        dest_dir = vault_root / "career" / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{obj.entity_id}.md"

        # Build frontmatter
        fm: Dict[str, Any] = {}
        fm["id"] = obj.entity_id
        fm["entity_type"] = obj.entity_type
        fm.update(obj.fields)
        fm["provenance"] = obj.provenance.to_dict()

        if obj.conflicts:
            fm["conflicts"] = [c.to_dict() for c in obj.conflicts]

        # Build body
        body = self._render_body(obj)

        # Write
        frontmatter_yaml = yaml.dump(
            fm, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
        content = f"---\n{frontmatter_yaml}---\n\n{body}"
        dest.write_text(content, encoding="utf-8")
        return dest

    def read(
        self, entity_type: str, entity_id: str, vault_root: Path
    ) -> Optional[Dict[str, Any]]:
        folder = _TYPE_TO_FOLDER.get(entity_type, entity_type + "s")
        path = vault_root / "career" / folder / f"{entity_id}.md"
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
        m = _FM_RE.match(text)
        if not m:
            return None
        try:
            data = yaml.safe_load(m.group(1))
        except yaml.YAMLError:
            return None
        return data if isinstance(data, dict) else None

    def _render_body(self, obj: KnowledgeObject) -> str:
        """Render Markdown body from KnowledgeObject fields."""
        fields = obj.fields
        lines: List[str] = []

        title = fields.get("title", obj.entity_id)
        lines.append(f"# {title}\n")

        if fields.get("description"):
            lines.append(f"{fields['description']}\n")

        # Tech stack
        stack = fields.get("stack", {})
        if isinstance(stack, dict) and any(
            stack.get(k) for k in ["hardware", "software", "protocol", "algorithm", "dataset"]
        ):
            lines.append("## Tech Stack\n")
            for layer in ["hardware", "software", "protocol", "algorithm", "dataset"]:
                vals = stack.get(layer, [])
                if vals:
                    lines.append(f"- **{layer.title()}**: {', '.join(vals)}")
            lines.append("")

        # Metrics
        metrics = fields.get("metrics", [])
        if metrics:
            lines.append("## Metrics\n")
            for m in metrics:
                if isinstance(m, dict):
                    line = f"- {m.get('metric', '')}: {m.get('value', '')}"
                    if m.get("context"):
                        line += f" ({m['context']})"
                    lines.append(line)
            lines.append("")

        # Contribution
        contribution = fields.get("contribution")
        if contribution:
            lines.append("## Contribution\n")
            lines.append(f"{contribution}\n")

        # Conflicts (surface for user review)
        if obj.conflicts:
            lines.append("## Conflicts (needs review)\n")
            for c in obj.conflicts:
                lines.append(
                    f"- **{c.field}**: existing=`{c.existing_value}` "
                    f"vs new=`{c.new_value}`"
                )
            lines.append("")

        # Provenance footer
        prov = obj.provenance
        if prov.generated_by:
            lines.append("---\n")
            lines.append(
                f"*Generated by {prov.generated_by} via {prov.llm} "
                f"(prompt: {prov.prompt}, artifact: {prov.artifact[:12]}...)*\n"
            )

        return "\n".join(lines)
