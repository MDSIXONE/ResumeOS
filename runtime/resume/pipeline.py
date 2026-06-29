"""Pipeline — end-to-end Resume Assembly orchestration.

Per user directive (Sprint 5):
    Resume is just a projection of the Career Knowledge Base.
    Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

The Pipeline orchestrates the three stages:
    1. Selector: filter entities by JD keywords
    2. Ranker: score and sort selected entities
    3. Layout: group into sections, apply page constraints, produce ResumeIR

When a template_id is provided, the Pipeline loads the TemplateConfig and
passes it to Layout. This enables different visual layouts (e.g. Chinese
resume with 教育背景→工作经历→... ordering) from the same Knowledge.

NO LLM — pure rule-based assembly. Knowledge is NEVER modified.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from runtime.resume.selector import Selector
from runtime.resume.ranker import Ranker
from runtime.resume.layout import Layout
from runtime.resume.template import TemplateConfig

if TYPE_CHECKING:
    from runtime.knowledge_index import KnowledgeIndex
    from runtime.resume.ir import ResumeIR


class ResumeAssemblyPipeline:
    """End-to-end Resume Assembly pipeline.

    Orchestrates:
        KnowledgeIndex -> Selector -> Ranker -> Layout(template) -> ResumeIR

    NO LLM — pure rule-based assembly. Knowledge is NEVER modified (read-only).
    """

    def __init__(
        self,
        selector: Optional[Selector] = None,
        ranker: Optional[Ranker] = None,
        layout: Optional[Layout] = None,
    ) -> None:
        """Initialise pipeline with optional dependency injection.

        Args:
            selector: Selector instance (created if None)
            ranker: Ranker instance (created if None)
            layout: Layout instance (created if None)
        """
        self.selector = selector or Selector()
        self.ranker = ranker or Ranker()
        self.layout = layout or Layout()

    def assemble(
        self,
        kb_index: "KnowledgeIndex",
        jd: str = "",
        company: str = "",
        template_id: str = "",
        basics: Optional[Dict[str, Any]] = None,
        summary: str = "",
        self_evaluation: str = "",
    ) -> "ResumeIR":
        """Assemble a ResumeIR from a KnowledgeIndex and optional JD.

        Args:
            kb_index: KnowledgeIndex to query (read-only, NEVER modified)
            jd: Job description text (empty = generic resume)
            company: Target company name (for ResumeIR metadata)
            template_id: Layout template ID (e.g. 'chinese-resume').
                Empty = use default ('classic-ats').
            basics: Personal info dict (name, photo, email, phone, gender,
                birthDate, etc.). Populated from resumeos.config.yaml:profile.
            summary: Professional summary text (shown by templates with
                fields.show_summary=true).
            self_evaluation: 自我评价 text (shown by templates with
                fields.show_self_evaluation=true).

        Returns:
            ResumeIR ready for rendering

        Constraint:
            kb_index is NEVER modified. Pipeline only calls kb_index.query().
        """
        # -- Load template config --
        if template_id:
            template = TemplateConfig.load(template_id)
        else:
            template = TemplateConfig.default()

        # -- Step 1: Query all entities from Knowledge --
        all_entities = kb_index.query()

        # -- Step 2: Select relevant entities --
        selected = self.selector.select(all_entities, jd=jd)

        # -- Step 3: Rank and convert to ResumeItems --
        ranked = self.ranker.rank(selected, jd=jd)

        # -- Step 4: Arrange into sections (template-driven) --
        ir = self.layout.arrange(ranked, layout_mode="one-page", template=template)

        # -- Step 5: Set metadata --
        ir.target_jd = jd
        ir.target_company = company
        ir.template_id = template.template_id

        # -- Step 6: Set personal info (basics/summary/self_evaluation) --
        if basics:
            ir.basics = basics
        ir.summary = summary
        ir.self_evaluation = self_evaluation

        return ir
