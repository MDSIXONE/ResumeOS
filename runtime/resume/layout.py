"""Layout — section grouping and page constraints for Resume Assembly.

Per user directive (Sprint 5):
    Resume is just a projection of the Career Knowledge Base.
    Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

The Layout stage:
    1. Groups ResumeItems by their section field
    2. Creates ResumeSection objects with display titles
    3. Applies page constraints (one-page = cap items per section)
    4. Orders sections according to the active template's section_order
    5. Produces the final ResumeIR

When a TemplateConfig is provided, its section_order, section_titles, and caps
override the hardcoded defaults. This enables Chinese resume ordering
(教育背景→工作经历→...) and Chinese section titles (技能特长 instead of Skills).

NO LLM — pure rule-based layout logic.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from runtime.resume.ir import ResumeIR, ResumeItem, ResumeSection
from runtime.resume.template import TemplateConfig


# ---------------------------------------------------------------------------
# Fallback defaults (used when no TemplateConfig is provided — backward compat)
# ---------------------------------------------------------------------------

_FALLBACK_TITLES: Dict[str, str] = {
    "skills": "Skills",
    "experience": "Work Experience",
    "projects": "Projects",
    "education": "Education",
    "awards": "Awards & Honors",
}

_FALLBACK_CAPS: Dict[str, int] = {
    "projects": 4,
    "experience": 3,
    "education": 2,
    "skills": 10,
    "awards": 3,
}

_FALLBACK_SECTION_ORDER: List[str] = [
    "skills",
    "experience",
    "projects",
    "education",
    "awards",
]


class Layout:
    """Arrange ranked ResumeItems into ResumeSections within a ResumeIR.

    Third stage of the Resume Assembly pipeline:
        Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

    The Layout is responsible for:
        - Grouping items by section
        - Applying page constraints (one-page = cap items per section)
        - Ordering sections per the active template (or fallback defaults)
        - Setting section display titles per the active template

    When a TemplateConfig is provided, section_order/titles/caps come from the
    template YAML (e.g. Chinese resume uses 教育背景→工作经历→...).

    NO LLM — pure rule-based layout logic.
    """

    def __init__(self) -> None:
        """Initialise Layout (stateless, no configuration needed)."""
        pass

    # ---------------------------------------------------------------------- #

    def arrange(
        self,
        items: List[ResumeItem],
        layout_mode: str = "one-page",
        template: Optional[TemplateConfig] = None,
    ) -> ResumeIR:
        """Group items into sections and produce a ResumeIR.

        Args:
            items: Ranked ResumeItems (from Ranker), already sorted by rank_score.
            layout_mode: "one-page" or "two-page". One-page caps items per section.
            template: Optional TemplateConfig. When provided, its section_order,
                section_titles, and caps are used instead of the hardcoded defaults.

        Returns:
            ResumeIR with sections, section_order, and provenance metadata.
        """
        # -- Resolve section order, titles, caps from template or fallback --
        if template is not None:
            section_order = template.section_order or _FALLBACK_SECTION_ORDER
            caps = template.caps if layout_mode == "one-page" else {}
            template_id = template.template_id
        else:
            section_order = _FALLBACK_SECTION_ORDER
            caps = _FALLBACK_CAPS if layout_mode == "one-page" else {}
            template_id = "classic-ats"

        # -- Step 1: Group items by section --
        section_groups: Dict[str, List[ResumeItem]] = {}
        for item in items:
            sec = item.section
            if sec not in section_groups:
                section_groups[sec] = []
            section_groups[sec].append(item)

        # -- Step 2: Apply one-page caps --
        for section_name, section_items in section_groups.items():
            cap = caps.get(section_name)
            if cap is not None and len(section_items) > cap:
                section_groups[section_name] = section_items[:cap]

        # -- Step 3: Create ResumeSection objects --
        sections: List[ResumeSection] = []
        for section_name in section_order:
            section_items = section_groups.get(section_name)
            if not section_items:
                continue  # Skip empty sections

            # Title: from template, or fallback, or title-cased
            if template is not None:
                display_title = template.get_section_title(section_name)
            else:
                display_title = _FALLBACK_TITLES.get(section_name, section_name.title())
            sections.append(ResumeSection(
                name=section_name,
                title=display_title,
                items=section_items,
            ))

        # -- Step 4: Build ResumeIR --
        actual_order = [s.name for s in sections]

        ir = ResumeIR(
            sections=sections,
            layout=layout_mode,
            section_order=actual_order,
            template_id=template_id,
            provenance={
                "generated_by": "resume_assembly_engine",
                "layout": layout_mode,
                "template": template_id,
            },
        )

        return ir
