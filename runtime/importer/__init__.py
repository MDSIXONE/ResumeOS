"""ResumeOS Importer Runtime — Sprint 2.5.

The Importer produces Artifact objects from raw source files. Pipeline:

    Detector  →  Extractor  →  Normalizer  →  Artifact

The Importer is ZERO AI: no LLM SDKs, only deterministic parsers
(pypdf, python-docx, Pillow EXIF, regex, subprocess to git). Output
is an Artifact — the Importer never writes Markdown.

Design constraints (user directive + ADR-0019):
    - runtime/importer/ imports only runtime/artifacts/ (leaf) + stdlib.
    - No skills/ imports from runtime/ (dependency direction).
    - 13-type detected_type enum from inbox-workflow.md §4.
"""

from runtime.importer.pipeline import ImporterPipeline
from runtime.importer.registry import ImporterRegistry

__all__ = ["ImporterPipeline", "ImporterRegistry"]
