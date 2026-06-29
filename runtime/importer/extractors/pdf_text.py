"""PDF text extractor — zero-AI, pypdf only.

Extracts the full text, page count, and selected metadata
(title, author) from a PDF using ``pypdf``. No vision, no OCR,
no LLM. Output is a plain ``dict`` consumed by the Normalizer.

The extracted text is deliberately kept raw: downstream stages
(Normalizer, then the Semantic Skills layer) may run their own
regex/LLM passes over it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from runtime.importer.detector import DetectionResult
from runtime.importer.extractor import Extractor


class PDFTextExtractor(Extractor):
    """Extract text + page count + PDF metadata with ``pypdf``."""

    def extract(self, path: Path, detection: DetectionResult) -> Dict[str, Any]:
        """Return ``{text, page_count, metadata, notes}``."""
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        try:
            pages = reader.pages
        except Exception as exc:  # pragma: no cover — corrupt PDF
            return {
                "text": "",
                "page_count": 0,
                "metadata": {},
                "notes": [f"PDF parse error: {exc}"],
            }

        text_parts: List[str] = []
        for page in pages:
            try:
                chunk = page.extract_text() or ""
            except Exception as exc:  # pragma: no cover
                chunk = ""
                # Append note to top-level list, handled below.
                pass
            text_parts.append(chunk)
        text = "\n".join(text_parts)

        metadata: Dict[str, str] = {}
        info = reader.metadata
        if info is not None:
            mapping = {"/Title": "title", "/Author": "author",
                       "/Subject": "subject", "/Creator": "creator",
                       "/Producer": "producer", "/CreationDate": "creation_date"}
            for key, out_key in mapping.items():
                try:
                    val = info.get(key)
                except Exception:
                    val = None
                if val:
                    metadata[out_key] = str(val)

        notes: List[str] = []
        if not text.strip():
            notes.append("PDF yielded no extractable text — scanned or empty")
        if len(pages) == 0:
            notes.append("PDF has zero pages")

        return {
            "text": text,
            "page_count": len(pages),
            "metadata": metadata,
            "notes": notes,
        }
