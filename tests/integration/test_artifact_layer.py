"""Sprint 2 acceptance test — Artifact Layer.

Contract for the Artifact layer (Sprint 2). The Importer (Sprint 2.5)
must produce Artifacts that pass these tests. Downstream Skills consume
Artifacts via this contract — they never see source files.

Verifies:
    1. Each of 6 artifact types round-trips through serialize/deserialize.
    2. Provenance carries source hash + path + extractor.
    3. Confidence defaults to "inferred" (ADR-0007).
    4. artifact_type discriminator is set correctly per type.
    5. ArtifactProvenance.hash_file computes a real SHA-256.
    6. Artifacts are JSON-serializable (no bytes, no datetime objects).
"""

import json
import tempfile
from pathlib import Path

import pytest

from runtime.artifacts import Artifact, ArtifactProvenance
from runtime.artifacts.types import (
    CertificateArtifact,
    CompetitionArtifact,
    ImageArtifact,
    ProjectArtifact,
    ResearchPaperArtifact,
    ResumeArtifact,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def provenance(tmp_path):
    """A provenance record pointing at a dummy source file."""
    src = tmp_path / "demo.pdf"
    src.write_bytes(b"%PDF-1.4 fake content for hashing")
    return ArtifactProvenance(
        source_path="inbox/demo.pdf",
        sha256=ArtifactProvenance.hash_file(src),
        detected_type="certificate",
        extractor="pdf_text",
    )


# ---------------------------------------------------------------------------
# 1. Round-trip per type
# ---------------------------------------------------------------------------

class TestArtifactRoundTrip:
    """Every artifact type must serialize → deserialize losslessly."""

    @pytest.mark.parametrize("artifact_cls,extra_fields", [
        (CertificateArtifact, {"title": "AWS Cert", "issuer": "Amazon",
                               "issue_date": "2024-03-01",
                               "certificate_id": "AWS-12345",
                               "recipient_name": "Zhang San"}),
        (ProjectArtifact, {"title": "PX4 UAV", "description": "Drone nav",
                           "tech_stack": ["Python", "ROS2"], "repo_url": "",
                           "languages": ["Python"], "readme_text": "# PX4",
                           "commit_count": 42}),
        (ResearchPaperArtifact, {"title": "Paper", "authors": ["A", "B"],
                                 "abstract": "Lorem", "doi": "10.1000/1",
                                 "arxiv_id": "2401.0001", "year": "2024",
                                 "venue": "ICRA"}),
        (CompetitionArtifact, {"competition_name": "RoboMaster",
                               "award": "Gold", "rank": "1",
                               "team_size": 8, "date": "2024-07-01",
                               "organization": "DJI"}),
        (ResumeArtifact, {"raw_text": "Zhang San\nExperience...",
                          "contact_name": "Zhang San",
                          "contact_email": "a@b.com",
                          "contact_phone": "13800000000",
                          "sections": ["Experience", "Education"]}),
        (ImageArtifact, {"width": 1920, "height": 1080, "format": "JPEG",
                         "exif": {"DateTime": "2024:01:01 12:00:00"},
                         "caption_hint": "award"}),
    ])
    def test_round_trip(self, provenance, artifact_cls, extra_fields):
        art = artifact_cls(provenance=provenance, **extra_fields)
        raw = art.serialize()
        # Must be valid JSON with no bytes/datetime
        parsed = json.loads(raw)
        restored = artifact_cls.from_dict(parsed)
        assert restored.artifact_type == art.artifact_type
        assert restored.provenance.sha256 == provenance.sha256
        for k, v in extra_fields.items():
            assert getattr(restored, k) == v, f"field {k} not preserved"


# ---------------------------------------------------------------------------
# 2. Provenance
# ---------------------------------------------------------------------------

class TestProvenance:
    def test_hash_file(self, tmp_path):
        f = tmp_path / "test.bin"
        f.write_bytes(b"hello world")
        h = ArtifactProvenance.hash_file(f)
        assert len(h) == 64  # SHA-256 hex
        assert h == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"

    def test_provenance_to_dict(self, provenance):
        d = provenance.to_dict()
        assert d["source_path"] == "inbox/demo.pdf"
        assert len(d["sha256"]) == 64
        assert d["detected_type"] == "certificate"
        assert d["extractor"] == "pdf_text"
        assert "extracted_at" in d and d["extracted_at"]

    def test_provenance_from_dict_round_trip(self, provenance):
        d = provenance.to_dict()
        restored = ArtifactProvenance.from_dict(d)
        assert restored.source_path == provenance.source_path
        assert restored.sha256 == provenance.sha256
        assert restored.detected_type == provenance.detected_type
        assert restored.extractor == provenance.extractor


# ---------------------------------------------------------------------------
# 3. Confidence
# ---------------------------------------------------------------------------

class TestConfidence:
    def test_default_confidence_is_inferred(self, provenance):
        art = CertificateArtifact(provenance=provenance)
        assert art.confidence == "inferred"

    def test_confidence_carried_through_serialization(self, provenance):
        art = CertificateArtifact(provenance=provenance, confidence="confirmed")
        restored = CertificateArtifact.from_dict(json.loads(art.serialize()))
        assert restored.confidence == "confirmed"


# ---------------------------------------------------------------------------
# 4. artifact_type discriminator
# ---------------------------------------------------------------------------

class TestArtifactType:
    @pytest.mark.parametrize("cls,expected_type", [
        (CertificateArtifact, "certificate"),
        (ProjectArtifact, "project"),
        (ResearchPaperArtifact, "research_paper"),
        (CompetitionArtifact, "competition"),
        (ResumeArtifact, "resume"),
        (ImageArtifact, "image"),
    ])
    def test_type_discriminator(self, provenance, cls, expected_type):
        art = cls(provenance=provenance)
        assert art.artifact_type == expected_type
        # Also present in serialized form
        d = json.loads(art.serialize())
        assert d["artifact_type"] == expected_type


# ---------------------------------------------------------------------------
# 5. JSON-serializable (no bytes / datetime)
# ---------------------------------------------------------------------------

class TestJSONSerializable:
    def test_no_bytes_in_output(self, provenance):
        art = ProjectArtifact(provenance=provenance, readme_text="x" * 500)
        raw = art.serialize()
        # If this succeeds, it's valid JSON with no bytes
        json.loads(raw)

    def test_no_datetime_objects(self, provenance):
        art = ResearchPaperArtifact(provenance=provenance)
        raw = art.serialize()
        # Re-parse and check all values are JSON-native
        d = json.loads(raw)
        assert isinstance(d["provenance"]["extracted_at"], str)
