"""Unit tests for each Importer Runtime stage.

Covers the five extractors shipped in Sprint 2.5 (PDF, DOCX, README,
Git, Image), the MimeDetector first pass, the Normalizer's semantic
type classification, and the pipeline end-to-end orchestration.

All tests use committed binary/text fixtures in ``tests/fixtures/``.
Run:
    pytest tests/unit/test_importer.py -v
"""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.importer.detector import MimeDetector, DetectionResult
from runtime.importer.extractors.pdf_text import PDFTextExtractor
from runtime.importer.extractors.docx_text import DOCXTextExtractor
from runtime.importer.extractors.readme_parser import READMEExtractor
from runtime.importer.extractors.git_log import GitExtractor
from runtime.importer.extractors.image_exif import ImageExtractor
from runtime.importer.normalizer import Normalizer
from runtime.importer.pipeline import ImporterPipeline
from runtime.importer.registry import ImporterRegistry
from runtime.artifacts.base import ArtifactProvenance
from runtime.artifacts.types import (
    ProjectArtifact,
    ResearchPaperArtifact,
    ResumeArtifact,
)


# ---------------------------------------------------------------------------
# Fixture paths
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
SAMPLE_README  = FIXTURES / "readme"  / "sample-readme.md"
SAMPLE_PDF     = FIXTURES / "pdf"     / "sample-paper.pdf"
SAMPLE_DOCX    = FIXTURES / "docx"    / "sample-resume.docx"
SAMPLE_IMAGE   = FIXTURES / "image"   / "sample-award.jpg"
SAMPLE_GIT     = FIXTURES / "github"  / "sample-repo"


# ---------------------------------------------------------------------------
# 1. MimeDetector
# ---------------------------------------------------------------------------

class TestMimeDetector:
    detector = MimeDetector()

    def test_pdf_extension(self, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4 fake")
        r = self.detector.detect(f)
        assert r.detected_type == "pdf"
        assert r.confidence == 0.80

    def test_docx_extension(self, tmp_path):
        f = tmp_path / "cv.docx"
        f.write_bytes(b"PK\x03\x04fake")
        r = self.detector.detect(f)
        assert r.detected_type == "docx"

    def test_jpg_extension(self, tmp_path):
        f = tmp_path / "award.jpg"
        r = self.detector.detect(f)
        assert r.detected_type == "image"

    def test_readme_md_filename(self, tmp_path):
        f = tmp_path / "README.md"
        r = self.detector.detect(f)
        assert r.detected_type == "readme"
        assert r.confidence == 0.90

    def test_readme_md_case_insensitive(self, tmp_path):
        f = tmp_path / "readme.md"
        r = self.detector.detect(f)
        assert r.detected_type == "readme"

    def test_git_directory(self, tmp_path):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        (repo / ".git").mkdir()
        r = self.detector.detect(repo)
        assert r.detected_type == "git_repository"
        assert r.confidence == 0.95
        assert any(".git directory present" in s for s in r.signals)

    def test_unknown_extension(self, tmp_path):
        f = tmp_path / "weird.xyz"
        r = self.detector.detect(f)
        assert r.detected_type == "unknown"
        assert r.confidence == 0.0


# ---------------------------------------------------------------------------
# 2. PDFTextExtractor
# ---------------------------------------------------------------------------

class TestPDFTextExtractor:
    def test_extracts_text_from_fixture(self):
        ext = PDFTextExtractor()
        detection = DetectionResult("pdf", 0.8, ["extension=.pdf"])
        r = ext.extract(SAMPLE_PDF, detection)
        # Should extract text from our hand-crafted PDF
        assert "Sample Research Paper" in r["text"]
        assert "DOI: 10.1000/test" in r["text"]
        assert r["page_count"] == 1
        assert isinstance(r["notes"], list)


# ---------------------------------------------------------------------------
# 3. DOCXTextExtractor
# ---------------------------------------------------------------------------

class TestDOCXTextExtractor:
    def test_extracts_headings_from_fixture(self):
        ext = DOCXTextExtractor()
        detection = DetectionResult("docx", 0.8, ["extension=.docx"])
        r = ext.extract(SAMPLE_DOCX, detection)
        # Our generator added H1 + H2 headings
        assert "Curriculum Vitae" in r["headings"]
        assert "Experience" in r["headings"]
        assert "Education" in r["headings"]
        assert r["paragraph_count"] > 0


# ---------------------------------------------------------------------------
# 4. READMEExtractor
# ---------------------------------------------------------------------------

class TestREADMEExtractor:
    def test_extracts_title_and_tech_stack(self):
        ext = READMEExtractor()
        detection = DetectionResult("readme", 0.9, [
            "filename=readme.md",
        ])
        r = ext.extract(SAMPLE_README, detection)
        assert r["title"] == "Sample Project"
        assert "Python" in r["tech_stack"]
        assert "ROS2" in r["tech_stack"]
        assert "CMake" in r["tech_stack"]
        assert r["readme_text"].startswith("# Sample Project")


# ---------------------------------------------------------------------------
# 5. GitExtractor
# ---------------------------------------------------------------------------

class TestGitExtractor:
    def test_extracts_commit_count(self):
        ext = GitExtractor()
        detection = DetectionResult(
            "git_repository", 0.95, [".git directory present"]
        )
        r = ext.extract(SAMPLE_GIT, detection)
        assert r["commit_count"] >= 1  # generator added 1 commit
        assert isinstance(r["languages"], list)
        # Should detect Python + Markdown
        assert "Python" in r["languages"] or "Markdown" in r["languages"]

    def test_graceful_when_not_repo(self, tmp_path):
        ext = GitExtractor()
        detection = DetectionResult("git_repository", 0.9, [])
        # Pass a non-git directory — should not raise
        r = ext.extract(tmp_path, detection)
        assert r["commit_count"] >= 0
        assert isinstance(r["notes"], list)


# ---------------------------------------------------------------------------
# 6. ImageExtractor
# ---------------------------------------------------------------------------

class TestImageExtractor:
    def test_extracts_dimensions(self):
        ext = ImageExtractor()
        detection = DetectionResult("image", 0.8, ["extension=.jpg"])
        r = ext.extract(SAMPLE_IMAGE, detection)
        # Our generator made a 100x100 JPEG
        assert r["width"] == 100
        assert r["height"] == 100
        assert r["format"] == "JPEG"
        assert "DateTime" in r["exif"]
        assert r["exif"]["DateTime"] == "2024:01:01 12:00:00"
        assert r["caption_hint"] == "award"


# ---------------------------------------------------------------------------
# 7. Normalizer
# ---------------------------------------------------------------------------

class TestNormalizer:
    def _mk_prov(self) -> ArtifactProvenance:
        return ArtifactProvenance(
            source_path="test",
            sha256="0" * 64,
            detected_type="pdf",
            extractor="pdf_text",
        )

    def test_pdf_with_doi_becomes_research_paper(self):
        prov = self._mk_prov()
        norm = Normalizer(prov)
        detection = DetectionResult("pdf", 0.8, [])
        fields = {
            "text": "Lorem ipsum. DOI: 10.1000/test. arXiv: 2401.0001",
            "page_count": 3, "metadata": {}, "notes": [],
        }
        art = norm.normalize(detection, fields)
        assert isinstance(art, ResearchPaperArtifact)
        assert art.artifact_type == "research_paper"
        assert art.doi == "10.1000/test"
        assert art.arxiv_id == "2401.0001"

    def test_pdf_with_cv_becomes_resume(self):
        prov = self._mk_prov()
        norm = Normalizer(prov)
        detection = DetectionResult("pdf", 0.8, [])
        fields = {
            "text": "Curriculum Vitae\n\nName: Jane Doe\nExperience: ...",
            "page_count": 1, "metadata": {}, "notes": [],
        }
        art = norm.normalize(detection, fields)
        assert isinstance(art, ResumeArtifact)
        assert art.artifact_type == "resume"

    def test_readme_becomes_project(self):
        prov = self._mk_prov()
        norm = Normalizer(prov)
        detection = DetectionResult("readme", 0.9, [])
        fields = {
            "title": "My Repo", "description": "A test project",
            "tech_stack": ["Python", "Docker"],
            "readme_text": "# My Repo\n\nA test project.",
            "notes": [],
        }
        art = norm.normalize(detection, fields)
        assert isinstance(art, ProjectArtifact)
        assert art.artifact_type == "project"
        assert art.title == "My Repo"
        assert "Python" in art.tech_stack

    def test_git_repo_becomes_project(self):
        prov = self._mk_prov()
        norm = Normalizer(prov)
        detection = DetectionResult("git_repository", 0.95, [])
        fields = {
            "commit_count": 5,
            "repo_url": "https://github.com/foo/bar",
            "languages": ["Python", "Rust"],
            "notes": [],
        }
        art = norm.normalize(detection, fields)
        assert isinstance(art, ProjectArtifact)
        assert art.commit_count == 5
        assert art.repo_url == "https://github.com/foo/bar"

    def test_unknown_pdf_defaults_to_resume(self):
        prov = self._mk_prov()
        norm = Normalizer(prov)
        detection = DetectionResult("pdf", 0.8, [])
        fields = {
            "text": "Some generic text with no keyword signals whatsoever.",
            "page_count": 1, "metadata": {}, "notes": [],
        }
        art = norm.normalize(detection, fields)
        assert isinstance(art, ResumeArtifact)
        assert art.artifact_type == "resume"


# ---------------------------------------------------------------------------
# 8. Pipeline (end-to-end per fixture)
# ---------------------------------------------------------------------------

class TestPipeline:
    def test_pipeline_on_readme(self):
        pipe = ImporterPipeline()
        art = pipe.run(SAMPLE_README)
        assert isinstance(art, ProjectArtifact)
        assert art.artifact_type == "project"
        assert art.title == "Sample Project"

    def test_pipeline_on_pdf(self):
        pipe = ImporterPipeline()
        art = pipe.run(SAMPLE_PDF)
        # sample-paper.pdf has DOI → research_paper
        assert isinstance(art, ResearchPaperArtifact)
        assert art.artifact_type == "research_paper"

    def test_pipeline_on_docx(self):
        pipe = ImporterPipeline()
        art = pipe.run(SAMPLE_DOCX)
        # sample-resume.docx has "Curriculum Vitae" → resume
        assert isinstance(art, ResumeArtifact)
        assert art.artifact_type == "resume"

    def test_pipeline_on_image(self):
        pipe = ImporterPipeline()
        art = pipe.run(SAMPLE_IMAGE)
        from runtime.artifacts.types import ImageArtifact
        assert isinstance(art, ImageArtifact)
        assert art.width == 100
        assert art.height == 100
        assert art.caption_hint == "award"

    def test_pipeline_on_git_repo(self):
        pipe = ImporterPipeline()
        art = pipe.run(SAMPLE_GIT)
        assert isinstance(art, ProjectArtifact)
        assert art.commit_count >= 1

    def test_pipeline_unknown_file_raises(self, tmp_path):
        f = tmp_path / "weird.xyz"
        f.write_text("garbage")
        pipe = ImporterPipeline()
        with pytest.raises(ImportError, match="unsupported file type"):
            pipe.run(f)


# ---------------------------------------------------------------------------
# 9. Registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_register_get_extractor(self):
        from runtime.importer.extractor import Extractor

        reg = ImporterRegistry()
        assert reg.has("pdf")
        ext = reg.get_extractor("pdf")
        assert isinstance(ext, PDFTextExtractor)

    def test_get_extractor_missing_kind(self):
        reg = ImporterRegistry()
        with pytest.raises(KeyError, match="no extractor"):
            reg.get_extractor("pptx")

    def test_custom_register(self):
        from runtime.importer.extractor import Extractor

        class DummyExtractor(Extractor):
            def extract(self, path, detection):
                return {"notes": []}

        reg = ImporterRegistry()
        reg.register("pptx", DummyExtractor())
        ext = reg.get_extractor("pptx")
        assert isinstance(ext, DummyExtractor)

    def test_kind_for_path_pdf(self, tmp_path):
        reg = ImporterRegistry()
        p = tmp_path / "doc.pdf"
        assert reg.kind_for_path(p) == "pdf"

    def test_kind_for_path_readme(self, tmp_path):
        reg = ImporterRegistry()
        p = tmp_path / "README.md"
        assert reg.kind_for_path(p) == "readme"

    def test_kind_for_path_git(self, tmp_path):
        reg = ImporterRegistry()
        p = tmp_path / "myrepo"
        p.mkdir()
        (p / ".git").mkdir()
        assert reg.kind_for_path(p) == "git"

    def test_kind_for_path_unknown_raises(self, tmp_path):
        reg = ImporterRegistry()
        p = tmp_path / "xyz.unknown"
        with pytest.raises(KeyError, match="no kind mapping"):
            reg.kind_for_path(p)
