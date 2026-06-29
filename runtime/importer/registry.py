"""ImporterRegistry — maps file kinds to Extractor classes.

The registry is a thin table-driven wrapper around the 5 concrete
extractors shipped in Sprint 2.5. It lets users add an extractor for
a new file kind (``register("pptx", PptxExtractor())``) without
touching the Pipeline itself, and keeps the extractor mapping in one
place instead of sprinkled through conditionals.

Kinds registered out of the box:

    pdf    →  PDFTextExtractor
    docx   →  DOCXTextExtractor
    image  →  ImageExtractor
    git    →  GitExtractor        (directory with .git/)
    readme →  READMEExtractor     (README.md)

The registry also handles the inverse mapping: given a path, derive
the kind string (see :meth:`kind_for_path`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Type

from runtime.importer.extractor import Extractor
from runtime.importer.extractors.pdf_text import PDFTextExtractor
from runtime.importer.extractors.docx_text import DOCXTextExtractor
from runtime.importer.extractors.readme_parser import READMEExtractor
from runtime.importer.extractors.git_log import GitExtractor
from runtime.importer.extractors.image_exif import ImageExtractor


class ImporterRegistry:
    """Registry mapping file kinds to Extractor instances.

    Instances are created eagerly on ``__init__``. Register new
    extractors with :meth:`register` at any time after construction.
    """

    # File extensions → kind. Lower-case.
    EXT_TO_KIND: Dict[str, str] = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".gif": "image",
        ".bmp": "image",
        ".webp": "image",
        ".tiff": "image",
        ".tif": "image",
    }

    def __init__(self) -> None:
        self._extractors: Dict[str, Extractor] = {}
        # Seed the registry with the five extractors from Sprint 2.5.
        self.register("pdf", PDFTextExtractor())
        self.register("docx", DOCXTextExtractor())
        self.register("image", ImageExtractor())
        self.register("git", GitExtractor())
        self.register("readme", READMEExtractor())

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, kind: str, extractor: Extractor) -> None:
        """Register *extractor* under *kind*. Overwrites previous bindings."""
        if not isinstance(extractor, Extractor):
            raise TypeError(
                f"expected Extractor instance, got {type(extractor).__name__}"
            )
        self._extractors[kind] = extractor

    def get_extractor(self, kind: str) -> Extractor:
        """Return the extractor bound to *kind*, or raise KeyError."""
        if kind not in self._extractors:
            raise KeyError(
                f"no extractor registered for kind {kind!r}; "
                f"have: {sorted(self._extractors)}"
            )
        return self._extractors[kind]

    def has(self, kind: str) -> bool:
        return kind in self._extractors

    # ------------------------------------------------------------------
    # Path → kind
    # ------------------------------------------------------------------

    def kind_for_path(self, path: Path) -> str:
        """Derive the registry kind string for *path*.

        Precedence:
            1. Directory with ``.git/`` → ``git``
            2. Filename is a README.md (case-insensitive) → ``readme``
            3. Extension match (see EXT_TO_KIND) → that kind
            4. Unknown → raises KeyError
        """
        path = Path(path)

        if _is_git_dir(path):
            return "git"
        # Check filename pattern without requiring file existence
        if "readme.md" in path.name.lower():
            return "readme"
        ext = path.suffix.lower()
        if ext in self.EXT_TO_KIND:
            return self.EXT_TO_KIND[ext]
        raise KeyError(
            f"no kind mapping for path={path.name!r}; "
            f"extension {ext!r} not in {sorted(self.EXT_TO_KIND.keys())}"
        )


def _is_git_dir(path: Path) -> bool:
    try:
        return path.is_dir() and (path / ".git").is_dir()
    except OSError:
        return False
