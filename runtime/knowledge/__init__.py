"""Knowledge layer -- the intermediate representation between Artifact and output.

Public API:
    KnowledgeObject    -- the intermediate entity representation
    KnowledgeProvenance -- traceability for generated knowledge
    Draft              -- unvalidated LLM output
    Conflict           -- a field where existing and new values differ
    ConflictDetector   -- static conflict detection utility
    KnowledgeWriter    -- abstract writer (ABC)
    MarkdownWriter     -- default Markdown renderer
"""
from __future__ import annotations

from runtime.knowledge.provenance import KnowledgeProvenance
from runtime.knowledge.conflict import Conflict, ConflictDetector
from runtime.knowledge.object import KnowledgeObject
from runtime.knowledge.draft import Draft
from runtime.knowledge.writer import KnowledgeWriter, MarkdownWriter

__all__ = [
    "KnowledgeObject",
    "KnowledgeProvenance",
    "Draft",
    "Conflict",
    "ConflictDetector",
    "KnowledgeWriter",
    "MarkdownWriter",
]
