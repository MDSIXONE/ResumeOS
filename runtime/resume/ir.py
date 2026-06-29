"""ResumeIR -- Resume Intermediate Representation (Sprint 5 core data model).

Per user directive (Sprint 5 review, ★★★★★):
    Resume is just a projection of the Career Knowledge Base.

    Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

ResumeIR sits between Knowledge and output formats. It is:
    - Immutable once created (Tailoring produces a NEW ResumeIR, never mutates one)
    - Deterministic (no LLM in the assembly pipeline -- pure rules)
    - Explainable (every item carries WHY it was selected and ranked)
    - Multi-format (Markdown / JSON Resume / HTML / PDF / DOCX all render FROM ResumeIR)

Knowledge is NEVER modified by the resume pipeline. Tailoring reads Knowledge,
produces a ResumeIR. Different JDs -> different ResumeIRs from the same Knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Explanation (Explainability ★★★★★)
# ---------------------------------------------------------------------------

@dataclass
class ResumeExplanation:
    """Why this item is in the resume.

    Click an item in the resume -> show this explanation.
    Makes the resume transparent and auditable.
    """

    matched_keywords: List[str] = field(default_factory=list)
    """Keywords from the JD (or ranking criteria) that matched this item."""

    selection_reason: str = ""
    """Human-readable reason: "JD keyword overlap", "required skill", "high impact", etc."""

    rank_factors: Dict[str, float] = field(default_factory=dict)
    """Individual ranking factors and their scores, e.g. {"keyword_overlap": 0.8, "recency": 0.6}."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched_keywords": self.matched_keywords,
            "selection_reason": self.selection_reason,
            "rank_factors": self.rank_factors,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResumeExplanation":
        return cls(
            matched_keywords=d.get("matched_keywords", []),
            selection_reason=d.get("selection_reason", ""),
            rank_factors=d.get("rank_factors", {}),
        )


# ---------------------------------------------------------------------------
# ResumeItem (a single entry in a section)
# ---------------------------------------------------------------------------

@dataclass
class ResumeItem:
    """A single item in a resume section.

    References a Knowledge entity by (entity_type, entity_id).
    Carries the content to render + the explanation of why it's here.
    """

    item_id: str = ""
    """Unique within this resume, e.g. 'proj-px4-uav'."""

    entity_type: str = ""
    """Knowledge entity type: 'project', 'job', 'education', 'skill', 'award', etc."""

    entity_id: str = ""
    """Knowledge entity ID (kebab-case), e.g. 'px4-uav'. Links back to KB."""

    section: str = ""
    """Resume section: 'projects', 'experience', 'education', 'skills', 'awards'."""

    title: str = ""
    """Display title for this item."""

    content: Dict[str, Any] = field(default_factory=dict)
    """Section-specific data. For a project: {role, timeline, stack, metrics, contribution, bullets}.
    For a skill: {level, last_used, category}. For education: {institution, degree, dates}."""

    explanation: ResumeExplanation = field(default_factory=ResumeExplanation)
    """WHY this item is in the resume (Explainability ★★★★★)."""

    rank_score: float = 0.0
    """Overall ranking score (0.0 to 1.0). Higher = more relevant to the target JD."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "section": self.section,
            "title": self.title,
            "content": self.content,
            "explanation": self.explanation.to_dict(),
            "rank_score": self.rank_score,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResumeItem":
        return cls(
            item_id=d.get("item_id", ""),
            entity_type=d.get("entity_type", ""),
            entity_id=d.get("entity_id", ""),
            section=d.get("section", ""),
            title=d.get("title", ""),
            content=d.get("content", {}),
            explanation=ResumeExplanation.from_dict(d.get("explanation", {})),
            rank_score=d.get("rank_score", 0.0),
        )


# ---------------------------------------------------------------------------
# ResumeSection
# ---------------------------------------------------------------------------

@dataclass
class ResumeSection:
    """A section of the resume (e.g. 'projects', 'skills', 'education')."""

    name: str = ""
    """Section identifier: 'projects', 'experience', 'education', 'skills', 'awards'."""

    title: str = ""
    """Display title: 'Projects', 'Work Experience', 'Education', 'Skills', 'Awards'."""

    items: List[ResumeItem] = field(default_factory=list)
    """Items in this section, ordered by rank_score (highest first)."""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResumeSection":
        return cls(
            name=d.get("name", ""),
            title=d.get("title", ""),
            items=[ResumeItem.from_dict(i) for i in d.get("items", [])],
        )


# ---------------------------------------------------------------------------
# ResumeIR (the top-level intermediate representation)
# ---------------------------------------------------------------------------

@dataclass
class ResumeIR:
    """Resume Intermediate Representation (★★★★★).

    The central data structure of the Resume Assembly Engine.

        Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

    ResumeIR is:
        - Immutable in spirit (Tailoring creates a new one, doesn't mutate)
        - Format-agnostic (Renderer converts to Markdown/JSON/HTML/PDF/DOCX)
        - Explainable (every item has an explanation)
        - Provenance-tracked (links back to the Knowledge Base that produced it)

    Tailoring NEVER modifies Knowledge. It reads Knowledge and produces a
    ResumeIR. Different JDs produce different ResumeIRs from the same Knowledge.
    """

    ir_id: str = ""
    """Unique ID for this resume version (auto-generated if empty)."""

    target_jd: str = ""
    """Job description text (empty if generic / untailored resume)."""

    target_company: str = ""
    """Company name (empty if generic)."""

    template_id: str = "classic-ats"
    """Which layout template was used (e.g. 'classic-ats', 'chinese-resume')."""

    sections: List[ResumeSection] = field(default_factory=list)
    """Ordered resume sections. Order is determined by Layout + template."""

    layout: str = "one-page"
    """Layout mode: 'one-page' or 'two-page'."""

    section_order: List[str] = field(default_factory=list)
    """Ordered section names, e.g. ['education', 'experience', 'projects', ...]."""

    basics: Dict[str, Any] = field(default_factory=dict)
    """Personal info: name, photo, email, phone, gender, birthDate, ethnicity,
    politicalStatus, location, website, github, linkedin.
    Populated from resumeos.config.yaml:profile. Needed for Chinese resume
    (photo + personal info) and any template that shows contact details."""

    summary: str = ""
    """Professional summary / profile statement. Optional; shown by templates
    that have fields.show_summary=true."""

    self_evaluation: str = ""
    """自我评价 (self-evaluation). Chinese resume convention, distinct from
    summary. Shown by templates that have fields.show_self_evaluation=true."""

    created_at: str = ""
    """ISO 8601 timestamp (auto-filled if empty)."""

    provenance: Dict[str, str] = field(default_factory=dict)
    """How this ResumeIR was produced:
    - 'generated_by': 'resume_assembly_engine'
    - 'source_kb': hash or path of the Knowledge Base used
    - 'selector': selector version/config
    - 'ranker': ranker version/config
    - 'layout': layout version/config
    """

    def __post_init__(self) -> None:
        if not self.ir_id:
            import uuid
            self.ir_id = f"resume-{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.section_order and self.sections:
            self.section_order = [s.name for s in self.sections]

    # -- Serialization ----------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ir_id": self.ir_id,
            "target_jd": self.target_jd,
            "target_company": self.target_company,
            "template_id": self.template_id,
            "sections": [s.to_dict() for s in self.sections],
            "layout": self.layout,
            "section_order": self.section_order,
            "basics": self.basics,
            "summary": self.summary,
            "self_evaluation": self.self_evaluation,
            "created_at": self.created_at,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResumeIR":
        return cls(
            ir_id=d.get("ir_id", ""),
            target_jd=d.get("target_jd", ""),
            target_company=d.get("target_company", ""),
            template_id=d.get("template_id", "classic-ats"),
            sections=[ResumeSection.from_dict(s) for s in d.get("sections", [])],
            layout=d.get("layout", "one-page"),
            section_order=d.get("section_order", []),
            basics=d.get("basics", {}),
            summary=d.get("summary", ""),
            self_evaluation=d.get("self_evaluation", ""),
            created_at=d.get("created_at", ""),
            provenance=d.get("provenance", {}),
        )

    def serialize(self, path: "Path") -> None:
        """Write ResumeIR to a JSON file."""
        import json
        from pathlib import Path as _Path

        p = _Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def deserialize(cls, path: "Path") -> "ResumeIR":
        """Read ResumeIR from a JSON file."""
        import json
        from pathlib import Path as _Path

        data = json.loads(_Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    # -- Queries ----------------------------------------------------------

    @property
    def all_items(self) -> List[ResumeItem]:
        """All items across all sections, flattened."""
        items: List[ResumeItem] = []
        for section in self.sections:
            items.extend(section.items)
        return items

    @property
    def item_count(self) -> int:
        return len(self.all_items)

    def find_item(self, item_id: str) -> Optional[ResumeItem]:
        """Find an item by its item_id. Returns None if not found."""
        for item in self.all_items:
            if item.item_id == item_id:
                return item
        return None

    def explain(self, item_id: str) -> Optional[ResumeExplanation]:
        """Get the explanation for why an item is in the resume.

        This is the Explainability API (★★★★★):
        click an item in the resume -> show its explanation.
        """
        item = self.find_item(item_id)
        if item is None:
            return None
        return item.explanation

    def get_section(self, name: str) -> Optional[ResumeSection]:
        """Get a section by name. Returns None if not found."""
        for section in self.sections:
            if section.name == name:
                return section
        return None
