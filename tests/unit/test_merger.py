"""Unit tests for the Merger stage."""
from __future__ import annotations

from typing import Any, Dict

import pytest

from runtime.builder.merger import Merger
from runtime.knowledge.conflict import Conflict
from runtime.knowledge.draft import Draft
from runtime.knowledge.provenance import KnowledgeProvenance


@pytest.fixture
def merger():
    return Merger()


@pytest.fixture
def draft():
    return Draft(
        entity_type="project",
        entity_id="yolo-detection",
        fields={
            "title": "YOLO Detection",
            "status": "completed",
            "role": "Developer",
            "description": "A computer vision project",
        },
        provenance=KnowledgeProvenance(
            generated_by="career_builder", llm="dummy", prompt="v1", artifact="abc"
        ),
    )


@pytest.fixture
def plan():
    return {"entity_id": "yolo-detection", "entity_type": "project"}


class TestMerger:
    """Test the Merger class."""

    def test_merge_new_entity(self, merger, draft, plan):
        result = merger.merge(draft, None, plan)
        assert result.is_new is True
        assert result.version == 1
        assert result.conflicts == []
        assert result.fields["title"] == "YOLO Detection"

    def test_merge_existing_no_conflict(self, merger, draft, plan):
        existing = {
            "title": "YOLO Detection",
            "status": "completed",
            "role": "Developer",
        }
        result = merger.merge(draft, existing, plan)
        assert result.is_new is False
        assert result.version == 2
        assert result.conflicts == []
        assert result.fields["title"] == "YOLO Detection"
        assert result.fields["description"] == "A computer vision project"

    def test_merge_existing_with_conflict(self, merger, draft, plan):
        existing = {
            "title": "YOLO Detection",
            "status": "completed",
            "role": "Team Lead",  # Conflicts with draft's "Developer"
        }
        result = merger.merge(draft, existing, plan)
        assert result.is_new is False
        assert len(result.conflicts) == 1
        conflict = result.conflicts[0]
        assert conflict.field == "role"
        assert conflict.existing_value == "Team Lead"
        assert conflict.new_value == "Developer"
        # Existing value should be preserved
        assert result.fields["role"] == "Team Lead"

    def test_merge_fills_gaps_without_conflict(self, merger, draft, plan):
        existing = {
            "title": "YOLO Detection",
            "status": "completed",
            "role": "Developer",
            "description": "",  # Empty - should be filled without conflict
        }
        result = merger.merge(draft, existing, plan)
        assert result.is_new is False
        assert len(result.conflicts) == 0
        assert result.fields["description"] == "A computer vision project"

    def test_merge_increments_version_from_history(self, merger, draft, plan):
        existing = {
            "title": "YOLO Detection",
            "history": [
                {"version": 1, "captured_at": "2024-01-01", "changed_fields": []},
                {"version": 2, "captured_at": "2024-02-01", "changed_fields": []},
            ],
        }
        result = merger.merge(draft, existing, plan)
        assert result.version == 3  # len(history) + 1
