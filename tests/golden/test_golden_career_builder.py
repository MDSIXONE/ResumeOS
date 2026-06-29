"""Golden tests for the Career Builder pipeline.

Proves the pipeline is DETERMINISTIC with a fixed LLM provider (DummyLLMProvider).
Same artifact → same KnowledgeObject structure, every time.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from adapters.llm.dummy import DummyLLMProvider
from runtime.artifacts.types import ProjectArtifact
from runtime.builder.merger import Merger
from runtime.builder.planner import Planner
from runtime.builder.pipeline import BuilderPipeline
from runtime.builder.retriever import Retriever
from runtime.builder.validator import Validator
from runtime.event_bus import EventBus
from runtime.knowledge.writer import MarkdownWriter
from runtime.knowledge_index import KnowledgeIndex

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_ROOT = REPO_ROOT / "schemas"


@pytest.fixture
def vault(tmp_path):
    v = tmp_path / "vault"
    (v / "career" / "projects").mkdir(parents=True)
    (v / ".library" / "index").mkdir(parents=True)
    return v


@pytest.fixture
def pipeline(vault):
    bus = EventBus(events_log=vault / ".library" / "events.jsonl")
    idx = KnowledgeIndex(vault_root=vault)

    return BuilderPipeline(
        planner=Planner(),
        retriever=Retriever(knowledge_index=idx, writer=MarkdownWriter()),
        llm=DummyLLMProvider(),
        validator=Validator(schemas_root=SCHEMAS_ROOT),
        merger=Merger(),
        writer=MarkdownWriter(),
        event_bus=bus,
        knowledge_index=idx,
    )


@pytest.fixture
def artifact():
    """Load the golden test artifact."""
    input_path = REPO_ROOT / "tests" / "golden" / "input" / "project_artifact.json"
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ProjectArtifact.from_dict(data)


class TestGoldenCareerBuilder:
    """Golden tests for the Career Builder pipeline."""

    def test_golden_pipeline_success(self, pipeline, vault, artifact):
        """Pipeline runs successfully with golden artifact."""
        result = pipeline.run(artifact, vault)
        assert result.success is True

    def test_golden_entity_type(self, pipeline, vault, artifact):
        """Entity type is project."""
        result = pipeline.run(artifact, vault)
        assert result.knowledge_object.entity_type == "project"

    def test_golden_title(self, pipeline, vault, artifact):
        """Title matches expected."""
        result = pipeline.run(artifact, vault)
        assert result.knowledge_object.fields["title"] == "YOLO Detection"

    def test_golden_status(self, pipeline, vault, artifact):
        """Status is completed."""
        result = pipeline.run(artifact, vault)
        assert result.knowledge_object.fields["status"] == "completed"

    def test_golden_role(self, pipeline, vault, artifact):
        """Role is Developer."""
        result = pipeline.run(artifact, vault)
        assert result.knowledge_object.fields["role"] == "Developer"

    def test_golden_sources(self, pipeline, vault, artifact):
        """Sources array is present and non-empty."""
        result = pipeline.run(artifact, vault)
        ko = result.knowledge_object
        assert "sources" in ko.fields
        assert len(ko.fields["sources"]) >= 1

    def test_golden_markdown_structure(self, pipeline, vault, artifact):
        """Written markdown has correct frontmatter structure."""
        result = pipeline.run(artifact, vault)
        text = result.written_path.read_text(encoding="utf-8")
        
        # Split frontmatter
        parts = text.split("---\n")
        assert len(parts) >= 2
        fm = yaml.safe_load(parts[1])

        # Check required fields
        assert "id" in fm
        assert "entity_type" in fm
        assert "title" in fm
        assert "status" in fm
        assert "role" in fm
        assert "timeline" in fm
        assert "sources" in fm
        assert "provenance" in fm

    def test_golden_deterministic(self, pipeline, vault, artifact):
        """Running twice produces the same result."""
        r1 = pipeline.run(artifact, vault)
        
        # Clean up and run again
        r1.written_path.unlink()
        r2 = pipeline.run(artifact, vault)

        assert r1.knowledge_object.fields["title"] == r2.knowledge_object.fields["title"]
        assert r1.knowledge_object.fields["status"] == r2.knowledge_object.fields["status"]
        assert r1.knowledge_object.fields["role"] == r2.knowledge_object.fields["role"]
