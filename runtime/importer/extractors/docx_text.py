"""DOCX text extractor — zero-AI, python-docx only.

Extracts paragraphs and heading text from a DOCX file using
``python-docx``. Headings are identified by the style name starting
with the word ``Heading`` (the python-docx default naming).

No LLM. The output is a raw dict; the Normalizer in stage 3 decides
whether this DOCX is a résumé, certificate, or other semantic type
based on the text content.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from runtime.importer.detector import DetectionResult
from runtime.importer.extractor import Extractor


class DOCXTextExtractor(Extractor):
    """Extract paragraphs + headings from a DOCX with ``python-docx``."""

    HEADING_PREFIX = "Heading"

    def extract(self, path: Path, detection: DetectionResult) -> Dict[str, Any]:
        """Return ``{text, headings, paragraph_count, notes}``."""
        try:
            from docx import Document
        except ImportError as exc:  # pragma: no cover
            return {
                "text": "", "headings": [], "paragraph_count": 0,
                "notes": [f"python-docx not installed: {exc}"],
            }

        try:
            doc = Document(str(path))
        except Exception as exc:
            return {
                "text": "", "headings": [], "paragraph_count": 0,
                "notes": [f"DOCX parse error: {exc}"],
            }

        paragraphs: List[str] = []
        headings: List[str] = []
        for para in doc.paragraphs:
            text = para.text or ""
            paragraphs.append(text)
            # python-docx styles are named "Heading 1", "Heading 2", …
            style_name = (para.style.name if para.style else "") or ""
            if style_name.startswith(self.HEADING_PREFIX):
                headings.append(text)

        full_text = "\n".join(paragraphs)
        notes: List[str] = []
        if not full_text.strip():
            notes.append("DOCX yielded no paragraph text")

        return {
            "text": full_text,
            "headings": headings,
            "paragraph_count": len(paragraphs),
            "notes": notes,
        }
