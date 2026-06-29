"""HTMLRenderer -- renders ResumeIR to a full HTML5 document (Sprint 5).

Phase 2: Template-aware rendering with support for:
    - Dynamic fonts and colors from TemplateConfig
    - Photo rendering (file path or base64 data URI)
    - Personal info blocks (gender, birthDate, ethnicity, etc.)
    - Professional summary section
    - Self-evaluation section (自我评价)

Core principle: Resume is just a projection of Knowledge.
ResumeIR is the intermediate; Renderer is the final step.

    ResumeIR -> HTMLRenderer -> HTML5 document

No LLM. Pure template rendering. stdlib only (html.escape for safety).
"""
from __future__ import annotations

import html
from typing import Any, Dict, List, Optional

from runtime.resume.ir import ResumeIR
from runtime.resume.renderer.base import Renderer
from runtime.resume.template import TemplateConfig


_CSS_TEMPLATE = """\
body {{
    font-family: {font_family};
    max-width: 800px;
    margin: 2em auto;
    padding: 0 1em;
    color: #333;
    line-height: 1.6;
}}
h1 {{ border-bottom: 2px solid {primary_color}; padding-bottom: 0.3em; }}
h2 {{ color: {primary_color}; margin-top: 1.5em; border-bottom: 1px solid #ddd; padding-bottom: 0.2em; }}
h3 {{ margin-bottom: 0.2em; }}
.section {{ margin-bottom: 1em; }}
.item {{ margin-bottom: 1em; }}
.meta {{ color: #666; font-size: 0.9em; }}
ul {{ margin-top: 0.3em; }}
.photo {{ float: {float_position}; margin-left: 20px; margin-bottom: 10px; }}
.personal-info {{ margin: 10px 0; font-size: 0.95em; }}
.personal-info span {{ margin-right: 15px; }}
"""


# Chinese labels for personal info fields
_PERSONAL_INFO_LABELS_ZH = {
    "gender": "性别",
    "birthDate": "出生年月",
    "ethnicity": "民族",
    "politicalStatus": "政治面貌",
    "phone": "电话",
    "email": "邮箱",
    "location": "所在地",
}

# English labels for personal info fields
_PERSONAL_INFO_LABELS_EN = {
    "gender": "Gender",
    "birthDate": "Date of Birth",
    "ethnicity": "Ethnicity",
    "politicalStatus": "Political Status",
    "phone": "Phone",
    "email": "Email",
    "location": "Location",
}


class HTMLRenderer(Renderer):
    """Render a ResumeIR as a self-contained HTML5 document."""

    def __init__(self) -> None:
        pass

    # -- Renderer ABC -------------------------------------------------------

    def render(self, ir: ResumeIR) -> str:  # noqa: D401
        """Produce an HTML resume string from *ir*."""
        # Load template
        template = TemplateConfig.load(ir.template_id) if ir.template_id else TemplateConfig.default()

        parts: List[str] = []

        # Document head with template-specific CSS
        parts.append("<!DOCTYPE html>")
        parts.append('<html lang="en">')
        parts.append("<head>")
        parts.append('<meta charset="utf-8">')
        parts.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
        parts.append("<title>Resume</title>")

        # Build CSS with template colors and fonts
        float_position = "right" if template.photo_position == "top-right" else "left"
        css = _CSS_TEMPLATE.format(
            font_family=html.escape(template.font_family),
            primary_color=html.escape(template.primary_color),
            float_position=float_position,
        )
        parts.append(f"<style>{css}</style>")
        parts.append("</head>")
        parts.append("<body>")

        # Header section with optional photo
        parts.append('<div class="header">')

        # Photo (if enabled and available)
        if template.show_photo and ir.basics.get("photo"):
            parts.append(self._render_photo(
                photo=ir.basics.get("photo", ""),
                position=template.photo_position,
                size=template.photo_size,
            ))

        # Name
        name = html.escape(ir.basics.get("name", "ResumeOS User"))
        parts.append(f"<h1>{name}</h1>")

        # Personal info block (if enabled)
        if template.show_personal_info:
            parts.append(self._render_personal_info(
                basics=ir.basics,
                fields=template.personal_info_fields,
                template=template,
            ))

        parts.append("</div>")

        if ir.target_company:
            parts.append(f'<p class="meta">{html.escape(ir.target_company)}</p>')

        # Summary section (if enabled and available)
        if template.show_summary and ir.summary:
            parts.append(f"<h2>{html.escape('Summary')}</h2>")
            parts.append(f"<p>{html.escape(ir.summary)}</p>")

        # Sections
        ordered = self._ordered_sections(ir)
        for section in ordered:
            # Skip self_evaluation section - it will be rendered separately
            if section.name == "self_evaluation":
                continue
            parts.append(f"<h2>{html.escape(section.title)}</h2>")
            parts.append('<div class="section">')
            for item in section.items:
                parts.append(self._render_item(item, section.name))
            parts.append("</div>")

        # Self-evaluation section (if enabled and available)
        if template.show_self_evaluation and ir.self_evaluation:
            title = template.get_section_title("self_evaluation")
            parts.append(self._render_self_evaluation(
                text=ir.self_evaluation,
                title=title,
            ))

        parts.append("</body>")
        parts.append("</html>")
        return "\n".join(parts)

    def file_extension(self) -> str:  # noqa: D102
        return "html"

    def format_name(self) -> str:  # noqa: D102
        return "HTML"

    # -- New helpers (Phase 2) ----------------------------------------------

    def _render_photo(self, photo: str, position: str, size: str) -> str:
        """Render a photo element.

        Args:
            photo: File path or base64 data URI (e.g. "data:image/jpeg;base64,...")
            position: "top-right" or "top-left"
            size: CSS size (e.g. "100px")

        Returns:
            HTML img tag with positioning class
        """
        # Use photo as src (could be file path or data URI)
        src = html.escape(photo)
        return f'<img src="{src}" alt="Photo" class="photo" style="width: {html.escape(size)}; height: {html.escape(size)};">'

    def _render_personal_info(
        self,
        basics: Dict[str, Any],
        fields: List[str],
        template: TemplateConfig,
    ) -> str:
        """Render a personal info block.

        Args:
            basics: Personal info dict from ResumeIR
            fields: List of field names to display (from template)
            template: TemplateConfig for language detection

        Returns:
            HTML div with personal info spans
        """
        # Choose label language based on template
        if template.cjk:
            labels = _PERSONAL_INFO_LABELS_ZH
        else:
            labels = _PERSONAL_INFO_LABELS_EN

        parts: List[str] = ['<div class="personal-info">']
        for field_name in fields:
            value = basics.get(field_name)
            if value:
                label = labels.get(field_name, field_name)
                parts.append(f'<span><strong>{label}:</strong> {html.escape(str(value))}</span>')
        parts.append("</div>")
        return "\n".join(parts)

    def _render_self_evaluation(self, text: str, title: str) -> str:
        """Render a self-evaluation section.

        Args:
            text: Self-evaluation text
            title: Section title (e.g. "自我评价")

        Returns:
            HTML section with heading and paragraph
        """
        parts: List[str] = []
        parts.append(f"<h2>{html.escape(title)}</h2>")
        parts.append(f"<p>{html.escape(text)}</p>")
        return "\n".join(parts)

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
        level = html.escape(str(content.get("level", content.get("proficiency", []))))
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
