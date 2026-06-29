"""Selector - JD-based entity filtering for the Resume Assembly Pipeline.

Sprint 5: Resume is just a projection of the Career Knowledge Base.

    Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

The Selector extracts keywords from a job description and filters entities
from the Knowledge Index to those relevant to the JD. Pure rule-based:
keyword matching against entity tags and titles. No LLM used.

Architectural constraints:
    - NO LLM SDK imports
    - NO Knowledge mutation (read-only)
    - NO imports from skills/ or runtime/builder/
"""
from __future__ import annotations

import re
from typing import Dict, List, Set


# Common stopwords to filter from JD text
_STOPWORDS: Set[str] = {
    "the", "a", "an", "with", "for", "and", "or", "you", "will",
    "work", "on", "in", "of", "to", "is", "are", "we", "looking",
    "experience",
}


def _extract_keywords(jd: str) -> List[str]:
    """Extract meaningful keywords from JD text.

    Process: lowercase, split on non-alphanumeric, filter stopwords,
    keep terms >= 2 chars.

    Args:
        jd: Job description text.

    Returns:
        List of lowercase keywords (deduplicated).
    """
    if not jd:
        return []

    # Lowercase and split on non-alphanumeric
    tokens = re.split(r"[^a-z0-9]+", jd.lower())

    # Filter stopwords and short tokens
    keywords = [
        t for t in tokens
        if t and t not in _STOPWORDS and len(t) >= 2
    ]

    # Deduplicate while preserving order
    seen: Set[str] = set()
    deduped: List[str] = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            deduped.append(kw)

    return deduped


class Selector:
    """Filter Knowledge entities by JD keyword relevance.

    Sprint 5: Selector is the first stage of the Resume Assembly Pipeline.
    It takes raw entities from KnowledgeIndex.query() and returns a subset
    whose tags or title overlap with JD keywords.

    If no JD is provided, all entities are selected (generic resume).

    Pure rules: keyword matching on tags/title. No LLM.
    """

    def __init__(self) -> None:
        """Initialise a Selector (stateless, no config needed)."""

    def select(self, entities: List[Dict], jd: str = "") -> List[Dict]:
        """Select entities relevant to the given JD.

        Args:
            entities: List of entity dicts from KnowledgeIndex.query().
                      Each dict has keys: id, title, type, tags, path.
            jd: Job description text. If empty, selects all entities.

        Returns:
            Subset of entities with keyword overlap > 0.
            Input list is NOT modified.

        Behavior:
            - Extract keywords from JD (lowercase, split, filter stopwords).
            - For each entity, count how many JD keywords appear in its tags
              (case-insensitive) or title.
            - Select entities with overlap > 0.
            - If no JD given, select ALL entities.
        """
        # Empty JD -> generic resume -> select all
        if not jd:
            return list(entities)  # return a copy to not modify input

        keywords = _extract_keywords(jd)
        if not keywords:
            return list(entities)

        selected: List[Dict] = []
        for entity in entities:
            if self._matches(entity, keywords):
                selected.append(entity)

        return selected

    def _matches(self, entity: Dict, keywords: List[str]) -> bool:
        """Check if entity matches any JD keyword.

        Args:
            entity: Entity dict with keys id, title, type, tags, path.
            keywords: List of JD keywords (lowercase).

        Returns:
            True if at least one keyword matches entity tags or title.
        """
        # Normalize entity tags to lowercase strings
        tags_raw = entity.get("tags", [])
        tags = [str(t).lower() for t in tags_raw] if tags_raw else []

        # Normalize title
        title = str(entity.get("title", "")).lower()

        # Check overlap
        for kw in keywords:
            if kw in tags:
                return True
            if kw in title:
                return True

        return False
