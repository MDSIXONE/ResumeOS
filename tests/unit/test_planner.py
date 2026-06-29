"""Unit tests for the Planner stage."""
from __future__ import annotations

import pytest

from runtime.artifacts.types import ProjectArtifact, CertificateArtifact
from runtime.builder.planner import Planner, _slugify


class TestSlugify:
    """Test the slugify helper function."""

    def test_basic_slugify(self):
        assert _slugify("YOLO Detection") == "yolo-detection"

    def test_slugify_with_special_chars(self):
        assert _slugify("Project #1 (Alpha)") == "project-1-alpha"

    def test_slugify_with_multiple_spaces(self):
        assert _slugify("My   Cool   Project") == "my-cool-project"

    def test_slugify_with_unicode(self):
        assert _slugify("项目 Alpha") == "alpha"

    def test_slugify_strips_leading_trailing_hyphens(self):
        assert _slugify("--test--") == "test"

    def test_slugify_collapses_multiple_hyphens(self):
        assert _slugify("foo---bar") == "foo-bar"

    def test_slugify_empty_string(self):
        assert _slugify("") == ""


class TestPlanner:
    """Test the Planner class."""

    def test_plan_project(self):
        planner = Planner()
        artifact = ProjectArtifact(title="YOLO Detection", tech_stack=["Python"])
        plan = planner.plan(artifact)
        assert plan["entity_type"] == "project"
        assert plan["entity_id"] == "yolo-detection"
        assert plan["artifact_type"] == "project"
        assert plan["schema_name"] == "project.schema.json"

    def test_plan_certificate_maps_to_award(self):
        planner = Planner()
        artifact = CertificateArtifact(title="AWS Certificate")
        plan = planner.plan(artifact)
        assert plan["entity_type"] == "award"
        assert plan["schema_name"] == "award.schema.json"

    def test_plan_with_empty_title(self):
        planner = Planner()
        artifact = ProjectArtifact(title="", tech_stack=[])
        plan = planner.plan(artifact)
        assert plan["entity_id"].startswith("untitled-")

    def test_plan_with_special_chars_in_title(self):
        planner = Planner()
        artifact = ProjectArtifact(title="My Project #1 (Beta)")
        plan = planner.plan(artifact)
        assert plan["entity_id"] == "my-project-1-beta"

    def test_plan_schema_name_derived_from_entity_type(self):
        planner = Planner()
        artifact = ProjectArtifact(title="Test", tech_stack=[])
        plan = planner.plan(artifact)
        assert plan["schema_name"].endswith(".schema.json")
        assert plan["entity_type"] in plan["schema_name"]
