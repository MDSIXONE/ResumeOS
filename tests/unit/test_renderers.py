"""Unit tests for the 3 Sprint 5 renderers: Markdown, JSON Resume, HTML.

These tests build ResumeIR objects manually (no dependency on Lane G pipeline).
Core principle: ResumeIR is the intermediate; Renderer is the final step.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

from runtime.resume.ir import (
    ResumeIR,
    ResumeExplanation,
    ResumeItem,
    ResumeSection,
)
from runtime.resume.renderer.markdown import MarkdownRenderer
from runtime.resume.renderer.json_resume import JSONResumeRenderer
from runtime.resume.renderer.html import HTMLRenderer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_sample_ir() -> ResumeIR:
    """Build a ResumeIR manually with one project, one skill, one education."""
    project_item = ResumeItem(
        item_id="proj-1",
        entity_type="project",
        entity_id="px4-uav",
        section="projects",
        title="PX4 UAV Flight Controller",
        content={
            "role": "Developer",
            "timeline": {"start": "2024-01-01", "end": "2024-06-01"},
            "stack": {"software": ["C++", "ROS", "Python", "PX4"]},
            "metrics": [{"label": "FPS", "value": "35"}],
            "contribution": "Designed flight control algorithms",
        },
        explanation=ResumeExplanation(
            matched_keywords=["ROS", "C++"],
            selection_reason="JD keyword overlap",
            rank_factors={"keyword_overlap": 0.8},
        ),
        rank_score=0.85,
    )
    skill_item = ResumeItem(
        item_id="skill-1",
        entity_type="skill",
        entity_id="python",
        section="skills",
        title="Python",
        content={"level": "advanced", "proficiency": "advanced"},
        explanation=ResumeExplanation(),
        rank_score=0.9,
    )
    education_item = ResumeItem(
        item_id="edu-1",
        entity_type="education",
        entity_id="beng-robotics",
        section="education",
        title="BEng Robotics Engineering",
        content={
            "institution": "Test University",
            "degree": "BEng",
            "timeline": {"start": "2020-09-01", "end": "2024-06-01"},
        },
        explanation=ResumeExplanation(),
        rank_score=0.7,
    )
    award_item = ResumeItem(
        item_id="award-1",
        entity_type="award",
        entity_id="robomaster-2024",
        section="awards",
        title="RoboMaster 2024 Gold Award",
        content={"rank": "1st", "date": "2024-08-01"},
        explanation=ResumeExplanation(),
        rank_score=0.6,
    )
    experience_item = ResumeItem(
        item_id="exp-1",
        entity_type="job",
        entity_id="intern-acme",
        section="experience",
        title="Acme Robotics",
        content={
            "role": "Software Intern",
            "timeline": {"start": "2023-06-01", "end": "2023-09-01"},
        },
        explanation=ResumeExplanation(),
        rank_score=0.75,
    )
    sections = [
        ResumeSection(name="skills", title="Skills", items=[skill_item]),
        ResumeSection(name="projects", title="Projects", items=[project_item]),
        ResumeSection(name="education", title="Education", items=[education_item]),
        ResumeSection(name="awards", title="Awards", items=[award_item]),
        ResumeSection(name="experience", title="Work Experience", items=[experience_item]),
    ]
    return ResumeIR(
        ir_id="test-resume-unit",
        target_jd="Test JD with ROS and Python",
        target_company="Test Corp",
        sections=sections,
        layout="one-page",
        section_order=["skills", "experience", "projects", "education", "awards"],
    )


def _make_empty_ir() -> ResumeIR:
    """An empty ResumeIR with zero sections."""
    return ResumeIR(
        ir_id="test-resume-empty",
        target_company="",
        target_jd="",
        sections=[],
    )


@pytest.fixture
def sample_ir() -> ResumeIR:
    return _make_sample_ir()


@pytest.fixture
def empty_ir() -> ResumeIR:
    return _make_empty_ir()


# ---------------------------------------------------------------------------
# MarkdownRenderer
# ---------------------------------------------------------------------------

class TestMarkdownRenderer:
    """Unit tests for MarkdownRenderer."""

    def test_render_non_empty_string(self, sample_ir):
        r = MarkdownRenderer()
        output = r.render(sample_ir)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_file_extension(self):
        r = MarkdownRenderer()
        assert r.file_extension() == "md"

    def test_format_name(self):
        r = MarkdownRenderer()
        assert r.format_name() == "Markdown"

    def test_starts_with_hash(self, sample_ir):
        r = MarkdownRenderer()
        output = r.render(sample_ir)
        assert output.startswith("#")

    def test_has_section_headings(self, sample_ir):
        r = MarkdownRenderer()
        output = r.render(sample_ir)
        assert "## Skills" in output
        assert "## Projects" in output
        assert "## Education" in output
        assert "## Awards" in output
        assert "## Work Experience" in output

    def test_has_project_titles(self, sample_ir):
        r = MarkdownRenderer()
        output = r.render(sample_ir)
        assert "### PX4 UAV Flight Controller" in output

    def test_has_project_details(self, sample_ir):
        r = MarkdownRenderer()
        output = r.render(sample_ir)
        assert "**Role:** Developer" in output
        assert "**Timeline:** 2024-01-01 - 2024-06-01" in output
        assert "C++, ROS, Python, PX4" in output

    def test_has_skill(self, sample_ir):
        r = MarkdownRenderer()
        output = r.render(sample_ir)
        assert "**Python**" in output
        assert "proficiency" in output.lower() or "advanced" in output.lower()

    def test_has_education(self, sample_ir):
        r = MarkdownRenderer()
        output = r.render(sample_ir)
        assert "Test University" in output
        assert "BEng" in output

    def test_has_award(self, sample_ir):
        r = MarkdownRenderer()
        output = r.render(sample_ir)
        assert "RoboMaster 2024 Gold Award" in output
        assert "1st" in output

    def test_has_experience(self, sample_ir):
        r = MarkdownRenderer()
        output = r.render(sample_ir)
        assert "Acme Robotics" in output
        assert "Software Intern" in output

    def test_target_company_in_output(self, sample_ir):
        r = MarkdownRenderer()
        output = r.render(sample_ir)
        assert "Test Corp" in output

    def test_empty_ir_no_crash(self, empty_ir):
        r = MarkdownRenderer()
        output = r.render(empty_ir)
        assert isinstance(output, str)
        assert output.startswith("#")

    def test_render_to_file(self, sample_ir, tmp_path):
        r = MarkdownRenderer()
        path = tmp_path / "resume.md"
        r.render_to_file(sample_ir, path)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert content.startswith("#")
        assert len(content) > 0

    def test_render_to_dir(self, sample_ir, tmp_path):
        r = MarkdownRenderer()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        path = r.render_to_dir(sample_ir, output_dir, filename="my_resume")
        assert path.exists()
        assert path.name == "my_resume.md"
        assert path.parent == output_dir


# ---------------------------------------------------------------------------
# JSONResumeRenderer
# ---------------------------------------------------------------------------

class TestJSONResumeRenderer:
    """Unit tests for JSONResumeRenderer."""

    def test_render_non_empty_string(self, sample_ir):
        r = JSONResumeRenderer()
        output = r.render(sample_ir)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_file_extension(self):
        r = JSONResumeRenderer()
        assert r.file_extension() == "json"

    def test_format_name(self):
        r = JSONResumeRenderer()
        assert r.format_name() == "JSON Resume"

    def test_valid_json(self, sample_ir):
        r = JSONResumeRenderer()
        output = r.render(sample_ir)
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_has_basics(self, sample_ir):
        r = JSONResumeRenderer()
        output = r.render(sample_ir)
        data = json.loads(output)
        assert "basics" in data
        assert data["basics"]["name"] == "ResumeOS User"
        assert data["basics"]["label"] == "Test Corp"

    def test_has_projects(self, sample_ir):
        r = JSONResumeRenderer()
        output = r.render(sample_ir)
        data = json.loads(output)
        assert "projects" in data
        assert len(data["projects"]) == 1
        proj = data["projects"][0]
        assert proj["name"] == "PX4 UAV Flight Controller"
        assert "C++" in proj["keywords"]

    def test_has_skills(self, sample_ir):
        r = JSONResumeRenderer()
        output = r.render(sample_ir)
        data = json.loads(output)
        assert "skills" in data
        assert len(data["skills"]) == 1
        assert data["skills"][0]["name"] == "Python"

    def test_has_education(self, sample_ir):
        r = JSONResumeRenderer()
        output = r.render(sample_ir)
        data = json.loads(output)
        assert "education" in data
        assert len(data["education"]) == 1
        assert data["education"][0]["institution"] == "Test University"

    def test_has_awards(self, sample_ir):
        r = JSONResumeRenderer()
        output = r.render(sample_ir)
        data = json.loads(output)
        assert "awards" in data
        assert len(data["awards"]) == 1
        assert data["awards"][0]["title"] == "RoboMaster 2024 Gold Award"

    def test_has_work(self, sample_ir):
        r = JSONResumeRenderer()
        output = r.render(sample_ir)
        data = json.loads(output)
        assert "work" in data
        assert len(data["work"]) == 1
        assert data["work"][0]["name"] == "Acme Robotics"

    def test_empty_ir_no_crash(self, empty_ir):
        r = JSONResumeRenderer()
        output = r.render(empty_ir)
        data = json.loads(output)
        assert "basics" in data
        assert data["projects"] == []
        assert data["skills"] == []

    def test_render_to_file(self, sample_ir, tmp_path):
        r = JSONResumeRenderer()
        path = tmp_path / "resume.json"
        r.render_to_file(sample_ir, path)
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "basics" in data

    def test_render_to_dir(self, sample_ir, tmp_path):
        r = JSONResumeRenderer()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        path = r.render_to_dir(sample_ir, output_dir, filename="my_resume")
        assert path.exists()
        assert path.name == "my_resume.json"


# ---------------------------------------------------------------------------
# HTMLRenderer
# ---------------------------------------------------------------------------

class TestHTMLRenderer:
    """Unit tests for HTMLRenderer."""

    def test_render_non_empty_string(self, sample_ir):
        r = HTMLRenderer()
        output = r.render(sample_ir)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_file_extension(self):
        r = HTMLRenderer()
        assert r.file_extension() == "html"

    def test_format_name(self):
        r = HTMLRenderer()
        assert r.format_name() == "HTML"

    def test_has_html_tag(self, sample_ir):
        r = HTMLRenderer()
        output = r.render(sample_ir)
        assert "<html" in output.lower() or "<!doctype" in output.lower()

    def test_has_h1(self, sample_ir):
        r = HTMLRenderer()
        output = r.render(sample_ir)
        assert "<h1>" in output

    def test_has_h2_for_sections(self, sample_ir):
        r = HTMLRenderer()
        output = r.render(sample_ir)
        assert "<h2>Skills</h2>" in output
        assert "<h2>Projects</h2>" in output
        assert "<h2>Education</h2>" in output

    def test_has_project_content(self, sample_ir):
        r = HTMLRenderer()
        output = r.render(sample_ir)
        assert "PX4 UAV Flight Controller" in output
        assert "Developer" in output

    def test_has_style(self, sample_ir):
        r = HTMLRenderer()
        output = r.render(sample_ir)
        assert "<style>" in output
        assert "font-family" in output

    def test_html_escape(self):
        """Verify HTML escaping of special characters."""
        ir = ResumeIR(
            ir_id="test-escape",
            sections=[
                ResumeSection(
                    name="projects",
                    title="Projects",
                    items=[
                        ResumeItem(
                            item_id="p1",
                            entity_type="project",
                            title="A <script>alert('xss')</script>",
                            content={"contribution": "Works with <b>bold</b>"},
                        ),
                    ],
                ),
            ],
        )
        r = HTMLRenderer()
        output = r.render(ir)
        assert "<script>alert" not in output
        assert "&lt;script&gt;" in output or "&lt;" in output

    def test_empty_ir_no_crash(self, empty_ir):
        r = HTMLRenderer()
        output = r.render(empty_ir)
        assert "<html" in output.lower()
        assert "<body>" in output.lower()

    def test_render_to_file(self, sample_ir, tmp_path):
        r = HTMLRenderer()
        path = tmp_path / "resume.html"
        r.render_to_file(sample_ir, path)
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "<html" in content.lower()

    def test_render_to_dir(self, sample_ir, tmp_path):
        r = HTMLRenderer()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        path = r.render_to_dir(sample_ir, output_dir, filename="my_resume")
        assert path.exists()
        assert path.name == "my_resume.html"


# ---------------------------------------------------------------------------
# Cross-renderer tests
# ---------------------------------------------------------------------------

class TestRenderersCommon:
    """Tests that apply to all renderers."""

    @pytest.fixture(params=[MarkdownRenderer, JSONResumeRenderer, HTMLRenderer])
    def renderer(self, request):
        return request.param()

    def test_render_returns_string(self, renderer, sample_ir):
        output = renderer.render(sample_ir)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_file_extension_is_string(self, renderer):
        ext = renderer.file_extension()
        assert isinstance(ext, str)
        assert len(ext) > 0

    def test_format_name_is_string(self, renderer):
        name = renderer.format_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_empty_ir_does_not_crash(self, renderer, empty_ir):
        output = renderer.render(empty_ir)
        assert isinstance(output, str)

    def test_render_to_file_creates_file(self, renderer, sample_ir, tmp_path):
        ext = renderer.file_extension()
        path = tmp_path / f"test.{ext}"
        renderer.render_to_file(sample_ir, path)
        assert path.exists()
        assert path.stat().st_size > 0

    def test_render_to_dir_creates_correct_file(self, renderer, sample_ir, tmp_path):
        output_dir = tmp_path / "out"
        output_dir.mkdir()
        path = renderer.render_to_dir(sample_ir, output_dir, filename="resume")
        assert path.exists()
        expected_ext = renderer.file_extension()
        assert path.suffix == f".{expected_ext}"
        assert path.name == f"resume.{expected_ext}"
