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

    Process: lowercase, tokenize on non-word boundaries (Unicode-aware — keeps
    CJK characters like 智能体/规划/决策), filter stopwords, keep terms >= 2 chars.

    Args:
        jd: Job description text.

    Returns:
        List of lowercase keywords (deduplicated, order preserved).
    """
    if not jd:
        return []

    # Unicode-aware tokenisation: [^\W_] matches letters + digits in any script
    # (Latin, CJK, Cyrillic, etc.) but excludes underscore. This preserves
    # Chinese terms like "智能体", "向量检索" instead of dropping them.
    tokens = re.findall(r"[^\W_]+", jd.lower(), flags=re.UNICODE)

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


def build_searchable_set(entity: Dict) -> Set[str]:
    """Collect all lowercase searchable strings from an entity summary.

    Matches against every field that carries keyword signal:
        - title (falls back to key_fields.name for skills)
        - tags
        - key_fields.name       (skill canonical name)
        - key_fields.role       (project/job role)
        - key_fields.stack      (flattened tech stack list)
        - key_fields.ats_keywords
        - key_fields.synonyms   (skill aliases)
        - key_fields.category   (skill category)

    Scalar string fields are tokenised so that ``"robotics"`` matches a title
    like ``"Advanced Robotics System"``. Multi-word phrases (e.g. ``"computer
    vision"``, ``"智能体开发"``) are added as whole strings too so exact phrase
    matching works. This is the shared matching surface used by both Selector
    and Ranker. Adding a field here automatically widens JD relevance matching.
    """
    result: Set[str] = set()

    def _add_text(val: str) -> None:
        """Add a string value: both as-is (lower) and tokenised into words."""
        s = str(val).lower().strip()
        if not s:
            return
        result.add(s)
        for tok in re.findall(r"[^\W_]+", s, flags=re.UNICODE):
            if len(tok) >= 2:
                result.add(tok)

    def _add_list(items: Any) -> None:
        if isinstance(items, list):
            for item in items:
                _add_text(item)

    # Title (already falls back to name in KnowledgeIndex.build)
    _add_text(entity.get("title", ""))

    # Tags
    _add_list(entity.get("tags"))

    # Key fields (type-specific high-signal fields from the index)
    kf = entity.get("key_fields") or {}

    # Scalar string fields
    for key in ("name", "role", "category"):
        _add_text(kf.get(key, ""))

    # List fields
    for key in ("stack", "ats_keywords", "synonyms"):
        _add_list(kf.get(key))

    # Also check top-level name (for entities not yet index-rebuilt)
    _add_text(entity.get("name", ""))

    return result


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
            entity: Entity dict with keys id, title, type, tags, path,
                    optionally key_fields (from KnowledgeIndex).
            keywords: List of JD keywords (lowercase).

        Returns:
            True if at least one keyword appears in the entity's searchable
            surface (title, tags, name, role, stack, ats_keywords, synonyms).
        """
        searchable = build_searchable_set(entity)
        for kw in keywords:
            if kw in searchable:
                return True
        return False
