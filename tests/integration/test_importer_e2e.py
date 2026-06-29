"""E2E test for the Importer Runtime.

Proves the Importer Runtime works end-to-end for all 5 fixture types:

    fixture path → ImporterPipeline.run() → Artifact → serialize
                  → verify artifact_type + provenance.sha256 + key fields

This test runs the pipeline on real committed fixtures and verifies
the output artifacts have the right structure and provenance. It is
the acceptance test for Sprint 2.5.

Run:
    pytest tests/integration/test_importer_e2e.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.importer.pipeline import ImporterPipeline
from runtime.artifacts.types import (
    ProjectArtifact,
    ResearchPaperArtifact,
    ResumeArtifact,
    ImageArtifact,
)


# ---------------------------------------------------------------------------
# Fixture paths
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
SAMPLE_README = FIXTURES / "readme" / "sample-readme.md"
SAMPLE_PDF    = FIXTURES / "pdf"    / "sample-paper.pdf"
SAMPLE_DOCX   = FIXTURES / "docx"   / "sample-resume.docx"
SAMPLE_IMAGE  = FIXTURES / "image"  / "sample-award.jpg"
SAMPLE_GIT    = FIXTURES / "github" / "sample-repo"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestImporterE2E:
    """Run the full pipeline on each fixture and verify output."""

    def test_readme_e2e(self):
        pipe = ImporterPipeline()
        art = pipe.run(SAMPLE_README)

        # Type check
        assert isinstance(art, ProjectArtifact)
        assert art.artifact_type == "project"

        # Provenance
        assert art.provenance is not None
        assert len(art.provenance.sha256) == 64
        assert art.provenance.detected_type == "readme"
        assert art.provenance.extractor == "readme"

        # Key fields
        assert art.title == "Sample Project"
        assert "Python" in art.tech_stack
        assert "ROS2" in art.tech_stack

        # Serialize round-trip
        raw = art.serialize()
        parsed = json.loads(raw)
        assert parsed["artifact_type"] == "project"
        assert parsed["provenance"]["sha256"] == art.provenance.sha256
        assert parsed["title"] == "Sample Project"

    def test_pdf_e2e(self):
        pipe = ImporterPipeline()
        art = pipe.run(SAMPLE_PDF)

        # sample-paper.pdf has DOI → research_paper
        assert isinstance(art, ResearchPaperArtifact)
        assert art.artifact_type == "research_paper"

        # Provenance
        assert art.provenance is not None
        assert len(art.provenance.sha256) == 64
        assert art.provenance.detected_type == "pdf"
        # extractor is "pdf" (kind), not "pdf_text" (class name)
        assert art.provenance.extractor == "pdf"

        # Key fields
        assert art.doi == "10.1000/test"
        assert art.arxiv_id == "2401.0001"

        # Serialize round-trip
        raw = art.serialize()
        parsed = json.loads(raw)
        assert parsed["artifact_type"] == "research_paper"
        assert parsed["doi"] == "10.1000/test"

    def test_docx_e2e(self):
        pipe = ImporterPipeline()
        art = pipe.run(SAMPLE_DOCX)

        # sample-resume.docx has "Curriculum Vitae" → resume
        assert isinstance(art, ResumeArtifact)
        assert art.artifact_type == "resume"

        # Provenance
        assert art.provenance is not None
        assert len(art.provenance.sha256) == 64
        assert art.provenance.detected_type == "docx"
        assert art.provenance.extractor == "docx"

        # Key fields
        assert "Curriculum Vitae" in art.raw_text or "Experience" in art.raw_text

        # Serialize round-trip
        raw = art.serialize()
        parsed = json.loads(raw)
        assert parsed["artifact_type"] == "resume"

    def test_image_e2e(self):
        pipe = ImporterPipeline()
        art = pipe.run(SAMPLE_IMAGE)

        assert isinstance(art, ImageArtifact)
        assert art.artifact_type == "image"

        # Provenance
        assert art.provenance is not None
        assert len(art.provenance.sha256) == 64
        assert art.provenance.detected_type == "image"
        assert art.provenance.extractor == "image"

        # Key fields
        assert art.width == 100
        assert art.height == 100
        assert art.format == "JPEG"
        assert "DateTime" in art.exif
        assert art.caption_hint == "award"

        # Serialize round-trip
        raw = art.serialize()
        parsed = json.loads(raw)
        assert parsed["artifact_type"] == "image"
        assert parsed["width"] == 100
        assert parsed["caption_hint"] == "award"

    def test_git_repo_e2e(self):
        pipe = ImporterPipeline()
        art = pipe.run(SAMPLE_GIT)

        assert isinstance(art, ProjectArtifact)
        assert art.artifact_type == "project"

        # Provenance
        assert art.provenance is not None
        assert len(art.provenance.sha256) == 64
        assert art.provenance.detected_type == "git_repository"
        # Pipeline resolves git_repository → "git" kind
        assert art.provenance.extractor == "git"

        # Key fields
        assert art.commit_count >= 1  # generator added 1 commit
        # Should detect at least one language
        assert len(art.languages) > 0
        assert "Python" in art.languages or "Markdown" in art.languages

        # Serialize round-trip
        raw = art.serialize()
        parsed = json.loads(raw)
        assert parsed["artifact_type"] == "project"
        assert parsed["commit_count"] >= 1
