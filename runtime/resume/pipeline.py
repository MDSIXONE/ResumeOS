"""Pipeline — end-to-end Resume Assembly orchestration (Sprint 5).

Per user directive (Sprint 5):
    Resume is just a projection of the Career Knowledge Base.
    Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

The Pipeline orchestrates the three stages:
    1. Selector: filter entities by JD keywords
    2. Ranker: score and sort selected entities
    3. Layout: group into sections, apply page constraints, produce ResumeIR

NO LLM — pure rule-based assembly. Knowledge is NEVER modified.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from runtime.resume.selector import Selector
from runtime.resume.ranker import Ranker
from runtime.resume.layout import Layout

if TYPE_CHECKING:
    from runtime.knowledge_index import KnowledgeIndex
    from runtime.resume.ir import ResumeIR


class ResumeAssemblyPipeline:
    """End-to-end Resume Assembly pipeline.

    Orchestrates:
        KnowledgeIndex -> Selector -> Ranker -> Layout -> ResumeIR

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
    ) -> "ResumeIR":
        """Assemble a ResumeIR from a KnowledgeIndex and optional JD.

        Args:
            kb_index: KnowledgeIndex to query (read-only, NEVER modified)
            jd: Job description text (empty = generic resume)
            company: Target company name (for ResumeIR metadata)

        Returns:
            ResumeIR ready for rendering

        Constraint:
            kb_index is NEVER modified. Pipeline only calls kb_index.query().
        """
        # -- Step 1: Query all entities from Knowledge --
        all_entities = kb_index.query()

        # -- Step 2: Select relevant entities --
        selected = self.selector.select(all_entities, jd=jd)

        # -- Step 3: Rank and convert to ResumeItems --
        ranked = self.ranker.rank(selected, jd=jd)

        # -- Step 4: Arrange into sections (one-page layout) --
        ir = self.layout.arrange(ranked, layout_mode="one-page")

        # -- Step 5: Set metadata --
        ir.target_jd = jd
        ir.target_company = company

        return ir
