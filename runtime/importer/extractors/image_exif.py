"""Image EXIF extractor — zero-AI, Pillow only.

Reads an image's pixel dimensions, format, and a small curated set of
EXIF tags (DateTime, Make, Model). This is a METADATA extractor: it
does NOT classify what the image depicts — that would require a vision
model, which is explicitly forbidden in the Importer layer.

Caption hint is derived ONLY from the filename (e.g. ``award.jpg`` →
``caption_hint="award"``). It is a downstream Skill job to confirm or
refine the caption via vision.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from runtime.importer.detector import DetectionResult
from runtime.importer.extractor import Extractor


# EXIF tag ID → friendly name for the small set we carry through.
# Tag IDs from the TIFF / Exif spec — stable, numeric keys.
_EXIF_TAGS = {
    271: "Make",         # Camera manufacturer
    272: "Model",        # Camera model
    306: "DateTime",     # Image creation timestamp
    315: "Artist",       # Person who created the image
    36867: "DateTimeOriginal",
    36868: "DateTimeDigitized",
}

# Caption-hint keywords we look for in the filename stem.
_CAPTION_KEYWORDS = (
    "award", "certificate", "cert", "cv", "resume",
    "photo", "screenshot", "diagram", "trophy", "medal",
    "logo", "banner", "cover", "portrait",
)


class ImageExtractor(Extractor):
    """Extract dimensions + EXIF from an image with ``Pillow``."""

    def extract(self, path: Path, detection: DetectionResult) -> Dict[str, Any]:
        """Return ``{width, height, format, exif, caption_hint, notes}``."""
        from PIL import Image

        notes: list = []
        try:
            im = Image.open(path)
            im.load()  # force decode so size is valid
        except Exception as exc:
            return {
                "width": 0, "height": 0, "format": "",
                "exif": {}, "caption_hint": "",
                "notes": [f"image open error: {exc}"],
            }

        width, height = im.size
        fmt = (im.format or path.suffix.lstrip(".").upper() or "").upper()

        exif: Dict[str, str] = {}
        try:
            raw = im.getexif()
            for tag_id, friendly in _EXIF_TAGS.items():
                if tag_id in raw:
                    val = raw[tag_id]
                    exif[friendly] = _stringify(val)
        except Exception as exc:
            notes.append(f"EXIF read error: {exc}")

        caption_hint = _filename_caption_hint(path)

        return {
            "width": width,
            "height": height,
            "format": fmt,
            "exif": exif,
            "caption_hint": caption_hint,
            "notes": notes,
        }


def _stringify(value: Any) -> str:
    """Best-effort stringification of an EXIF value.

    EXIF values can be tuples, bytes, numbers, or strings; we coerce to
    a JSON-safe string form.
    """
    if value is None:
        return ""
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace").strip("\x00")
        except Exception:
            return value.decode("latin-1", errors="replace")
    if isinstance(value, tuple):
        return "/".join(str(x) for x in value)
    return str(value)


def _filename_caption_hint(path: Path) -> str:
    """Derive a caption hint from the filename stem.

    Returns the first matched keyword or the bare stem if none match.
    """
    stem = path.stem.lower()
    for kw in _CAPTION_KEYWORDS:
        if kw in stem:
            return kw
    return path.stem
