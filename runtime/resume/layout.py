"""Layout — section grouping and page constraints for Resume Assembly (Sprint 5).

Per user directive (Sprint 5):
    Resume is just a projection of the Career Knowledge Base.
    Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

The Layout stage:
    1. Groups ResumeItems by their section field
    2. Creates ResumeSection objects with display titles
    3. Applies page constraints (one-page = cap items per section)
    4. Orders sections in ATS-friendly order (skills first)
    5. Produces the final ResumeIR

NO LLM — pure rule-based layout logic.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from runtime.resume.ir import ResumeIR, ResumeItem, ResumeSection


# ---------------------------------------------------------------------------
# Section display titles
# ---------------------------------------------------------------------------

_SECTION_TITLES: Dict[str, str] = {
    "skills": "Skills",
    "experience": "Work Experience",
    "projects": "Projects",
    "education": "Education",
    "awards": "Awards & Honors",
}

# ---------------------------------------------------------------------------
# One-page layout: max items per section
# ---------------------------------------------------------------------------

_ONE_PAGE_CAPS: Dict[str, int] = {
    "projects": 4,
    "experience": 3,
    "education": 2,
    "skills": 10,
    "awards": 3,
}

# ---------------------------------------------------------------------------
# Default section order (ATS-friendly: skills first)
# ---------------------------------------------------------------------------

_DEFAULT_SECTION_ORDER: List[str] = [
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
        - Ordering sections (skills first for ATS compatibility)

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
    ) -> ResumeIR:
        """Group items into sections and produce a ResumeIR.

        Args:
            items: Ranked ResumeItems (from Ranker), already sorted by rank_score.
            layout_mode: "one-page" or "two-page". One-page caps items per section.

        Returns:
            ResumeIR with sections, section_order, and provenance metadata.

        Behavior:
            - Group items by their section field
            - For one-page: cap each section to _ONE_PAGE_CAPS limits
            - Create ResumeSection objects with display titles
            - Order sections according to _DEFAULT_SECTION_ORDER
            - Set layout and provenance metadata on ResumeIR
        """
        # -- Step 1: Group items by section --
        section_groups: Dict[str, List[ResumeItem]] = {}
        for item in items:
            sec = item.section
            if sec not in section_groups:
                section_groups[sec] = []
            section_groups[sec].append(item)

        # -- Step 2: Apply one-page caps --
        caps = _ONE_PAGE_CAPS if layout_mode == "one-page" else {}
        for section_name, section_items in section_groups.items():
            cap = caps.get(section_name)
            if cap is not None and len(section_items) > cap:
                # Keep only the top 'cap' items (already sorted by rank_score descending)
                section_groups[section_name] = section_items[:cap]

        # -- Step 3: Create ResumeSection objects --
        sections: List[ResumeSection] = []
        for section_name in _DEFAULT_SECTION_ORDER:
            section_items = section_groups.get(section_name)
            if not section_items:
                continue  # Skip empty sections

            display_title = _SECTION_TITLES.get(section_name, section_name.title())
            sections.append(ResumeSection(
                name=section_name,
                title=display_title,
                items=section_items,
            ))

        # -- Step 4: Build ResumeIR --
        section_order = [s.name for s in sections]

        ir = ResumeIR(
            sections=sections,
            layout=layout_mode,
            section_order=section_order,
            provenance={
                "generated_by": "resume_assembly_engine",
                "layout": layout_mode,
            },
        )

        return ir
