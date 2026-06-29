"""MarkdownRenderer -- renders ResumeIR to Markdown (Sprint 5).

Core principle: Resume is just a projection of Knowledge.
ResumeIR is the intermediate; Renderer is the final step.

    ResumeIR -> MarkdownRenderer -> Markdown text

No LLM. Pure template rendering. stdlib only.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from runtime.resume.ir import ResumeIR
from runtime.resume.renderer.base import Renderer


class MarkdownRenderer(Renderer):
    """Render a ResumeIR as a Markdown resume."""

    def __init__(self) -> None:
        pass

    # -- Renderer ABC -------------------------------------------------------

    def render(self, ir: ResumeIR) -> str:  # noqa: D401
        """Produce a Markdown resume string from *ir*."""
        lines: List[str] = []

        # Title
        name = "ResumeOS User"
        subtitle = ir.target_company or "Resume"
        lines.append(f"# {name}")
        lines.append(f"### {subtitle}")
        lines.append("")

        # Sections -- iterate in section_order if available
        ordered_sections = self._ordered_sections(ir)

        for section in ordered_sections:
            lines.append(f"## {section.title}")
            lines.append("")
            for item in section.items:
                lines.extend(
                    self._render_item(item, section.name)
                )
                lines.append("")  # blank line between items

        return "\n".join(lines).rstrip("\n") + "\n"

    def file_extension(self) -> str:  # noqa: D102
        return "md"

    def format_name(self) -> str:  # noqa: D102
        return "Markdown"

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
        # Also include sections not explicitly listed in section_order
        listed = {s.name for s in ordered}
        for section in ir.sections:
            if section.name not in listed:
                ordered.append(section)
        return ordered

    def _render_item(self, item: Any, section_name: str) -> List[str]:
        """Render a single ResumeItem to a list of Markdown lines."""
        content: Dict[str, Any] = item.content or {}
        title: str = item.title or ""

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
            # Fallback: just the title
            return [f"### {title}", ""]

    # -- Section-specific renderers -----------------------------------------

    @staticmethod
    def _render_project(title: str, content: Dict[str, Any]) -> List[str]:
        lines: List[str] = [f"### {title}"]

        role = content.get("role", "")
        timeline = content.get("timeline") or {}
        start = timeline.get("start", "") if isinstance(timeline, dict) else ""
        end = timeline.get("end", "") if isinstance(timeline, dict) else ""
        stack = content.get("stack") or {}
        software: list = []
        if isinstance(stack, dict):
            software = stack.get("software", []) or []
        elif isinstance(stack, list):
            software = stack
        metrics = content.get("metrics", "")
        contribution = content.get("contribution", "")

        lines.append(f"**Role:** {role} | **Timeline:** {start} - {end}")
        lines.append(f"**Stack:** {', '.join(str(s) for s in software)}")

        # Format metrics
        if isinstance(metrics, list):
            metrics_str = ", ".join(
                f"{m.get('label', '')}: {m.get('value', '')}" for m in metrics
            ) if metrics else ""
        elif isinstance(metrics, str):
            metrics_str = metrics
        else:
            metrics_str = str(metrics) if metrics else ""
        lines.append(f"**Metrics:** {metrics_str}")

        if contribution:
            lines.append(str(contribution))

        return lines

    @staticmethod
    def _render_skill(title: str, content: Dict[str, Any]) -> List[str]:
        level = content.get("level", content.get("proficiency", ""))
        return [f"- **{title}** (proficiency: {level})"]

    @staticmethod
    def _render_education(title: str, content: Dict[str, Any]) -> List[str]:
        institution = content.get("institution", "")
        degree = content.get("degree", "")
        timeline = content.get("timeline") or {}
        start = timeline.get("start", "") if isinstance(timeline, dict) else ""
        end = timeline.get("end", "") if isinstance(timeline, dict) else ""
        return [
            f"### {title}",
            f"{institution} | {degree}",
            f"{start} - {end}",
        ]

    @staticmethod
    def _render_award(title: str, content: Dict[str, Any]) -> List[str]:
        rank = content.get("rank", "")
        date = content.get("date", "")
        return [f"- **{title}** ({rank}, {date})"]

    @staticmethod
    def _render_experience(title: str, content: Dict[str, Any]) -> List[str]:
        role = content.get("role", "")
        timeline = content.get("timeline") or {}
        start = timeline.get("start", "") if isinstance(timeline, dict) else ""
        end = timeline.get("end", "") if isinstance(timeline, dict) else ""
        return [
            f"### {title}",
            f"**Role:** {role}",
            f"{start} - {end}",
        ]
