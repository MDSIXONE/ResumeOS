"""Stage 2 of the Importer pipeline: Extractor.

An Extractor receives a path and a :class:`DetectionResult` from stage 1
and returns a raw ``dict`` of extracted fields. The dict is NOT an
Artifact — that is stage 3's job (:mod:`runtime.importer.normalizer`).

Each Extractor is zero-AI: it uses only stdlib + deterministic parsers
(``pypdf``, ``python-docx``, ``Pillow`` EXIF, ``regex``,
``subprocess`` to ``git``). No LLM. No network.

The raw dict shape is extractor-specific (e.g. ``PDFTextExtractor``
returns ``{text, page_count, metadata, notes}``). The Normalizer in
stage 3 knows how to map each extractor's field dict into the right
Artifact subclass.

All extractors MUST include a ``notes`` list: low-confidence signals,
warnings, or missing-field notes that the Normalizer carries through
onto the final Artifact.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

from runtime.importer.detector import DetectionResult


# ---------------------------------------------------------------------------
# Extractor ABC
# ---------------------------------------------------------------------------

class Extractor(ABC):
    """Abstract Extractor.

    Subclasses implement :meth:`extract` which returns a raw fields
    dict. The dict must be JSON-serializable (no bytes, no datetime
    objects) and include a ``notes`` key with a list of strings.
    """

    @abstractmethod
    def extract(self, path: Path, detection: DetectionResult) -> Dict[str, Any]:
        """Extract raw fields from *path*.

        Returns a dict (JSON-safe) with at least a ``notes`` key.
        """
        ...  # pragma: no cover
