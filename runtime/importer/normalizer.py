"""Stage 3 of the Importer pipeline: Normalizer.

The Normalizer turns a ``(DetectionResult, raw_fields, provenance)``
tuple into a concrete :class:`Artifact` subclass.

For the five extractors shipped in Sprint 2.5 we have a 1:1 mapping
from ``detected_type`` → Artifact class, except for PDF/DOCX — those
are MIME-level results (``pdf``, ``docx``) and need a content-scout
pass to pick the semantic type. The content scout is regex-based
(rule-based, zero-AI):

    text contains "DOI" or "arXiv"         → research_paper
    text contains "Curriculum Vitae" OR
        (contains "Experience" AND "Education") → resume
    text contains "Certificate" or "Certified"   → certificate
    text contains "Award" or "Prize"
        or "First Place" or "First Prize"        → competition
    (default)                                    → resume

The default fallback for an unknown PDF is ``resume`` — this is the
most common resume-import use case and avoids a hard error for users
who drop an unclassified PDF. If the rules fire ambiguously (e.g.
both DOI and Curriculum Vitae appear), we pick the rule with the
highest specificity, in the order listed above (DOI/arXiv > CV >
Certificate > Award).

ADR-0007: every artifact leaves confidence = "inferred" — downstream
Skills upgrade it after user confirmation.

Dependency direction: this module imports only runtime.artifacts
(leaf) and runtime.importer.detector (stage 1). It does NOT import
skills/ and it does NOT write files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional, Type

from runtime.artifacts.base import Artifact, ArtifactProvenance
from runtime.artifacts.types import (
    CertificateArtifact,
    CompetitionArtifact,
    ImageArtifact,
    ProjectArtifact,
    ResearchPaperArtifact,
    ResumeArtifact,
)
from runtime.importer.detector import DetectionResult


# Case-insensitive regex helpers for the content-scout rules.
_RE_DOI = re.compile(r"10\.\d{4,}/[^\s,]+|arXiv:\s*[^\s,]+|#", re.IGNORECASE)
_RE_ARXIV_ID = re.compile(r"\d{4}\.\d{4,}(?:v\d+)?")
_RE_CV = re.compile(r"curriculum\s+vitae|resume", re.IGNORECASE)
_RE_CERT = re.compile(r"\bcertificate\b|\bcertified\b", re.IGNORECASE)
_RE_AWARD = re.compile(
    r"\b(first\s+place|first\s+prize|gold|silver|bronze|award|prize|winner)\b",
    re.IGNORECASE,
)
_RE_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_RE_PHONE = re.compile(r"\+?\d[\d\s\-.()\u200b-]{7,}\d")


class Normalizer:
    """Build the correct Artifact from detection + extracted fields.

    Parameters
    ----------
    provenance:
        A pre-built :class:`ArtifactProvenance`. The Normalizer does
        NOT compute hashes — those are the Pipeline's job (it sees the
        original path and can hash it once).
    """

    def __init__(self, provenance: ArtifactProvenance):
        self.provenance = provenance

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def normalize(
        self,
        detection: DetectionResult,
        fields: Dict[str, Any],
    ) -> Artifact:
        """Build the right Artifact subclass for *detection* + *fields*."""
        dtype = detection.detected_type
        notes = list(fields.get("notes", []) or [])

        # --- Semantic types with a 1:1 extractor mapping ---------------
        if dtype == "readme":
            return self._readme_to_project(fields, notes)
        if dtype == "git_repository":
            return self._git_to_project(fields, notes)
        if dtype == "image":
            return ImageArtifact(
                provenance=self.provenance,
                width=int(fields.get("width", 0) or 0),
                height=int(fields.get("height", 0) or 0),
                format=str(fields.get("format", "")),
                exif=dict(fields.get("exif") or {}),
                caption_hint=str(fields.get("caption_hint", "")),
                notes=notes,
            )

        # --- PDF / DOCX need a content-scout pass ---------------------
        if dtype in ("pdf", "docx"):
            text = str(fields.get("text", ""))
            notes_note = self._pdf_semantic_note(detection, dtype)
            if notes_note:
                notes.append(notes_note)
            sem_type = self._classify_semantic_text(text, default="resume")
            return self._build_semantic_pdf_docx(
                sem_type, fields, notes,
            )

        # --- Fallback: unknown → ResumeArtifact with a warning --------
        notes.append(
            f"Normalizer: no mapping for detected_type={dtype!r}, "
            "falling back to resume"
        )
        return ResumeArtifact(
            provenance=self.provenance,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pdf_semantic_note(detection: DetectionResult, mime: str) -> Optional[str]:
        return f"MIME-level first pass ({mime}); semantic type inferred from text"

    @staticmethod
    def _classify_semantic_text(text: str, *, default: str = "resume") -> str:
        """Rule-based content scout.

        Order of precedence (most specific first):
        1. DOI/arXiv → research_paper
        2. Curriculum Vitae / Resume → resume
        3. Certificate / Certified → certificate
        4. Award / Prize / First Place → competition
        """
        if not text:
            return default
        if _RE_DOI.search(text) or _RE_ARXIV_ID.search(text):
            return "research_paper"
        if _RE_CV.search(text):
            return "resume"
        if _RE_CERT.search(text):
            return "certificate"
        if _RE_AWARD.search(text):
            return "competition"
        return default

    def _build_semantic_pdf_docx(
        self, sem_type: str, fields: Dict[str, Any], notes: list,
    ) -> Artifact:
        text = str(fields.get("text", ""))

        if sem_type == "research_paper":
            # Extract DOI: look for "10.4 digits/something" pattern first
            doi = ""
            m = re.search(r'10\.\d{4,}/[^\s,]+', text)
            if m:
                doi = m.group(0).rstrip('.')
            else:
                # Fall back to extracting from "DOI: xxx" pattern
                m = re.search(r'DOI:\s*([10\.\d{4,}/]+)', text, re.IGNORECASE)
                if m:
                    doi = m.group(1).rstrip('.')
            
            # Extract arXiv ID
            arxiv_id = ""
            m = re.search(r'arXiv:\s*(\d{4}\.\d{4,}(?:v\d+)?)', text, re.IGNORECASE)
            if m:
                arxiv_id = m.group(1)
            else:
                arxiv_id = _extract_first(_RE_ARXIV_ID, text)
            
            return ResearchPaperArtifact(
                provenance=self.provenance,
                abstract="",
                doi=doi,
                arxiv_id=arxiv_id,
                notes=notes,
            )
        if sem_type == "certificate":
            return CertificateArtifact(
                provenance=self.provenance,
                notes=notes,
            )
        if sem_type == "competition":
            return CompetitionArtifact(
                provenance=self.provenance,
                notes=notes,
            )
        # default: resume
        email = ""
        m = _RE_EMAIL.search(text)
        if m:
            email = m.group(0)
        phone = ""
        m = _RE_PHONE.search(text)
        if m:
            phone = m.group(0).strip()
        return ResumeArtifact(
            provenance=self.provenance,
            raw_text=text,
            contact_email=email,
            contact_phone=phone,
            notes=notes,
        )

    def _readme_to_project(self, fields: Dict[str, Any], notes: list) -> ProjectArtifact:
        return ProjectArtifact(
            provenance=self.provenance,
            title=str(fields.get("title", "")),
            description=str(fields.get("description", "")),
            tech_stack=list(fields.get("tech_stack") or []),
            readme_text=str(fields.get("readme_text", "")),
            notes=notes,
        )

    def _git_to_project(self, fields: Dict[str, Any], notes: list) -> ProjectArtifact:
        return ProjectArtifact(
            provenance=self.provenance,
            repo_url=str(fields.get("repo_url", "")),
            languages=list(fields.get("languages") or []),
            commit_count=int(fields.get("commit_count", 0) or 0),
            notes=notes,
        )


def _extract_first(pattern: re.Pattern, text: str) -> str:
    m = pattern.search(text)
    return m.group(0) if m else ""
