"""Ranker — rule-based scoring and sorting of selected entities (Sprint 5).

Per user directive (Sprint 5):
    Resume is just a projection of the Career Knowledge Base.
    Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

The Ranker converts selected entity dicts into ResumeItems with:
    - Unique item_ids  (e.g. "proj-px4-uav", "skill-python")
    - Section mapping  (entity type -> resume section)
    - Ranking scores   (keyword overlap + recency + impact)
    - Explanations     (WHY this item is in the resume — Explainability ★★★★★)

NO LLM — pure rule-based scoring.
"""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from runtime.resume.ir import ResumeExplanation, ResumeItem
from runtime.resume.selector import build_searchable_set


# ---------------------------------------------------------------------------
# Entity type → resume section mapping
# ---------------------------------------------------------------------------

_ENTITY_TYPE_TO_SECTION: Dict[str, str] = {
    "project": "projects",
    "job": "experience",
    "education": "education",
    "skill": "skills",
    "award": "awards",
    "competition": "awards",
    "research": "projects",
    "internship": "experience",
    "opensource": "projects",
}

# Entity type → short prefix for item_id
_ENTITY_TYPE_SHORT: Dict[str, str] = {
    "project": "proj",
    "job": "job",
    "education": "edu",
    "skill": "skill",
    "award": "award",
    "competition": "comp",
    "research": "res",
    "internship": "intern",
    "opensource": "oss",
}

# Stopwords (must match Selector for consistency)
_STOPWORDS: frozenset = frozenset({
    "the", "a", "an", "with", "for", "and", "or", "you", "will", "work",
    "on", "in", "of", "to", "is", "are", "we", "looking", "experience",
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_keywords(text: str) -> Set[str]:
    """Extract meaningful keywords from JD text (same logic as Selector).

    Unicode-aware: keeps CJK characters (智能体/规划/决策) instead of
    dropping them as non-ASCII-alphanumeric separators.
    """
    if not text:
        return set()
    words = re.findall(r"[^\W_]+", text.lower(), flags=re.UNICODE)
    return {w for w in words if w and w not in _STOPWORDS and len(w) >= 2}


def _count_keyword_overlap(
    entity: Dict[str, Any],
    keywords: Set[str],
) -> Tuple[int, List[str]]:
    """Count how many JD keywords overlap with the entity's searchable surface.

    Matches against title, tags, name, role, stack, ats_keywords, synonyms —
    the full surface from ``build_searchable_set``.

    Returns:
        (overlap_count, sorted list of matched keyword strings)
    """
    searchable = build_searchable_set(entity)

    matched: Set[str] = set()
    for kw in keywords:
        if kw.lower() in searchable:
            matched.add(kw)

    return len(matched), sorted(matched)


def _parse_date(val: Any) -> Optional[date]:
    """Best-effort parse of a date value from YAML frontmatter."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%Y-%m"):
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue
    return None


def _compute_rank_score(
    entity: Dict[str, Any],
    jd_keywords: Set[str],
    overlap_count: int,
) -> Tuple[float, Dict[str, float]]:
    """Compute composite rank_score and factor breakdown.

    rank_score = keyword_overlap (0-0.5) + recency (0-0.3) + impact (0-0.2)

    If no JD is given, rank_score = 0.5 (all equal).
    """
    has_jd = bool(jd_keywords)

    if not has_jd:
        return 0.5, {"keyword_overlap": 0.0, "recency": 0.0, "impact": 0.0}

    # --- keyword overlap score (0.0 - 0.5) ---
    total_kw = max(len(jd_keywords), 1)
    kw_score = min(overlap_count / total_kw, 1.0) * 0.5

    # --- recency score (0.0 - 0.3) ---
    kf = entity.get("key_fields") or {}
    timeline = kf.get("timeline") or entity.get("timeline")
    if isinstance(timeline, dict):
        end_val = timeline.get("end")
    else:
        end_val = None

    end_date = _parse_date(end_val)
    if end_date is not None:
        ref = date(2025, 1, 1)
        days_diff = max((ref - end_date).days, 0)
        max_days = 365 * 3  # 3-year window
        if days_diff >= max_days:
            rec_score = 0.0
        else:
            rec_score = (1.0 - days_diff / max_days) * 0.3
    else:
        rec_score = 0.0

    # --- impact score (0.0 - 0.2) ---
    metrics = kf.get("metrics") or entity.get("metrics")
    if metrics is not None and isinstance(metrics, (list, dict)) and len(metrics) > 0:
        imp_score = 0.2
    else:
        imp_score = 0.0

    total = min(kw_score + rec_score + imp_score, 1.0)

    factors = {
        "keyword_overlap": round(kw_score, 4),
        "recency": round(rec_score, 4),
        "impact": round(imp_score, 4),
    }
    return total, factors


# ---------------------------------------------------------------------------
# Ranker
# ---------------------------------------------------------------------------

class Ranker:
    """Score and rank selected entities by relevance to the JD.

    Second stage of the Resume Assembly pipeline:
        Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

    NO LLM — pure rule-based scoring (keyword overlap + recency + impact).
    """

    def __init__(self) -> None:
        """Initialise Ranker (stateless, no configuration needed)."""
        pass

    # ------------------------------------------------------------------ #

    def rank(self, entities: List[Dict[str, Any]], jd: str = "") -> List[ResumeItem]:
        """Convert selected entities to scored *ResumeItems*, sorted best-first.

        Args:
            entities: Selected entity dicts (may be enriched with full
                frontmatter fields like ``timeline``, ``metrics``, etc.).
            jd: Job description text.

        Returns:
            ``List[ResumeItem]`` sorted by ``rank_score`` descending.
        """
        keywords = _extract_keywords(jd)
        has_jd = bool(keywords)

        items: List[ResumeItem] = []
        for entity in entities:
            entity_type = entity.get("type", "")
            entity_id = entity.get("id", "")
            title = str(entity.get("title", ""))

            # -- item_id --
            type_short = _ENTITY_TYPE_SHORT.get(entity_type, entity_type[:4])
            item_id = f"{type_short}-{entity_id}"

            # -- section --
            section = _ENTITY_TYPE_TO_SECTION.get(entity_type, "projects")

            # -- content (gather all relevant fields from entity dict + key_fields) --
            content: Dict[str, Any] = {}
            kf = entity.get("key_fields") or {}
            for key in (
                "role", "timeline", "stack", "metrics", "contribution",  # project / job
                "proficiency", "level", "last_used", "category",          # skill
                "institution", "degree",                                   # education
                "rank", "date",                                            # award
            ):
                if key in kf:
                    content[key] = kf[key]
                elif key in entity:
                    content[key] = entity[key]

            # -- keyword overlap --
            overlap_count, matched_kw = _count_keyword_overlap(entity, keywords)

            # -- rank score --
            rank_score, rank_factors = _compute_rank_score(
                entity, keywords, overlap_count,
            )

            # -- explanation (Explainability ★★★★★) --
            explanation = ResumeExplanation(
                matched_keywords=matched_kw,
                selection_reason="JD keyword overlap" if has_jd else "generic inclusion",
                rank_factors=rank_factors,
            )

            items.append(ResumeItem(
                item_id=item_id,
                entity_type=entity_type,
                entity_id=entity_id,
                section=section,
                title=title,
                content=content,
                explanation=explanation,
                rank_score=rank_score,
            ))

        # Stable sort: highest score first
        items.sort(key=lambda i: i.rank_score, reverse=True)
        return items
