"""Review — Knowledge vs ResumeIR gap analysis (Sprint 5).

Per user directive (Sprint 5):
    Resume is just a projection of the Career Knowledge Base.

Resume Review compares what's in Knowledge vs what made it into the ResumeIR.
It reports gaps (e.g. skills in KB that didn't make it into the resume).

NO LLM — pure rule-based comparison. Knowledge and ResumeIR are NEVER modified.
"""
from __future__ import annotations

from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.knowledge_index import KnowledgeIndex
    from runtime.resume.ir import ResumeIR


class ResumeReview:
    """Compare Knowledge entities vs ResumeIR items and report gaps.

    Resume Review is an audit tool: it identifies entities that exist in the
    Knowledge Base but were not selected for the ResumeIR. This helps users
    understand coverage gaps (e.g. "I have 10 skills in KB but only 3 made it
    into the resume — why?").

    NO LLM — pure rule-based comparison. Inputs are NEVER modified.
    """

    def __init__(self) -> None:
        """Initialise ResumeReview (stateless, no configuration needed)."""
        pass

    def review(
        self,
        kb_index: "KnowledgeIndex",
        ir: "ResumeIR",
    ) -> Dict[str, Any]:
        """Compare Knowledge vs ResumeIR and report gaps.

        Args:
            kb_index: KnowledgeIndex to query (read-only, NEVER modified)
            ir: ResumeIR to audit (read-only, NEVER modified)

        Returns:
            Dict with at least these keys:
            {
                "skill_gaps": [{
                    "in_kb": [...],
                    "in_resume": [...],
                    "missing": [...]
                }],
                "summary": {
                    "total_kb_skills": int,
                    "total_resume_skills": int,
                    "missing_count": int
                }
            }

        Constraint:
            kb_index and ir are NEVER modified. Review only reads them.
        """
        # -- Step 1: Query all skills from Knowledge --
        kb_skills = kb_index.query(entity_type="skill")
        kb_skill_ids = {s["id"] for s in kb_skills}

        # -- Step 2: Get all skills from ResumeIR --
        ir_skill_ids = set()
        for item in ir.all_items:
            if item.entity_type == "skill":
                ir_skill_ids.add(item.entity_id)

        # -- Step 3: Compute gaps --
        missing_ids = kb_skill_ids - ir_skill_ids

        # Sort for deterministic output
        in_kb_sorted = sorted(kb_skill_ids)
        in_resume_sorted = sorted(ir_skill_ids)
        missing_sorted = sorted(missing_ids)

        # -- Step 4: Build report --
        report = {
            "skill_gaps": [{
                "in_kb": in_kb_sorted,
                "in_resume": in_resume_sorted,
                "missing": missing_sorted,
            }],
            "summary": {
                "total_kb_skills": len(kb_skill_ids),
                "total_resume_skills": len(ir_skill_ids),
                "missing_count": len(missing_ids),
            },
        }

        return report
