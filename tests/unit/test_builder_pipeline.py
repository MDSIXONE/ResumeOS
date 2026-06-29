"""Unit tests for the BuilderPipeline."""
from __future__ import annotations

from pathlib import Path

import pytest

from runtime.builder.pipeline import BuilderPipeline
from runtime.artifacts.types import ProjectArtifact
from runtime.artifacts.base import ArtifactProvenance
from runtime.event_bus import EventBus
from runtime.knowledge_index import KnowledgeIndex
from runtime.knowledge.writer import MarkdownWriter


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def vault(tmp_path):
    v = tmp_path / "vault"
    (v / "career" / "projects").mkdir(parents=True)
    (v / ".library" / "index").mkdir(parents=True)
    return v


@pytest.fixture
def pipeline(vault):
    from runtime.builder.planner import Planner
    from runtime.builder.retriever import Retriever
    from runtime.builder.validator import Validator
    from runtime.builder.merger import Merger
    from adapters.llm.dummy import DummyLLMProvider

    bus = EventBus(events_log=vault / ".library" / "events.jsonl")
    idx = KnowledgeIndex(vault_root=vault)

    return BuilderPipeline(
        planner=Planner(),
        retriever=Retriever(knowledge_index=idx, writer=MarkdownWriter()),
        llm=DummyLLMProvider(),
        validator=Validator(schemas_root=REPO_ROOT / "schemas"),
        merger=Merger(),
        writer=MarkdownWriter(),
        event_bus=bus,
        knowledge_index=idx,
    )


@pytest.fixture
def artifact():
    return ProjectArtifact(
        artifact_type="project",
        title="Test Project",
        description="A test project",
        tech_stack=["Python", "PyTorch"],
        repo_url="https://github.com/test/project",
        languages=["Python"],
        readme_text="# Test Project\nA test.",
        commit_count=10,
        provenance=ArtifactProvenance(
            source_path="test/readme.md",
            sha256="abc123def456",
            detected_type="readme",
            extractor="readme_parser",
        ),
    )


class TestBuilderPipeline:
    """Test the BuilderPipeline class."""

    def test_pipeline_success(self, pipeline, vault, artifact):
        result = pipeline.run(artifact, vault)
        assert result.success is True
        assert result.knowledge_object is not None
        assert result.written_path is not None
        assert result.written_path.exists()

    def test_pipeline_publishes_events(self, pipeline, vault, artifact):
        result = pipeline.run(artifact, vault)
        assert result.success is True
        assert "KnowledgeDraftCreated" in result.events_published
        assert "KnowledgeCommitted" in result.events_published

    def test_pipeline_creates_draft_before_knowledge(self, pipeline, vault, artifact):
        """Principle 3: Draft is produced before KnowledgeObject."""
        result = pipeline.run(artifact, vault)
        assert result.success is True
        assert result.draft is not None
        assert result.draft.raw_output != ""
        assert result.draft.is_valid

    def test_pipeline_updates_knowledge_index(self, pipeline, vault, artifact):
        result = pipeline.run(artifact, vault)
        assert result.success is True

        idx = KnowledgeIndex(vault_root=vault)
        projects = idx.query(entity_type="project")
        assert len(projects) >= 1


class TestBuilderPipelineEdgeCases:
    """Edge cases and error handling."""

    def test_pipeline_deterministic_output(self, pipeline, vault, artifact):
        """Same artifact -> same fields on re-run (golden property)."""
        r1 = pipeline.run(artifact, vault)
        r1.written_path.unlink()
        r2 = pipeline.run(artifact, vault)
        assert r1.knowledge_object.fields["title"] == r2.knowledge_object.fields["title"]
        assert r1.knowledge_object.fields["status"] == r2.knowledge_object.fields["status"]

    def test_pipeline_preserves_existing_on_conflict(self, pipeline, vault, artifact):
        # Pre-create an existing entity with conflicting role
        existing_path = vault / "career" / "projects" / "test-project.md"
        existing_path.write_text(
            "---\nid: test-project\ntitle: Test Project\nrole: Team Lead\n"
            "status: completed\nsources:\n  - kind: readme\n    ref: test.md\n"
            "---\n# Test\n",
            encoding="utf-8",
        )

        result = pipeline.run(artifact, vault)
        assert result.success is True
        assert len(result.conflicts) > 0

        # Read the written file and check role is preserved
        text = result.written_path.read_text(encoding="utf-8")
        import yaml
        fm_start = text.find("---\n") + 4
        fm_end = text.find("\n---\n", fm_start)
        fm = yaml.safe_load(text[fm_start:fm_end])
        assert fm["role"] == "Team Lead"  # Existing preserved
