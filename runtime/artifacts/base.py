"""Artifact base class + provenance.

Every concrete Artifact type inherits from ``Artifact`` and declares:
    - ``artifact_type``: a stable string discriminator (e.g. "certificate")
    - ``fields``: the typed fields specific to that artifact kind

The base class provides:
    - ``provenance``: where this artifact came from (file hash + path)
    - ``serialize()`` / ``deserialize()``: JSON round-trip
    - ``confidence``: per ADR-0007, extracted facts are ``inferred`` until
      a user confirms; the Importer sets this, downstream Skills may
      upgrade it after user confirmation.

Dependency direction (user directive):
    runtime/artifacts/ imports NOTHING from skills/ or importers/.
    It is a leaf contract that both sides depend ON, not towards.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

@dataclass
class ArtifactProvenance:
    """Records where an Artifact came from.

    Importers populate this from the source file. Downstream consumers
    use it to cite sources in generated Markdown (ADR-0001 provenance).
    """

    source_path: str
    """Path to the original file (relative to vault root, forward slashes)."""

    sha256: str
    """SHA-256 of the original file bytes (dedup key per data-lifecycle.md)."""

    detected_type: str
    """The detected_type string from the import-log enum (13 types)."""

    extractor: str
    """Name of the extractor that produced this artifact (e.g. "pdf_text")."""

    extracted_at: str = ""
    """ISO 8601 timestamp of extraction. Auto-filled if empty."""

    byte_range: Optional[List[int]] = None
    """[start, end] byte offsets within the source, if applicable."""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not self.extracted_at:
            d["extracted_at"] = datetime.now(timezone.utc).isoformat()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ArtifactProvenance":
        return cls(
            source_path=d["source_path"],
            sha256=d["sha256"],
            detected_type=d["detected_type"],
            extractor=d["extractor"],
            extracted_at=d.get("extracted_at", ""),
            byte_range=d.get("byte_range"),
        )

    @staticmethod
    def hash_file(path: Path) -> str:
        """Compute SHA-256 of a file's bytes."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()


# ---------------------------------------------------------------------------
# Artifact base
# ---------------------------------------------------------------------------

@dataclass
class Artifact:
    """Base class for all Artifact types.

    Subclasses set ``artifact_type`` and add typed fields. The base
    provides provenance, confidence, and JSON serialization.

    Confidence follows ADR-0007:
        - "inferred": extractor derived this (Importers default here)
        - "confirmed": user verified (downstream Skills upgrade)
        - "missing": field could not be determined
    """

    artifact_type: str = "base"
    """Stable discriminator; subclasses override."""

    provenance: ArtifactProvenance = field(default=None)
    """Source trace. Required for any real Artifact."""

    confidence: str = "inferred"
    """ADR-0007 confidence enum: confirmed | inferred | missing."""

    notes: List[str] = field(default_factory=list)
    """Free-form extractor notes (e.g. 'OCR low confidence on line 3')."""

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-safe dict."""
        d = asdict(self) if hasattr(self, "__dataclass_fields__") else {}
        # Always ensure these base keys are present
        d["artifact_type"] = self.artifact_type
        d["provenance"] = self.provenance.to_dict() if self.provenance else None
        d["confidence"] = self.confidence
        d["notes"] = self.notes
        return d

    def serialize(self) -> str:
        """Serialize to a JSON string."""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Artifact":
        """Deserialize from a dict. Subclasses override to restore fields."""
        prov = d.get("provenance")
        return cls(
            artifact_type=d.get("artifact_type", "base"),
            provenance=ArtifactProvenance.from_dict(prov) if prov else None,
            confidence=d.get("confidence", "inferred"),
            notes=d.get("notes", []),
        )

    @classmethod
    def deserialize(cls, raw: str) -> "Artifact":
        """Deserialize from a JSON string."""
        import json
        return cls.from_dict(json.loads(raw))

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def source_sha256(self) -> str:
        """The dedup key for this artifact's source file."""
        return self.provenance.sha256 if self.provenance else ""
