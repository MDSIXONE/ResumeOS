"""Stage 1 of the Importer pipeline: Detector.

The Detector inspects a source file (or directory) and returns a
:class:`DetectionResult` containing:

- ``detected_type``: one of the 13-type enum values defined in
  ``docs/ux/inbox-workflow.md`` §4, or a MIME-level type (``pdf``,
  ``docx``) that will be narrowed by the Normalizer in stage 3.
- ``confidence``: 0.0–1.0, how confident the detector is.
- ``signals``: free-form string notes listing the signals
  (``extension=.pdf``, ``.git directory present``, …) that led to the
  detection, in priority order.

For Sprint 2.5 we support exactly this mapping from path → detected_type:

    path is a directory containing ``.git/``    →  ``git_repository``
    filename is ``readme.md`` (case-insensitive) →  ``readme``
    extension ``.pdf``                          →  ``pdf``
    extension ``.docx``                         →  ``docx``
    extension in the image set                  →  ``image``
    anything else                               →  ``unknown``

``pdf`` and ``docx`` are MIME-level types; stage 3 narrows to the
semantic type (``resume``, ``research_paper``, ``certificate``,
``competition``). The others are semantic directly.

This class deliberately does NOT read the file body. The MimeDetector
inspects only the path + magic byte sample. Content-aware detectors
(e.g. slide-deck sniff) can be added later via the ``Detector`` ABC.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------------
# DetectionResult
# ---------------------------------------------------------------------------

@dataclass
class DetectionResult:
    """A deterministic detection output.

    Carries the detected type, a 0.0–1.0 confidence, and the list of
    signals that drove the decision — so the Normalizer and downstream
    consumers can cite why a type was chosen (provenance).
    """

    detected_type: str
    confidence: float
    signals: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Detector ABC
# ---------------------------------------------------------------------------

class Detector(ABC):
    """Abstract detector.

    Subclasses inspect a path (and an optional content sample) and
    return a :class:`DetectionResult`. Detectors must be deterministic
    and side-effect free.
    """

    @abstractmethod
    def detect(self, path: Path, content_sample: bytes = b"") -> DetectionResult:
        """Detect the type of ``path``."""
        ...  # pragma: no cover


# ---------------------------------------------------------------------------
# MimeDetector — first-pass detection
# ---------------------------------------------------------------------------

class MimeDetector(Detector):
    """MIME + filename based first-pass detector.

    Order of precedence (first match wins):

    1. Directory containing ``.git/`` → ``git_repository`` (0.95).
    2. Filename containing ``README.md`` (case-insensitive, e.g.
       ``README.md``, ``sample-README.md``, ``README.MD``) → ``readme``
       (0.9).
    3. Extension → ``pdf`` / ``docx`` / ``image`` (0.8).
    4. Nothing matched → ``unknown`` (0.0).

    ``pdf`` and ``docx`` are MIME-level; the Normalizer later classifies
    them to the semantic enum. ``image``, ``readme``, ``git_repository``
    are semantic directly.
    """

    IMAGE_EXTS = {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif",
    }

    def detect(self, path: Path, content_sample: bytes = b"") -> DetectionResult:
        """Detect the type of *path* using name + extension + git-dir probe."""
        path = Path(path)
        name_lower = path.name.lower()

        # 1. Directory with a .git subdirectory → git_repository.
        try:
            git_dir = path / ".git"
            if git_dir.is_dir():
                return DetectionResult(
                    "git_repository", 0.95,
                    [".git directory present", f"path.name={path.name}"],
                )
        except OSError:
            pass

        # 2. README.md (case-insensitive) matches *readme.md → readme.
        if "readme.md" in name_lower:
            return DetectionResult(
                "readme", 0.90,
                ["filename matches *readme.md"],
            )

        # 3. Extension-based.
        ext = path.suffix.lower()
        if ext == ".pdf":
            return DetectionResult("pdf", 0.80, [f"extension={ext}"])
        if ext == ".docx":
            return DetectionResult("docx", 0.80, [f"extension={ext}"])
        if ext in self.IMAGE_EXTS:
            return DetectionResult("image", 0.80, [f"extension={ext}"])

        # 4. Unknown.
        return DetectionResult(
            "unknown", 0.0,
            [f"no matcher for path={path.name}"],
        )
