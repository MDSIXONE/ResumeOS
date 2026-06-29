"""Six concrete Artifact types produced by Importers.

Each type carries typed fields specific to its kind, plus the shared
provenance/confidence/notes from the base class. Downstream Skills
dispatch on ``artifact_type`` to consume the right fields.

Type set aligns with the 13 detected_type values in data-lifecycle.md
and the knowledge-extraction table in inbox-workflow.md. The 6 here
are the high-value types Importers produce in Sprint 2.5; the
remaining (transcript/blog/video/presentation/git_repository) extend
the same base in later sprints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from runtime.artifacts.base import Artifact, ArtifactProvenance


# ---------------------------------------------------------------------------
# Certificate
# ---------------------------------------------------------------------------

@dataclass
class CertificateArtifact(Artifact):
    """A certificate (e.g. course completion, certification)."""

    artifact_type: str = "certificate"
    title: str = ""
    issuer: str = ""
    issue_date: str = ""
    """ISO 8601 date if extractable, else empty (confidence: missing)."""
    certificate_id: str = ""
    recipient_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update(title=self.title, issuer=self.issuer, issue_date=self.issue_date,
                 certificate_id=self.certificate_id, recipient_name=self.recipient_name)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CertificateArtifact":
        base = super().from_dict(d)
        return cls(artifact_type=base.artifact_type, provenance=base.provenance,
                   confidence=base.confidence, notes=base.notes,
                   title=d.get("title", ""), issuer=d.get("issuer", ""),
                   issue_date=d.get("issue_date", ""),
                   certificate_id=d.get("certificate_id", ""),
                   recipient_name=d.get("recipient_name", ""))


# ---------------------------------------------------------------------------
# Project (from README, GitHub, ZIP)
# ---------------------------------------------------------------------------

@dataclass
class ProjectArtifact(Artifact):
    """A project extracted from a README, git repo, or archive."""

    artifact_type: str = "project"
    title: str = ""
    description: str = ""
    tech_stack: List[str] = field(default_factory=list)
    """Technologies detected (from README headings, package files, etc.)."""
    repo_url: str = ""
    """Git remote URL if a .git dir was present."""
    languages: List[str] = field(default_factory=list)
    """Programming languages detected."""
    readme_text: str = ""
    """Raw README text for downstream LLM processing (Importer does NOT LLM)."""
    commit_count: int = 0
    """Number of commits if extracted from git log."""

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update(title=self.title, description=self.description,
                 tech_stack=self.tech_stack, repo_url=self.repo_url,
                 languages=self.languages, readme_text=self.readme_text,
                 commit_count=self.commit_count)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProjectArtifact":
        base = super().from_dict(d)
        return cls(artifact_type=base.artifact_type, provenance=base.provenance,
                   confidence=base.confidence, notes=base.notes,
                   title=d.get("title", ""), description=d.get("description", ""),
                   tech_stack=d.get("tech_stack", []), repo_url=d.get("repo_url", ""),
                   languages=d.get("languages", []),
                   readme_text=d.get("readme_text", ""),
                   commit_count=d.get("commit_count", 0))


# ---------------------------------------------------------------------------
# Research Paper
# ---------------------------------------------------------------------------

@dataclass
class ResearchPaperArtifact(Artifact):
    """An academic paper (PDF with DOI/arXiv/abstract)."""

    artifact_type: str = "research_paper"
    title: str = ""
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    doi: str = ""
    arxiv_id: str = ""
    year: str = ""
    venue: str = ""
    """Journal/conference name if detectable from the PDF."""

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update(title=self.title, authors=self.authors, abstract=self.abstract,
                 doi=self.doi, arxiv_id=self.arxiv_id, year=self.year, venue=self.venue)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResearchPaperArtifact":
        base = super().from_dict(d)
        return cls(artifact_type=base.artifact_type, provenance=base.provenance,
                   confidence=base.confidence, notes=base.notes,
                   title=d.get("title", ""), authors=d.get("authors", []),
                   abstract=d.get("abstract", ""), doi=d.get("doi", ""),
                   arxiv_id=d.get("arxiv_id", ""), year=d.get("year", ""),
                   venue=d.get("venue", ""))


# ---------------------------------------------------------------------------
# Competition / Award
# ---------------------------------------------------------------------------

@dataclass
class CompetitionArtifact(Artifact):
    """A competition or award (certificate + result)."""

    artifact_type: str = "competition"
    competition_name: str = ""
    award: str = ""
    """e.g. 'Gold', 'First Prize', 'Participant'."""
    rank: str = ""
    """Numeric or descriptive rank if stated."""
    team_size: int = 0
    date: str = ""
    """ISO 8601 if extractable."""
    organization: str = ""
    """Organizing body."""

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update(competition_name=self.competition_name, award=self.award,
                 rank=self.rank, team_size=self.team_size, date=self.date,
                 organization=self.organization)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CompetitionArtifact":
        base = super().from_dict(d)
        return cls(artifact_type=base.artifact_type, provenance=base.provenance,
                   confidence=base.confidence, notes=base.notes,
                   competition_name=d.get("competition_name", ""),
                   award=d.get("award", ""), rank=d.get("rank", ""),
                   team_size=d.get("team_size", 0), date=d.get("date", ""),
                   organization=d.get("organization", ""))


# ---------------------------------------------------------------------------
# Resume
# ---------------------------------------------------------------------------

@dataclass
class ResumeArtifact(Artifact):
    """A previously-written resume (PDF/DOCX) imported for re-use."""

    artifact_type: str = "resume"
    raw_text: str = ""
    """Full text extract for downstream parsing (Importer does NOT LLM)."""
    contact_name: str = ""
    contact_email: str = ""
    contact_phone: str = ""
    sections: List[str] = field(default_factory=list)
    """Detected section headings (e.g. 'Experience', 'Education')."""

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update(raw_text=self.raw_text, contact_name=self.contact_name,
                 contact_email=self.contact_email, contact_phone=self.contact_phone,
                 sections=self.sections)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResumeArtifact":
        base = super().from_dict(d)
        return cls(artifact_type=base.artifact_type, provenance=base.provenance,
                   confidence=base.confidence, notes=base.notes,
                   raw_text=d.get("raw_text", ""),
                   contact_name=d.get("contact_name", ""),
                   contact_email=d.get("contact_email", ""),
                   contact_phone=d.get("contact_phone", ""),
                   sections=d.get("sections", []))


# ---------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------

@dataclass
class ImageArtifact(Artifact):
    """An image (screenshot, photo, diagram) — metadata only.

    The Importer extracts EXIF/dimensions but does NOT claim what the
    image depicts (that would require vision AI, which is a plugin,
    not the Importer's deterministic job).
    """

    artifact_type: str = "image"
    width: int = 0
    height: int = 0
    format: str = ""
    """e.g. 'JPEG', 'PNG'."""
    exif: Dict[str, str] = field(default_factory=dict)
    """Selected EXIF tags (camera, date, GPS if present)."""
    caption_hint: str = ""
    """Filename-derived hint only (e.g. 'award' from 'award.jpg')."""

    def to_dict(self) -> Dict[str, Any]:
        d = super().to_dict()
        d.update(width=self.width, height=self.height, format=self.format,
                 exif=self.exif, caption_hint=self.caption_hint)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ImageArtifact":
        base = super().from_dict(d)
        return cls(artifact_type=base.artifact_type, provenance=base.provenance,
                   confidence=base.confidence, notes=base.notes,
                   width=d.get("width", 0), height=d.get("height", 0),
                   format=d.get("format", ""), exif=d.get("exif", {}),
                   caption_hint=d.get("caption_hint", ""))
