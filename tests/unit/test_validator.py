"""Unit tests for the Validator stage."""
from __future__ import annotations

from pathlib import Path

import pytest

from runtime.builder.validator import Validator
from runtime.knowledge.draft import Draft


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_ROOT = REPO_ROOT / "schemas"


@pytest.fixture
def validator():
    return Validator(schemas_root=SCHEMAS_ROOT)


class TestValidator:
    """Test the Validator class."""

    def test_validate_valid_draft(self, validator):
        draft = Draft(
            entity_type="project",
            fields={
                "title": "My Project",
                "entity_type": "project",
                "status": "active",
                "timeline": {"start": "2024-01-01"},
                "role": "Developer",
                "sources": [{"kind": "readme", "ref": "test.md"}],
            },
        )
        result = validator.validate(draft)
        assert result.is_valid
        assert result.validation_errors == []

    def test_validate_missing_required_field(self, validator):
        draft = Draft(
            entity_type="project",
            fields={
                "title": "My Project",
                "entity_type": "project",
                # Missing: status, timeline, role, sources
            },
        )
        result = validator.validate(draft)
        assert not result.is_valid
        assert len(result.validation_errors) > 0
        # Check that missing fields are reported
        errors_text = " ".join(result.validation_errors).lower()
        assert "status" in errors_text or "timeline" in errors_text

    def test_validate_invalid_status_value(self, validator):
        draft = Draft(
            entity_type="project",
            fields={
                "title": "My Project",
                "entity_type": "project",
                "status": "invalid-status",
                "timeline": {"start": "2024-01-01"},
                "role": "Developer",
                "sources": [{"kind": "readme", "ref": "test.md"}],
            },
        )
        result = validator.validate(draft)
        assert not result.is_valid
        assert len(result.validation_errors) > 0

    def test_validate_missing_schema_file(self, validator, tmp_path):
        validator.schemas_root = tmp_path / "nonexistent"
        draft = Draft(entity_type="project", fields={})
        result = validator.validate(draft)
        assert not result.is_valid
        assert len(result.validation_errors) > 0
        assert "schema not found" in result.validation_errors[0]
