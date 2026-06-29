"""Tailoring — JD-tailored ResumeIR generation (Sprint 5).

Per user directive (Sprint 5):
    Resume is just a projection of the Career Knowledge Base.

Tailoring is the use-case: "given this JD, produce a ResumeIR from Knowledge".
It is a thin wrapper around ResumeAssemblyPipeline representing the
"JD → ResumeIR" operation. Knowledge is NEVER modified.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from runtime.resume.pipeline import ResumeAssemblyPipeline

if TYPE_CHECKING:
    from runtime.knowledge_index import KnowledgeIndex
    from runtime.resume.ir import ResumeIR


class Tailoring:
    """JD-tailored ResumeIR generation.

    Tailoring = "given a JD, produce a customised ResumeIR from Knowledge".

    This is a thin wrapper around ``ResumeAssemblyPipeline`` that represents
    the tailoring use-case: different JDs → different ResumeIRs from the
    same Knowledge. Knowledge is NEVER modified.
    """

    def __init__(self) -> None:
        """Initialise Tailoring with a default pipeline."""
        self._pipeline = ResumeAssemblyPipeline()

    def tailor(
        self,
        kb_index: "KnowledgeIndex",
        jd: str,
        company: str = "",
        template_id: str = "",
        basics: Optional[Dict[str, Any]] = None,
        summary: str = "",
        self_evaluation: str = "",
    ) -> "ResumeIR":
        """Produce a JD-tailored ResumeIR from Knowledge.

        Args:
            kb_index: KnowledgeIndex to query (read-only, NEVER modified)
            jd: Job description text
            company: Target company name (optional, for metadata)
            template_id: Layout template ID (e.g. 'chinese-resume').
                Empty = use default ('classic-ats').
            basics: Personal info dict (name, photo, email, phone, gender, etc.).
            summary: Professional summary text.
            self_evaluation: 自我评价 text.

        Returns:
            ResumeIR tailored to the given JD

        Constraint:
            kb_index is NEVER modified. Tailoring only reads Knowledge.
        """
        ir = self._pipeline.assemble(
            kb_index,
            jd=jd,
            company=company,
            template_id=template_id,
            basics=basics,
            summary=summary,
            self_evaluation=self_evaluation,
        )
        return ir
