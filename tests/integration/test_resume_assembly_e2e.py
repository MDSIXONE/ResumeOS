"""Sprint 5 acceptance test -- Resume Assembly Engine E2E.

This file is the CONTRACT for Sprint 5. The fixer must implement
``runtime/resume/`` modules so that every test passes.

Core principle (user directive):
    Resume is just a projection of the Career Knowledge Base.
    Knowledge -> Selector -> Ranker -> Layout -> ResumeIR -> Renderer

Verifies:
    1. Full pipeline: Knowledge + JD -> ResumeIR -> 3 rendered files (MD/JSON/HTML)
    2. Selector: JD keyword matching selects relevant entities
    3. Ranker: different criteria produce different orderings
    4. Layout: section ordering + one-page/two-page constraints
    5. Explainability (★★★★★): every item carries WHY it was selected
    6. Tailoring: produces ResumeIR, NEVER modifies Knowledge
    7. Resume Review: compares Knowledge vs ResumeIR, reports gaps
    8. Renderers: Markdown + JSON Resume + HTML all render from same ResumeIR

Architectural constraints (user directive, CI-enforced in test_resume_constraints.py):
    - runtime/resume/ MUST NOT import any LLM SDK
    - Resume pipeline MUST NOT modify Knowledge
    - runtime/resume/ MUST NOT import skills/ or runtime/builder/
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any, Dict, List

import pytest
import yaml


# ---------------------------------------------------------------------------
# Fixtures: a rich Knowledge Base with diverse entities
# ---------------------------------------------------------------------------

@pytest.fixture
def vault_with_kb(tmp_path):
    """Create a vault with 3 projects, 3 skills, 1 education, 1 award."""
    vault = tmp_path / "vault"
    career = vault / "career"

    # Projects
    projects = career / "projects"
    projects.mkdir(parents=True)

    (projects / "px4-uav.md").write_text(textwrap.dedent("""\
        ---
        id: px4-uav
        entity_type: project
        title: PX4 UAV Flight Controller
        tags: [ROS, C++, drone, embedded, robotics]
        status: completed
        role: Developer
        timeline:
          start: 2024-01-01
          end: 2024-06-01
        stack:
          software: [C++, ROS, Python, PX4]
        metrics:
          - {label: FPS, value: "35"}
        contribution: Designed flight control algorithms
        ---
        # PX4 UAV
        """), encoding="utf-8")

    (projects / "yolo-detection.md").write_text(textwrap.dedent("""\
        ---
        id: yolo-detection
        entity_type: project
        title: YOLO Real-time Detection
        tags: [Python, PyTorch, OpenCV, computer-vision]
        status: completed
        role: Developer
        timeline:
          start: 2023-06-01
          end: 2023-12-01
        stack:
          software: [Python, PyTorch, OpenCV]
        metrics:
          - {label: mAP, value: "0.89"}
        contribution: Built object detection pipeline
        ---
        # YOLO Detection
        """), encoding="utf-8")

    (projects / "ros-navigation.md").write_text(textwrap.dedent("""\
        ---
        id: ros-navigation
        entity_type: project
        title: ROS Navigation Stack
        tags: [ROS, ROS2, SLAM, navigation, robotics]
        status: completed
        role: Lead Developer
        timeline:
          start: 2024-03-01
          end: 2024-09-01
        stack:
          software: [ROS, ROS2, C++, Python]
        metrics:
          - {label: accuracy, value: "97%"}
        contribution: Implemented SLAM and path planning
        ---
        # ROS Navigation
        """), encoding="utf-8")

    # Skills
    skills = career / "skills"
    skills.mkdir(parents=True)

    for sid, title, tags in [
        ("python", "Python", ["python", "programming"]),
        ("ros", "ROS", ["ros", "robotics", "middleware"]),
        ("pytorch", "PyTorch", ["pytorch", "deep-learning", "ai"]),
    ]:
        (skills / f"{sid}.md").write_text(textwrap.dedent(f"""\
            ---
            id: {sid}
            entity_type: skill
            title: {title}
            tags: {tags}
            proficiency: advanced
            last_used: 2024-06-01
            ---
            # {title}
            """), encoding="utf-8")

    # Education
    education = career / "education"
    education.mkdir(parents=True)

    (education / "beng-robotics.md").write_text(textwrap.dedent("""\
        ---
        id: beng-robotics
        entity_type: education
        title: BEng Robotics Engineering
        tags: [robotics, engineering]
        institution: Test University
        degree: BEng
        timeline:
          start: 2020-09-01
          end: 2024-06-01
        ---
        # BEng Robotics
        """), encoding="utf-8")

    # Awards
    awards = career / "awards"
    awards.mkdir(parents=True)

    (awards / "robomaster-2024.md").write_text(textwrap.dedent("""\
        ---
        id: robomaster-2024
        entity_type: award
        title: RoboMaster 2024 Gold Award
        tags: [robotics, competition]
        rank: "1st"
        date: 2024-08-01
        ---
        # RoboMaster 2024
        """), encoding="utf-8")

    # Library dirs
    (vault / ".library" / "index").mkdir(parents=True)

    yield vault


@pytest.fixture
def kb_index(vault_with_kb):
    """Build a KnowledgeIndex from the vault."""
    from runtime.knowledge_index import KnowledgeIndex

    idx = KnowledgeIndex(vault_root=vault_with_kb)
    idx.build()
    return idx


@pytest.fixture
def ros_jd():
    """A JD that emphasizes ROS and robotics."""
    return textwrap.dedent("""\
        We are looking for a Robotics Software Engineer with experience in:
        - ROS / ROS2
        - Robot navigation and SLAM
        - C++ programming
        - Embedded systems
        - Drone or autonomous vehicle experience

        You will work on flight control systems and navigation algorithms.
        """)


@pytest.fixture
def cv_jd():
    """A JD that emphasizes computer vision — should rank YOLO higher."""
    return textwrap.dedent("""\
        We are looking for a Computer Vision Engineer with experience in:
        - Python and PyTorch
        - Object detection (YOLO, SSD, Faster R-CNN)
        - OpenCV
        - Deep learning models
        - Real-time inference

        You will build detection pipelines for production systems.
        """)


# ---------------------------------------------------------------------------
# 1. Full Pipeline E2E
# ---------------------------------------------------------------------------

class TestFullPipeline:
    """Knowledge + JD -> Selector -> Ranker -> Layout -> ResumeIR -> 3 files."""

    def test_full_pipeline_produces_resumeir(self, kb_index, ros_jd, tmp_path):
        from runtime.resume.pipeline import ResumeAssemblyPipeline

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=ros_jd, company="Boston Dynamics")

        assert ir is not None
        assert ir.target_jd == ros_jd
        assert ir.target_company == "Boston Dynamics"
        assert len(ir.sections) > 0
        assert ir.item_count > 0

    def test_pipeline_produces_three_rendered_files(self, kb_index, ros_jd, tmp_path):
        from runtime.resume.pipeline import ResumeAssemblyPipeline
        from runtime.resume.renderer.markdown import MarkdownRenderer
        from runtime.resume.renderer.json_resume import JSONResumeRenderer
        from runtime.resume.renderer.html import HTMLRenderer

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=ros_jd)

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        renderers = [MarkdownRenderer(), JSONResumeRenderer(), HTMLRenderer()]
        paths = []
        for r in renderers:
            path = r.render_to_dir(ir, output_dir, filename="resume")
            paths.append(path)

        assert len(paths) == 3
        for p in paths:
            assert p.exists()
            assert p.stat().st_size > 0
        assert paths[0].suffix == ".md"
        assert paths[1].suffix == ".json"
        assert paths[2].suffix == ".html"

    def test_knowledge_unchanged_after_pipeline(self, kb_index, ros_jd):
        """★★★★★ Knowledge must be immutable — pipeline reads, never writes."""
        from runtime.resume.pipeline import ResumeAssemblyPipeline

        projects_before = kb_index.query(entity_type="project")
        skills_before = kb_index.query(entity_type="skill")
        titles_before = [p["title"] for p in projects_before]

        pipeline = ResumeAssemblyPipeline()
        pipeline.assemble(kb_index, jd=ros_jd)

        projects_after = kb_index.query(entity_type="project")
        skills_after = kb_index.query(entity_type="skill")
        titles_after = [p["title"] for p in projects_after]

        assert titles_before == titles_after
        assert len(skills_before) == len(skills_after)

    def test_different_jds_produce_different_rankings(self, kb_index, ros_jd, cv_jd):
        """Same Knowledge, different JDs -> different item orderings."""
        from runtime.resume.pipeline import ResumeAssemblyPipeline

        pipeline = ResumeAssemblyPipeline()
        ir_ros = pipeline.assemble(kb_index, jd=ros_jd)
        ir_cv = pipeline.assemble(kb_index, jd=cv_jd)

        ros_projects = ir_ros.get_section("projects")
        cv_projects = ir_cv.get_section("projects")
        assert ros_projects is not None
        assert cv_projects is not None

        ros_order = [i.entity_id for i in ros_projects.items]
        cv_order = [i.entity_id for i in cv_projects.items]

        # ROS JD should rank ROS projects higher; CV JD should rank YOLO higher
        # The orderings should be different (at least one item position differs)
        assert ros_order != cv_order
        # ROS JD: ros-navigation or px4-uav should be top
        assert ros_order[0] in ("ros-navigation", "px4-uav")
        # CV JD: yolo-detection should be top
        assert cv_order[0] == "yolo-detection"


# ---------------------------------------------------------------------------
# 2. Selector
# ---------------------------------------------------------------------------

class TestSelector:
    """Selector: JD keyword matching -> selected entities."""

    def test_selector_picks_ros_projects_for_ros_jd(self, kb_index, ros_jd):
        from runtime.resume.selector import Selector

        selector = Selector()
        all_entities = kb_index.query()
        selected = selector.select(all_entities, jd=ros_jd)

        entity_ids = [e["id"] for e in selected]
        # PX4 UAV and ROS Navigation should be selected (both have ROS tag)
        assert "px4-uav" in entity_ids
        assert "ros-navigation" in entity_ids

    def test_selector_picks_cv_project_for_cv_jd(self, kb_index, cv_jd):
        from runtime.resume.selector import Selector

        selector = Selector()
        all_entities = kb_index.query()
        selected = selector.select(all_entities, jd=cv_jd)

        entity_ids = [e["id"] for e in selected]
        assert "yolo-detection" in entity_ids

    def test_selector_does_not_modify_input(self, kb_index, ros_jd):
        from runtime.resume.selector import Selector

        selector = Selector()
        all_entities = kb_index.query()
        original_count = len(all_entities)
        selector.select(all_entities, jd=ros_jd)
        # Input list should be unchanged
        assert len(all_entities) == original_count


# ---------------------------------------------------------------------------
# 3. Ranker
# ---------------------------------------------------------------------------

class TestRanker:
    """Ranker: scoring + sorting of selected items."""

    def test_ranker_orders_by_relevance(self, kb_index, ros_jd):
        from runtime.resume.selector import Selector
        from runtime.resume.ranker import Ranker

        selector = Selector()
        selected = selector.select(kb_index.query(), jd=ros_jd)

        ranker = Ranker()
        ranked = ranker.rank(selected, jd=ros_jd)

        # Higher scores should come first
        scores = [item.rank_score for item in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_ranker_assigns_explanation(self, kb_index, ros_jd):
        from runtime.resume.selector import Selector
        from runtime.resume.ranker import Ranker

        selector = Selector()
        selected = selector.select(kb_index.query(), jd=ros_jd)

        ranker = Ranker()
        ranked = ranker.rank(selected, jd=ros_jd)

        for item in ranked:
            assert item.explanation is not None
            assert len(item.explanation.matched_keywords) > 0 or \
                   item.explanation.selection_reason != ""

    def test_different_jd_different_scores(self, kb_index, ros_jd, cv_jd):
        from runtime.resume.selector import Selector
        from runtime.resume.ranker import Ranker

        selector = Selector()
        ranker = Ranker()

        # YOLO project: should score higher with CV JD than ROS JD
        selected_ros = selector.select(kb_index.query(), jd=ros_jd)
        selected_cv = selector.select(kb_index.query(), jd=cv_jd)

        ranked_ros = ranker.rank(selected_ros, jd=ros_jd)
        ranked_cv = ranker.rank(selected_cv, jd=cv_jd)

        yolo_ros = next((i for i in ranked_ros if i.entity_id == "yolo-detection"), None)
        yolo_cv = next((i for i in ranked_cv if i.entity_id == "yolo-detection"), None)

        if yolo_ros and yolo_cv:
            assert yolo_cv.rank_score > yolo_ros.rank_score


# ---------------------------------------------------------------------------
# 4. Layout
# ---------------------------------------------------------------------------

class TestLayout:
    """Layout: section ordering + page constraints."""

    def test_layout_produces_sections(self, kb_index, ros_jd):
        from runtime.resume.selector import Selector
        from runtime.resume.ranker import Ranker
        from runtime.resume.layout import Layout

        selector = Selector()
        selected = selector.select(kb_index.query(), jd=ros_jd)
        ranker = Ranker()
        ranked = ranker.rank(selected, jd=ros_jd)

        layout = Layout()
        ir = layout.arrange(ranked, layout_mode="one-page")

        assert len(ir.sections) > 0
        assert ir.layout == "one-page"

    def test_layout_section_order_is_defined(self, kb_index, ros_jd):
        from runtime.resume.selector import Selector
        from runtime.resume.ranker import Ranker
        from runtime.resume.layout import Layout

        selector = Selector()
        selected = selector.select(kb_index.query(), jd=ros_jd)
        ranker = Ranker()
        ranked = ranker.rank(selected, jd=ros_jd)

        layout = Layout()
        ir = layout.arrange(ranked, layout_mode="one-page")

        assert len(ir.section_order) > 0
        assert len(ir.section_order) == len(ir.sections)

    def test_layout_one_page_limits_items(self, kb_index, ros_jd):
        """One-page layout should cap items per section."""
        from runtime.resume.selector import Selector
        from runtime.resume.ranker import Ranker
        from runtime.resume.layout import Layout

        selector = Selector()
        selected = selector.select(kb_index.query(), jd=ros_jd)
        ranker = Ranker()
        ranked = ranker.rank(selected, jd=ros_jd)

        layout = Layout()
        ir = layout.arrange(ranked, layout_mode="one-page")

        # One-page resume should not have too many items total
        # (exact limit is an implementation detail, but it should be bounded)
        assert ir.item_count <= 20  # reasonable upper bound for one page


# ---------------------------------------------------------------------------
# 5. Explainability (★★★★★)
# ---------------------------------------------------------------------------

class TestExplainability:
    """Every item carries WHY it was selected."""

    def test_every_item_has_explanation(self, kb_index, ros_jd):
        from runtime.resume.pipeline import ResumeAssemblyPipeline

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=ros_jd)

        for item in ir.all_items:
            assert item.explanation is not None

    def test_explain_api_returns_explanation(self, kb_index, ros_jd):
        from runtime.resume.pipeline import ResumeAssemblyPipeline

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=ros_jd)

        first_item = ir.all_items[0]
        explanation = ir.explain(first_item.item_id)
        assert explanation is not None

    def test_explain_nonexistent_returns_none(self, kb_index, ros_jd):
        from runtime.resume.pipeline import ResumeAssemblyPipeline

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=ros_jd)

        assert ir.explain("nonexistent-item-id") is None

    def test_matched_keywords_non_empty_for_top_item(self, kb_index, ros_jd):
        from runtime.resume.pipeline import ResumeAssemblyPipeline

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=ros_jd)

        # The top project should have matched keywords from the JD
        projects = ir.get_section("projects")
        if projects and projects.items:
            top = projects.items[0]
            assert len(top.explanation.matched_keywords) > 0


# ---------------------------------------------------------------------------
# 6. Tailoring (Knowledge immutable)
# ---------------------------------------------------------------------------

class TestTailoring:
    """Tailoring: JD -> ResumeIR. Knowledge is NEVER modified."""

    def test_tailoring_produces_resumeir(self, kb_index, ros_jd):
        from runtime.resume.tailoring import Tailoring

        tailoring = Tailoring()
        ir = tailoring.tailor(kb_index, jd=ros_jd, company="Test Co")

        assert ir is not None
        assert ir.target_jd == ros_jd
        assert ir.target_company == "Test Co"

    def test_tailoring_does_not_modify_knowledge(self, kb_index, ros_jd):
        """★★★★★ Tailoring must not change the Knowledge Base."""
        from runtime.resume.tailoring import Tailoring

        projects_before = kb_index.query(entity_type="project")
        count_before = len(projects_before)

        tailoring = Tailoring()
        tailoring.tailor(kb_index, jd=ros_jd)

        projects_after = kb_index.query(entity_type="project")
        assert len(projects_after) == count_before
        # Titles and IDs should be unchanged
        ids_before = sorted(p["id"] for p in projects_before)
        ids_after = sorted(p["id"] for p in projects_after)
        assert ids_before == ids_after

    def test_tailoring_different_jds_different_irs(self, kb_index, ros_jd, cv_jd):
        from runtime.resume.tailoring import Tailoring

        tailoring = Tailoring()
        ir1 = tailoring.tailor(kb_index, jd=ros_jd, company="A")
        ir2 = tailoring.tailor(kb_index, jd=cv_jd, company="B")

        assert ir1.ir_id != ir2.ir_id
        assert ir1.target_company != ir2.target_company


# ---------------------------------------------------------------------------
# 7. Resume Review (Knowledge vs ResumeIR gap analysis)
# ---------------------------------------------------------------------------

class TestResumeReview:
    """Review: compare Knowledge vs ResumeIR, report gaps."""

    def test_review_reports_skill_gap(self, kb_index, ros_jd):
        """Knowledge has 3 skills, ResumeIR might have fewer -> gap reported."""
        from runtime.resume.pipeline import ResumeAssemblyPipeline
        from runtime.resume.review import ResumeReview

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=ros_jd)

        review = ResumeReview()
        report = review.review(kb_index, ir)

        assert report is not None
        # Should have a gap analysis
        assert "gaps" in report or "missing" in report or "skill_gaps" in report

    def test_review_does_not_modify_inputs(self, kb_index, ros_jd):
        from runtime.resume.pipeline import ResumeAssemblyPipeline
        from runtime.resume.review import ResumeReview

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=ros_jd)

        ir_items_before = ir.item_count
        skills_before = len(kb_index.query(entity_type="skill"))

        review = ResumeReview()
        review.review(kb_index, ir)

        assert ir.item_count == ir_items_before
        assert len(kb_index.query(entity_type="skill")) == skills_before


# ---------------------------------------------------------------------------
# 8. Renderers
# ---------------------------------------------------------------------------

class TestRenderers:
    """All renderers produce valid output from the same ResumeIR."""

    @pytest.fixture
    def sample_ir(self, kb_index, ros_jd):
        from runtime.resume.pipeline import ResumeAssemblyPipeline
        pipeline = ResumeAssemblyPipeline()
        return pipeline.assemble(kb_index, jd=ros_jd)

    def test_markdown_renderer_produces_valid_markdown(self, sample_ir):
        from runtime.resume.renderer.markdown import MarkdownRenderer

        r = MarkdownRenderer()
        output = r.render(sample_ir)

        assert isinstance(output, str)
        assert len(output) > 0
        assert output.startswith("#")  # Markdown starts with a heading
        assert r.file_extension() == "md"

    def test_json_resume_renderer_produces_valid_json(self, sample_ir):
        from runtime.resume.renderer.json_resume import JSONResumeRenderer

        r = JSONResumeRenderer()
        output = r.render(sample_ir)

        assert isinstance(output, str)
        data = json.loads(output)  # Must be valid JSON
        assert isinstance(data, dict)
        assert r.file_extension() == "json"

    def test_html_renderer_produces_valid_html(self, sample_ir):
        from runtime.resume.renderer.html import HTMLRenderer

        r = HTMLRenderer()
        output = r.render(sample_ir)

        assert isinstance(output, str)
        assert len(output) > 0
        assert "<html" in output.lower() or "<!doctype" in output.lower()
        assert r.file_extension() == "html"

    def test_all_renderers_same_ir(self, sample_ir):
        """All 3 renderers can render the same ResumeIR without error."""
        from runtime.resume.renderer.markdown import MarkdownRenderer
        from runtime.resume.renderer.json_resume import JSONResumeRenderer
        from runtime.resume.renderer.html import HTMLRenderer

        for r in [MarkdownRenderer(), JSONResumeRenderer(), HTMLRenderer()]:
            output = r.render(sample_ir)
            assert len(output) > 0
