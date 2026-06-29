"""HTMLRenderer -- renders ResumeIR to a full HTML5 document (Sprint 5).

Core principle: Resume is just a projection of Knowledge.
ResumeIR is the intermediate; Renderer is the final step.

    ResumeIR -> HTMLRenderer -> HTML5 document

No LLM. Pure template rendering. stdlib only (html.escape for safety).
"""
from __future__ import annotations

import html
from typing import Any, Dict, List

from runtime.resume.ir import ResumeIR
from runtime.resume.renderer.base import Renderer


_CSS = """\
body {
    font-family: "Segoe UI", Helvetica, Arial, sans-serif;
    max-width: 800px;
    margin: 2em auto;
    padding: 0 1em;
    color: #333;
    line-height: 1.6;
}
h1 { border-bottom: 2px solid #2a6496; padding-bottom: 0.3em; }
h2 { color: #2a6496; margin-top: 1.5em; border-bottom: 1px solid #ddd; padding-bottom: 0.2em; }
h3 { margin-bottom: 0.2em; }
.section { margin-bottom: 1em; }
.item { margin-bottom: 1em; }
.meta { color: #666; font-size: 0.9em; }
ul { margin-top: 0.3em; }
"""


class HTMLRenderer(Renderer):
    """Render a ResumeIR as a self-contained HTML5 document."""

    def __init__(self) -> None:
        pass

    # -- Renderer ABC -------------------------------------------------------

    def render(self, ir: ResumeIR) -> str:  # noqa: D401
        """Produce an HTML resume string from *ir*."""
        parts: List[str] = []

        # Document head
        parts.append("<!DOCTYPE html>")
        parts.append('<html lang="en">')
        parts.append("<head>")
        parts.append('<meta charset="utf-8">')
        parts.append("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
        parts.append("<title>Resume</title>")
        parts.append(f"<style>{_CSS}</style>")
        parts.append("</head>")
        parts.append("<body>")

        # Name / title
        name = html.escape("ResumeOS User")
        parts.append(f"<h1>{name}</h1>")

        if ir.target_company:
            parts.append(f'<p class="meta">{html.escape(ir.target_company)}</p>')

        # Sections
        ordered = self._ordered_sections(ir)
        for section in ordered:
            parts.append(f"<h2>{html.escape(section.title)}</h2>")
            parts.append('<div class="section">')
            for item in section.items:
                parts.append(self._render_item(item, section.name))
            parts.append("</div>")

        parts.append("</body>")
        parts.append("</html>")
        return "\n".join(parts)

    def file_extension(self) -> str:  # noqa: D102
        return "html"

    def format_name(self) -> str:  # noqa: D102
        return "HTML"

    # -- Helpers ------------------------------------------------------------

    @staticmethod
    def _ordered_sections(ir: ResumeIR) -> list:
        """Return sections ordered by ``ir.section_order``."""
        if not ir.section_order:
            return list(ir.sections)
        lookup = {s.name: s for s in ir.sections}
        ordered: list = []
        for name in ir.section_order:
            if name in lookup:
                ordered.append(lookup[name])
        listed = {s.name for s in ordered}
        for section in ir.sections:
            if section.name not in listed:
                ordered.append(section)
        return ordered

    def _render_item(self, item: Any, section_name: str) -> str:
        """Render a single ResumeItem to an HTML block."""
        content: Dict[str, Any] = item.content or {}
        title: str = html.escape(item.title or "")

        if section_name == "projects" or item.entity_type == "project":
            return self._render_project(title, content)
        elif section_name == "skills" or item.entity_type == "skill":
            return self._render_skill(title, content)
        elif section_name == "education" or item.entity_type == "education":
            return self._render_education(title, content)
        elif section_name == "awards" or item.entity_type == "award":
            return self._render_award(title, content)
        elif section_name == "experience" or item.entity_type in ("job", "experience"):
            return self._render_experience(title, content)
        else:
            return f'<div class="item"><h3>{title}</h3></div>'

    # -- Section-specific renderers -----------------------------------------

    @staticmethod
    def _render_project(title: str, content: Dict[str, Any]) -> str:
        role = html.escape(str(content.get("role", "")))
        timeline = content.get("timeline") or {}
        start = html.escape(str(timeline.get("start", "")) if isinstance(timeline, dict) else "")
        end = html.escape(str(timeline.get("end", "")) if isinstance(timeline, dict) else "")

        stack = content.get("stack") or {}
        if isinstance(stack, dict):
            software = stack.get("software", []) or []
        elif isinstance(stack, list):
            software = stack
        else:
            software = []
        stack_str = ", ".join(html.escape(str(s)) for s in software)

        metrics = content.get("metrics", "")
        if isinstance(metrics, list):
            metrics_parts = []
            for m in metrics:
                lbl = html.escape(str(m.get("label", "")))
                val = html.escape(str(m.get("value", "")))
                metrics_parts.append(f"{lbl}: {val}")
            metrics_str = ", ".join(metrics_parts) if metrics_parts else ""
        else:
            metrics_str = html.escape(str(metrics)) if metrics else ""

        contribution = html.escape(str(content.get("contribution", ""))) if content.get("contribution") else ""

        lines = [
            '<div class="item">',
            f"<h3>{title}</h3>",
            f'<p class="meta"><strong>Role:</strong> {role} | <strong>Timeline:</strong> {start} - {end}</p>',
        ]
        if stack_str:
            lines.append(f'<p><strong>Stack:</strong> {stack_str}</p>')
        if metrics_str:
            lines.append(f'<p><strong>Metrics:</strong> {metrics_str}</p>')
        if contribution:
            lines.append(f"<p>{contribution}</p>")
        lines.append("</div>")
        return "\n".join(lines)

    @staticmethod
    def _render_skill(title: str, content: Dict[str, Any]) -> str:
        level = html.escape(str(content.get("level", content.get("proficiency", ""))))
        return f'<div class="item"><p><strong>{title}</strong> (proficiency: {level})</p></div>'

    @staticmethod
    def _render_education(title: str, content: Dict[str, Any]) -> str:
        institution = html.escape(str(content.get("institution", "")))
        degree = html.escape(str(content.get("degree", "")))
        timeline = content.get("timeline") or {}
        start = html.escape(str(timeline.get("start", "")) if isinstance(timeline, dict) else "")
        end = html.escape(str(timeline.get("end", "")) if isinstance(timeline, dict) else "")
        lines = [
            '<div class="item">',
            f"<h3>{title}</h3>",
            f'<p class="meta">{institution} | {degree}</p>',
            f'<p class="meta">{start} - {end}</p>',
            "</div>",
        ]
        return "\n".join(lines)

    @staticmethod
    def _render_award(title: str, content: Dict[str, Any]) -> str:
        rank = html.escape(str(content.get("rank", "")))
        date = html.escape(str(content.get("date", "")))
        return f'<div class="item"><p><strong>{title}</strong> ({rank}, {date})</p></div>'

    @staticmethod
    def _render_experience(title: str, content: Dict[str, Any]) -> str:
        role = html.escape(str(content.get("role", "")))
        timeline = content.get("timeline") or {}
        start = html.escape(str(timeline.get("start", "")) if isinstance(timeline, dict) else "")
        end = html.escape(str(timeline.get("end", "")) if isinstance(timeline, dict) else "")
        lines = [
            '<div class="item">',
            f"<h3>{title}</h3>",
            f'<p class="meta"><strong>Role:</strong> {role}</p>',
            f'<p class="meta">{start} - {end}</p>',
            "</div>",
        ]
        return "\n".join(lines)
