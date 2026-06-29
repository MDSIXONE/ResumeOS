"""Unit tests for the Retriever stage."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from runtime.builder.retriever import Retriever
from runtime.event_bus import EventBus
from runtime.knowledge.writer import MarkdownWriter
from runtime.knowledge_index import KnowledgeIndex


@pytest.fixture
def vault(tmp_path):
    v = tmp_path / "vault"
    (v / "career" / "projects").mkdir(parents=True)
    (v / ".library" / "index").mkdir(parents=True)
    return v


@pytest.fixture
def knowledge_index(vault):
    return KnowledgeIndex(vault_root=vault)


@pytest.fixture
def writer():
    return MarkdownWriter()


@pytest.fixture
def retriever(knowledge_index, writer):
    return Retriever(knowledge_index=knowledge_index, writer=writer)


class TestRetriever:
    """Test the Retriever class."""

    def test_retrieve_existing_entity(self, retriever, vault):
        # Pre-create an existing entity
        existing_path = vault / "career" / "projects" / "yolo-detection.md"
        existing_path.write_text(
            "---\nid: yolo-detection\ntitle: YOLO Detection\n---\n# YOLO\n",
            encoding="utf-8",
        )

        plan = {"entity_type": "project", "entity_id": "yolo-detection"}
        result = retriever.retrieve(plan, vault)

        assert result["existing"] is not None
        assert result["existing"]["title"] == "YOLO Detection"

    def test_retrieve_new_entity(self, retriever, vault):
        plan = {"entity_type": "project", "entity_id": "new-project"}
        result = retriever.retrieve(plan, vault)
        assert result["existing"] is None

    def test_retrieve_related_entities(self, retriever, vault, knowledge_index):
        # Create two project entities
        (vault / "career" / "projects" / "project-a.md").write_text(
            "---\nid: project-a\ntitle: Project A\n---\n# A\n", encoding="utf-8"
        )
        (vault / "career" / "projects" / "project-b.md").write_text(
            "---\nid: project-b\ntitle: Project B\n---\n# B\n", encoding="utf-8"
        )

        # Rebuild index
        knowledge_index.build()

        plan = {"entity_type": "project", "entity_id": "project-c"}
        result = retriever.retrieve(plan, vault)

        assert result["existing"] is None
        assert len(result["related"]) >= 2
