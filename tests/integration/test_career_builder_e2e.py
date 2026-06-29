"""Sprint 4 acceptance test -- Career Builder pipeline E2E.

THE CONTRACT: defines the exact API the Builder pipeline must implement.
The fixer creates runtime/builder/ modules so that every test here passes.

Verifies user's 3 principles + 5 requirements:
    Principle 1: Markdown is always just a View (KnowledgeObject -> Writer)
    Principle 2: Builder never directly writes files (uses KnowledgeWriter)
    Principle 3: LLM always outputs Draft (Draft -> Validator -> Knowledge)
    Provenance: every KnowledgeObject has traceability
    No overwrite: conflicts detected, existing kept, user notified
    Events: KnowledgeDraftCreated + KnowledgeCommitted published
    Index: Knowledge Index auto-updates after commit

User's expected demo path:
    Artifact -> Planner -> Retriever -> LLM -> Draft -> Validation
    -> Knowledge -> Markdown -> Knowledge Index -> Published
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import yaml

from runtime.artifacts.base import ArtifactProvenance
from runtime.artifacts.types import ProjectArtifact
from runtime.event_bus import EventBus
from runtime.knowledge_index import KnowledgeIndex
from runtime.knowledge.object import KnowledgeObject
from runtime.knowledge.draft import Draft
from runtime.knowledge.conflict import Conflict
from runtime.knowledge.provenance import KnowledgeProvenance
from runtime.knowledge.writer import MarkdownWriter
from adapters.llm.dummy import DummyLLMProvider

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_ROOT = REPO_ROOT / "schemas"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vault(tmp_path):
    """Minimal vault with .library/ for index + events."""
    v = tmp_path / "vault"
    (v / "career" / "projects").mkdir(parents=True)
    (v / ".library" / "index").mkdir(parents=True)
    return v


@pytest.fixture
def project_artifact():
    """A realistic ProjectArtifact from a README import."""
    return ProjectArtifact(
        artifact_type="project",
        title="YOLO Detection",
        description="Real-time object detection system for robotics.",
        tech_stack=["Python", "PyTorch", "OpenCV"],
        repo_url="https://github.com/user/yolo-detection",
        languages=["Python"],
        readme_text="# YOLO Detection\nA real-time detection system.\n",
        commit_count=42,
        provenance=ArtifactProvenance(
            source_path="inbox/yolo-readme.md",
            sha256="a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
            detected_type="readme",
            extractor="readme_parser",
        ),
        confidence="inferred",
    )


@pytest.fixture
def pipeline(vault):
    """Build the full Career Builder pipeline with DummyLLMProvider."""
    from runtime.builder.pipeline import BuilderPipeline
    from runtime.builder.planner import Planner
    from runtime.builder.retriever import Retriever
    from runtime.builder.validator import Validator
    from runtime.builder.merger import Merger

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


# ---------------------------------------------------------------------------
# 1. Full pipeline E2E
# ---------------------------------------------------------------------------

class TestBuilderPipelineE2E:
    """Acceptance: Artifact -> ... -> career/projects/<id>.md with events."""

    def test_full_pipeline_produces_markdown(self, vault, project_artifact, pipeline):
        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        assert result.success is True
        assert result.written_path is not None
        assert result.written_path.exists()
        assert result.written_path.parent.name == "projects"

    def test_pipeline_produces_knowledge_object(self, vault, project_artifact, pipeline):
        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        assert result.knowledge_object is not None
        ko = result.knowledge_object
        assert isinstance(ko, KnowledgeObject)
        assert ko.entity_type == "project"
        assert ko.entity_id  # non-empty slug
        assert "title" in ko.fields
        assert ko.fields["title"] == "YOLO Detection"

    def test_pipeline_produces_draft(self, vault, project_artifact, pipeline):
        """Principle 3: LLM outputs Draft before Knowledge."""
        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        assert result.draft is not None
        assert isinstance(result.draft, Draft)
        assert result.draft.raw_output  # non-empty LLM response
        assert result.draft.is_valid  # passed validation

    def test_markdown_has_provenance(self, vault, project_artifact, pipeline):
        """Provenance: every KB entry is traceable."""
        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        text = result.written_path.read_text(encoding="utf-8")
        fm = yaml.safe_load(text.split("---\n")[1])
        assert "provenance" in fm
        prov = fm["provenance"]
        assert prov["generated_by"] == "career_builder"
        assert prov["llm"] == "dummy"
        assert prov["prompt"]  # non-empty prompt id
        assert prov["artifact"]  # non-empty artifact hash
        assert prov["time"]  # ISO 8601

    def test_markdown_has_sources(self, vault, project_artifact, pipeline):
        """Schema requires sources[] — provenance chain to original file."""
        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        text = result.written_path.read_text(encoding="utf-8")
        fm = yaml.safe_load(text.split("---\n")[1])
        assert "sources" in fm
        assert len(fm["sources"]) >= 1
        assert fm["sources"][0]["kind"]
        assert fm["sources"][0]["ref"]

    def test_knowledge_draft_created_event(self, vault, project_artifact, pipeline):
        """KnowledgeDraftCreated published after LLM produces Draft."""
        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        assert "KnowledgeDraftCreated" in result.events_published

    def test_knowledge_committed_event(self, vault, project_artifact, pipeline):
        """KnowledgeCommitted published after Writer commits."""
        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        assert "KnowledgeCommitted" in result.events_published

    def test_knowledge_index_auto_updates(self, vault, project_artifact, pipeline):
        """Knowledge Index reflects the new entity after pipeline run."""
        pipeline.run(artifact=project_artifact, vault_root=vault)
        idx = KnowledgeIndex(vault_root=vault)
        projects = idx.query(entity_type="project")
        assert len(projects) == 1
        assert projects[0]["title"] == "YOLO Detection"

    def test_pipeline_is_deterministic(self, vault, project_artifact, pipeline):
        """Same artifact + DummyLLM -> same result (golden test property)."""
        r1 = pipeline.run(artifact=project_artifact, vault_root=vault)
        # Remove the file so the second run creates it fresh
        r1.written_path.unlink()
        r2 = pipeline.run(artifact=project_artifact, vault_root=vault)
        assert r1.knowledge_object.fields.get("title") == r2.knowledge_object.fields.get("title")
        assert r1.knowledge_object.fields.get("status") == r2.knowledge_object.fields.get("status")
        assert r1.knowledge_object.fields.get("role") == r2.knowledge_object.fields.get("role")


# ---------------------------------------------------------------------------
# 2. Conflict detection (no silent overwrite)
# ---------------------------------------------------------------------------

class TestConflictDetection:
    """Acceptance: Builder never silently overwrites existing values."""

    def test_conflict_detected_when_existing_differs(self, vault, project_artifact, pipeline):
        """Existing role='Team Lead', LLM proposes 'Developer' -> conflict."""
        # Pre-create an existing entity with a different role
        existing_path = vault / "career" / "projects" / "yolo-detection.md"
        existing_path.write_text(textwrap.dedent("""\
            ---
            id: yolo-detection
            entity_type: project
            title: YOLO Detection
            status: completed
            role: Team Lead
            timeline:
              start: 2024-01-01
              end: 2024-06-01
              ongoing: false
            sources:
              - kind: manual
                ref: manual entry
            provenance:
              generated_by: manual
              llm: ""
              prompt: ""
              artifact: ""
              time: 2024-01-01T00:00:00+00:00
            ---
            # YOLO Detection
            """), encoding="utf-8")

        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        assert result.success is True
        assert len(result.conflicts) > 0
        conflict_fields = [c.field for c in result.conflicts]
        assert "role" in conflict_fields

    def test_existing_value_preserved_on_conflict(self, vault, project_artifact, pipeline):
        """On conflict, the .md keeps the existing value, NOT the LLM's."""
        existing_path = vault / "career" / "projects" / "yolo-detection.md"
        existing_path.write_text(textwrap.dedent("""\
            ---
            id: yolo-detection
            entity_type: project
            title: YOLO Detection
            status: completed
            role: Team Lead
            timeline:
              start: 2024-01-01
              end: 2024-06-01
              ongoing: false
            sources:
              - kind: manual
                ref: manual entry
            provenance:
              generated_by: manual
              llm: ""
              prompt: ""
              artifact: ""
              time: 2024-01-01T00:00:00+00:00
            ---
            # YOLO Detection
            """), encoding="utf-8")

        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        text = result.written_path.read_text(encoding="utf-8")
        fm = yaml.safe_load(text.split("---\n")[1])
        assert fm["role"] == "Team Lead"  # existing preserved, NOT "Developer"

    def test_no_conflict_when_filling_gap(self, vault, project_artifact, pipeline):
        """Existing has empty description, LLM fills it -> no conflict."""
        existing_path = vault / "career" / "projects" / "yolo-detection.md"
        existing_path.write_text(textwrap.dedent("""\
            ---
            id: yolo-detection
            entity_type: project
            title: YOLO Detection
            status: completed
            role: Developer
            timeline:
              start: 2024-01-01
              end: 2024-06-01
              ongoing: false
            sources:
              - kind: manual
                ref: manual entry
            description: ""
            provenance:
              generated_by: manual
              llm: ""
              prompt: ""
              artifact: ""
              time: 2024-01-01T00:00:00+00:00
            ---
            # YOLO Detection
            """), encoding="utf-8")

        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        # description was empty -> filling it is not a conflict
        conflict_fields = [c.field for c in result.conflicts]
        assert "description" not in conflict_fields

    def test_conflicts_recorded_in_markdown(self, vault, project_artifact, pipeline):
        """Conflicts are surfaced in the .md frontmatter for user review."""
        existing_path = vault / "career" / "projects" / "yolo-detection.md"
        existing_path.write_text(textwrap.dedent("""\
            ---
            id: yolo-detection
            entity_type: project
            title: YOLO Detection
            status: completed
            role: Team Lead
            timeline:
              start: 2024-01-01
              end: 2024-06-01
              ongoing: false
            sources:
              - kind: manual
                ref: manual entry
            provenance:
              generated_by: manual
              llm: ""
              prompt: ""
              artifact: ""
              time: 2024-01-01T00:00:00+00:00
            ---
            # YOLO Detection
            """), encoding="utf-8")

        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        text = result.written_path.read_text(encoding="utf-8")
        fm = yaml.safe_load(text.split("---\n")[1])
        assert "conflicts" in fm
        assert len(fm["conflicts"]) > 0


# ---------------------------------------------------------------------------
# 3. Version history (ADR-0015)
# ---------------------------------------------------------------------------

class TestVersionHistory:
    """Acceptance: updating an existing entity appends to history[]."""

    def test_new_entity_version_is_1(self, vault, project_artifact, pipeline):
        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        assert result.knowledge_object.version == 1
        assert result.knowledge_object.is_new is True

    def test_existing_entity_version_increments(self, vault, project_artifact, pipeline):
        """Pre-existing entity -> version 2, is_new=False."""
        existing_path = vault / "career" / "projects" / "yolo-detection.md"
        existing_path.write_text(textwrap.dedent("""\
            ---
            id: yolo-detection
            entity_type: project
            title: YOLO Detection
            status: completed
            role: Developer
            timeline:
              start: 2024-01-01
              end: 2024-06-01
              ongoing: false
            sources:
              - kind: manual
                ref: manual entry
            history:
              - version: 1
                captured_at: 2024-01-01T00:00:00+00:00
                changed_fields: []
                previous_values: {}
                reason: import
            provenance:
              generated_by: manual
              llm: ""
              prompt: ""
              artifact: ""
              time: 2024-01-01T00:00:00+00:00
            ---
            # YOLO Detection
            """), encoding="utf-8")

        result = pipeline.run(artifact=project_artifact, vault_root=vault)
        assert result.knowledge_object.is_new is False
        assert result.knowledge_object.version >= 2
