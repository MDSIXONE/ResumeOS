"""Unit tests for Resume Assembly Engine (Sprint 5).

Tests cover:
    - Selector: keyword extraction, matching logic, input immutability
    - Ranker: scoring, sorting, explanation population
    - Layout: section grouping, one-page caps, section ordering
    - Pipeline: end-to-end integration
    - Tailoring: JD-tailored ResumeIR production
    - ResumeReview: gap analysis and input immutability
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_entities():
    """A set of sample entity dicts for unit testing."""
    return [
        {
            "id": "proj-alpha",
            "title": "Alpha Project",
            "type": "project",
            "tags": ["python", "fastapi", "api"],
        },
        {
            "id": "proj-beta",
            "title": "Beta Robotics",
            "type": "project",
            "tags": ["ros", "c++", "robotics"],
        },
        {
            "id": "proj-gamma",
            "title": "Gamma Vision",
            "type": "project",
            "tags": ["python", "pytorch", "computer-vision"],
        },
        {
            "id": "skill-python",
            "title": "Python",
            "type": "skill",
            "tags": ["python", "programming"],
        },
        {
            "id": "skill-ros",
            "title": "ROS",
            "type": "skill",
            "tags": ["ros", "robotics", "middleware"],
        },
    ]


def _build_kb_index(tmp_path: Path):
    """Create a vault with test entities and build index.

    Shared by tests that need a KnowledgeIndex.  Returns the index.
    """
    from runtime.knowledge_index import KnowledgeIndex

    vault = tmp_path / "vault"
    career = vault / "career"

    (career / "projects").mkdir(parents=True)
    (career / "skills").mkdir(parents=True)
    (career / "education").mkdir(parents=True)

    (career / "projects" / "test-proj.md").write_text(textwrap.dedent("""\
        ---
        id: test-proj
        entity_type: project
        title: Test Project Python
        tags: [python, testing]
        timeline:
          start: 2024-01-01
          end: 2024-06-01
        metrics:
          - {label: coverage, value: "95%"}
        role: Developer
        contribution: Built test framework
        ---
        # Test Project
        """), encoding="utf-8")

    (career / "projects" / "ros-proj.md").write_text(textwrap.dedent("""\
        ---
        id: ros-proj
        entity_type: project
        title: ROS Robotics Project
        tags: [ros, ros2, robotics]
        timeline:
          start: 2024-03-01
          end: 2024-09-01
        metrics:
          - {label: accuracy, value: "97%"}
        role: Lead Developer
        contribution: Built SLAM system
        ---
        # ROS Project
        """), encoding="utf-8")

    (career / "skills" / "python.md").write_text(textwrap.dedent("""\
        ---
        id: python
        entity_type: skill
        title: Python
        tags: [python, programming]
        proficiency: advanced
        last_used: 2024-06-01
        ---
        # Python
        """), encoding="utf-8")

    (career / "skills" / "javascript.md").write_text(textwrap.dedent("""\
        ---
        id: javascript
        entity_type: skill
        title: JavaScript
        tags: [javascript, web]
        proficiency: intermediate
        last_used: 2023-12-01
        ---
        # JavaScript
        """), encoding="utf-8")

    (career / "education" / "bcs.md").write_text(textwrap.dedent("""\
        ---
        id: bcs
        entity_type: education
        title: BSc Computer Science
        tags: [education]
        institution: Test University
        degree: BSc
        timeline:
          start: 2020-09-01
          end: 2024-06-01
        ---
        # BSc CS
        """), encoding="utf-8")

    (vault / ".library" / "index").mkdir(parents=True)

    idx = KnowledgeIndex(vault_root=vault)
    idx.build()
    return idx


@pytest.fixture
def kb_index(tmp_path):
    """Build a KnowledgeIndex from a test vault."""
    return _build_kb_index(tmp_path)


# ---------------------------------------------------------------------------
# Selector Tests
# ---------------------------------------------------------------------------

class TestSelectorUnit:
    """Unit tests for Selector class."""

    def test_empty_jd_selects_all(self, sample_entities):
        """Empty JD should select all entities (generic resume)."""
        from runtime.resume.selector import Selector
        selector = Selector()
        selected = selector.select(sample_entities, jd="")
        assert len(selected) == len(sample_entities)

    def test_stopword_filtering(self, sample_entities):
        """Common stopwords should be filtered from JD keywords."""
        from runtime.resume.selector import Selector
        selector = Selector()

        # JD with lots of stopwords — only "python" and "ros" meaningful
        jd = "We are looking for experience with Python and ROS"
        selected = selector.select(sample_entities, jd=jd)

        selected_ids = {e["id"] for e in selected}
        assert "proj-alpha" in selected_ids   # has "python" tag
        assert "proj-beta" in selected_ids    # has "ros"   tag
        assert "skill-python" in selected_ids # has "python" tag

    def test_case_insensitive_matching(self, sample_entities):
        """Keyword matching should be case-insensitive."""
        from runtime.resume.selector import Selector
        selector = Selector()

        jd = "PYTHON ROS"  # uppercase in JD
        selected = selector.select(sample_entities, jd=jd)
        selected_ids = {e["id"] for e in selected}

        # "python" and "ros" tags are lowercase → must still match
        assert "proj-alpha" in selected_ids
        assert "proj-beta" in selected_ids

    def test_no_match_returns_empty(self, sample_entities):
        """Selector returns empty list when no entities match."""
        from runtime.resume.selector import Selector
        selector = Selector()
        jd = "blockchain ethereum"  # no matching tags
        selected = selector.select(sample_entities, jd=jd)
        assert len(selected) == 0

    def test_input_list_not_modified(self, sample_entities):
        """Selector does not modify the input list."""
        from runtime.resume.selector import Selector
        selector = Selector()
        original_count = len(sample_entities)
        selector.select(sample_entities, jd="python")
        assert len(sample_entities) == original_count

    def test_title_matching(self):
        """Selector matches keywords in entity title when not in tags."""
        from runtime.resume.selector import Selector
        selector = Selector()

        entities = [
            {
                "id": "test",
                "title": "Advanced Robotics System",
                "type": "project",
                "tags": ["other-tag"],
            },
        ]
        selected = selector.select(entities, jd="robotics engineer")
        assert len(selected) == 1  # "robotics" in title matches

    def test_tag_matching(self):
        """Selector matches keywords in entity tags."""
        from runtime.resume.selector import Selector
        selector = Selector()

        entities = [
            {
                "id": "test",
                "title": "Some Project",
                "type": "project",
                "tags": ["python", "fastapi"],
            },
        ]
        selected = selector.select(entities, jd="python developer")
        assert len(selected) == 1  # "python" in tags


# ---------------------------------------------------------------------------
# Ranker Tests
# ---------------------------------------------------------------------------

class TestRankerUnit:
    """Unit tests for Ranker class."""

    def test_score_range_0_to_1(self, sample_entities):
        """Rank scores should be in [0.0, 1.0]."""
        from runtime.resume.ranker import Ranker

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="python")

        for item in ranked:
            assert 0.0 <= item.rank_score <= 1.0

    def test_sort_order_descending(self, sample_entities):
        """Ranked items should be sorted by score descending."""
        from runtime.resume.ranker import Ranker

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="python")

        scores = [item.rank_score for item in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_explanation_fields_populated(self, sample_entities):
        """Each ResumeItem should have explanation fields populated."""
        from runtime.resume.ranker import Ranker

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="python")

        for item in ranked:
            assert item.explanation is not None
            assert item.explanation.selection_reason != ""
            assert isinstance(item.explanation.rank_factors, dict)
            assert "keyword_overlap" in item.explanation.rank_factors
            assert "recency" in item.explanation.rank_factors
            assert "impact" in item.explanation.rank_factors

    def test_no_jd_assigns_equal_score(self, sample_entities):
        """When no JD is given, rank_score should be 0.5 (all equal)."""
        from runtime.resume.ranker import Ranker

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="")

        assert all(item.rank_score == 0.5 for item in ranked)

    def test_matched_keywords_nonempty(self, sample_entities):
        """Items matched by JD have non-empty matched_keywords."""
        from runtime.resume.ranker import Ranker

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="python")

        items_with_python = [
            item for item in ranked
            if "python" in item.explanation.matched_keywords
        ]
        assert len(items_with_python) > 0

    def test_item_id_format(self, sample_entities):
        """ResumeItem has correct item_id format (type_short-entity_id)."""
        from runtime.resume.ranker import Ranker

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="python")

        for item in ranked:
            assert "-" in item.item_id
            assert item.entity_id in item.item_id

    def test_section_mapping_correct(self, sample_entities):
        """ResumeItem section field is correctly mapped from entity type."""
        from runtime.resume.ranker import Ranker

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="python")

        for item in ranked:
            if item.entity_type == "project":
                assert item.section in ("projects",)
            elif item.entity_type == "skill":
                assert item.section in ("skills",)

    def test_stable_sort(self, sample_entities):
        """Ranker maintains stable sort order for equal scores."""
        from runtime.resume.ranker import Ranker

        ranker = Ranker()
        ranked1 = ranker.rank(sample_entities, jd="python")
        ranked2 = ranker.rank(sample_entities, jd="python")

        assert [i.item_id for i in ranked1] == [i.item_id for i in ranked2]

    def test_recency_score_component(self):
        """Ranker computes recency score — more recent = higher score."""
        from runtime.resume.ranker import Ranker

        entities = [
            {
                "id": "recent",
                "title": "Recent Project",
                "type": "project",
                "tags": ["python"],
                "timeline": {"start": "2024-01-01", "end": "2024-06-01"},
            },
            {
                "id": "old",
                "title": "Old Project",
                "type": "project",
                "tags": ["python"],
                "timeline": {"start": "2020-01-01", "end": "2021-01-01"},
            },
        ]

        ranker = Ranker()
        ranked = ranker.rank(entities, jd="python")

        recent = next(i for i in ranked if i.entity_id == "recent")
        old = next(i for i in ranked if i.entity_id == "old")

        assert recent.explanation.rank_factors["recency"] > old.explanation.rank_factors["recency"]

    def test_impact_score_component(self):
        """Ranker computes impact score — metrics present = 0.2."""
        from runtime.resume.ranker import Ranker

        entities = [
            {
                "id": "with-metrics",
                "title": "Project with Metrics",
                "type": "project",
                "tags": ["python"],
                "metrics": [{"label": "accuracy", "value": "95%"}],
            },
            {
                "id": "no-metrics",
                "title": "Project without Metrics",
                "type": "project",
                "tags": ["python"],
            },
        ]

        ranker = Ranker()
        ranked = ranker.rank(entities, jd="python")

        with_m = next(i for i in ranked if i.entity_id == "with-metrics")
        no_m = next(i for i in ranked if i.entity_id == "no-metrics")

        assert with_m.explanation.rank_factors["impact"] > 0.0
        assert no_m.explanation.rank_factors["impact"] == 0.0


# ---------------------------------------------------------------------------
# Layout Tests
# ---------------------------------------------------------------------------

class TestLayoutUnit:
    """Unit tests for Layout class."""

    def test_section_grouping(self, sample_entities):
        """Layout groups items by their section field."""
        from runtime.resume.ranker import Ranker
        from runtime.resume.layout import Layout

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="python")

        layout = Layout()
        ir = layout.arrange(ranked, layout_mode="one-page")

        for section in ir.sections:
            for item in section.items:
                assert item.section == section.name

    def test_one_page_caps_enforced(self):
        """One-page layout enforces per-section item caps."""
        from runtime.resume.ranker import Ranker
        from runtime.resume.layout import Layout

        # Create 10 projects — cap is 4
        entities = [
            {
                "id": f"proj-{i}",
                "title": f"Project {i}",
                "type": "project",
                "tags": ["python"],
            }
            for i in range(10)
        ]

        ranker = Ranker()
        ranked = ranker.rank(entities, jd="python")

        layout = Layout()
        ir = layout.arrange(ranked, layout_mode="one-page")

        projects_section = ir.get_section("projects")
        assert projects_section is not None
        assert len(projects_section.items) <= 4  # Cap enforced

    def test_section_order_only_includes_nonempty(self, sample_entities):
        """section_order includes only non-empty sections."""
        from runtime.resume.ranker import Ranker
        from runtime.resume.layout import Layout

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="python")

        layout = Layout()
        ir = layout.arrange(ranked, layout_mode="one-page")

        section_names = {s.name for s in ir.sections}
        for name in ir.section_order:
            assert name in section_names
        assert len(ir.section_order) == len(ir.sections)

    def test_empty_items_produces_empty_ir(self):
        """Layout with empty items produces empty ResumeIR."""
        from runtime.resume.layout import Layout

        layout = Layout()
        ir = layout.arrange([], layout_mode="one-page")

        assert len(ir.sections) == 0
        assert ir.item_count == 0

    def test_section_titles_populated(self, sample_entities):
        """Each section has a display title."""
        from runtime.resume.ranker import Ranker
        from runtime.resume.layout import Layout

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="python")

        layout = Layout()
        ir = layout.arrange(ranked, layout_mode="one-page")

        for section in ir.sections:
            assert section.title != ""

    def test_provenance_metadata_set(self, sample_entities):
        """Layout sets provenance metadata on ResumeIR."""
        from runtime.resume.ranker import Ranker
        from runtime.resume.layout import Layout

        ranker = Ranker()
        ranked = ranker.rank(sample_entities, jd="python")

        layout = Layout()
        ir = layout.arrange(ranked, layout_mode="one-page")

        assert "generated_by" in ir.provenance
        assert ir.provenance["generated_by"] == "resume_assembly_engine"
        assert ir.provenance["layout"] == "one-page"


# ---------------------------------------------------------------------------
# Pipeline Tests
# ---------------------------------------------------------------------------

class TestPipelineUnit:
    """Unit tests for ResumeAssemblyPipeline class."""

    def test_end_to_end_produces_valid_resumeir(self, kb_index):
        """Pipeline produces valid ResumeIR end-to-end."""
        from runtime.resume.pipeline import ResumeAssemblyPipeline

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd="python")

        assert ir is not None
        assert len(ir.sections) > 0
        assert ir.item_count > 0
        assert ir.layout == "one-page"
        assert "generated_by" in ir.provenance

    def test_knowledge_unchanged_after_pipeline(self, kb_index):
        """Pipeline does not modify Knowledge Base."""
        entities_before = kb_index.query()
        count_before = len(entities_before)

        from runtime.resume.pipeline import ResumeAssemblyPipeline
        pipeline = ResumeAssemblyPipeline()
        pipeline.assemble(kb_index, jd="python")

        entities_after = kb_index.query()
        assert len(entities_after) == count_before

    def test_metadata_set_correctly(self, kb_index):
        """Pipeline sets target_jd and target_company on ResumeIR."""
        from runtime.resume.pipeline import ResumeAssemblyPipeline
        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd="python developer", company="Test Co")

        assert ir.target_jd == "python developer"
        assert ir.target_company == "Test Co"

    def test_generic_resume_with_empty_jd(self, kb_index):
        """Pipeline with empty JD produces generic resume (all entities = score 0.5)."""
        from runtime.resume.pipeline import ResumeAssemblyPipeline
        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd="")

        assert ir.item_count > 0
        # All items should have equal score (0.5) when no JD
        for item in ir.all_items:
            assert item.rank_score == 0.5


# ---------------------------------------------------------------------------
# Tailoring Tests
# ---------------------------------------------------------------------------

class TestTailoringUnit:
    """Unit tests for Tailoring class."""

    def test_produces_tailored_resumeir(self, kb_index):
        """Tailoring produces ResumeIR for given JD."""
        from runtime.resume.tailoring import Tailoring
        tailoring = Tailoring()
        ir = tailoring.tailor(kb_index, jd="python developer", company="Test Co")

        assert ir is not None
        assert ir.target_jd == "python developer"
        assert ir.target_company == "Test Co"

    def test_different_jds_different_irs(self, kb_index):
        """Different JDs produce different ResumeIRs (different ir_id)."""
        from runtime.resume.tailoring import Tailoring
        tailoring = Tailoring()
        ir1 = tailoring.tailor(kb_index, jd="python")
        ir2 = tailoring.tailor(kb_index, jd="robotics")

        assert ir1.ir_id != ir2.ir_id

    def test_knowledge_unchanged_by_tailoring(self, kb_index):
        """Tailoring does not modify Knowledge Base."""
        entities_before = kb_index.query()
        count_before = len(entities_before)

        from runtime.resume.tailoring import Tailoring
        tailoring = Tailoring()
        tailoring.tailor(kb_index, jd="python")

        entities_after = kb_index.query()
        assert len(entities_after) == count_before


# ---------------------------------------------------------------------------
# ResumeReview Tests
# ---------------------------------------------------------------------------

class TestResumeReviewUnit:
    """Unit tests for ResumeReview class."""

    def test_gap_detection_correct(self, kb_index):
        """Review correctly reports skill gaps between KB and ResumeIR."""
        from runtime.resume.pipeline import ResumeAssemblyPipeline
        from runtime.resume.review import ResumeReview

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd="python")

        review = ResumeReview()
        report = review.review(kb_index, ir)

        assert "skill_gaps" in report
        assert "summary" in report
        assert isinstance(report["skill_gaps"], list)
        assert len(report["skill_gaps"]) > 0

        summary = report["summary"]
        assert "total_kb_skills" in summary
        assert "total_resume_skills" in summary
        assert "missing_count" in summary
        assert summary["total_kb_skills"] >= summary["total_resume_skills"]

    def test_inputs_not_modified(self, kb_index):
        """Review does not modify Knowledge or ResumeIR."""
        from runtime.resume.pipeline import ResumeAssemblyPipeline
        from runtime.resume.review import ResumeReview

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd="python")

        ir_count_before = ir.item_count
        entities_before = kb_index.query()
        count_before = len(entities_before)

        review = ResumeReview()
        review.review(kb_index, ir)

        assert ir.item_count == ir_count_before
        assert len(kb_index.query()) == count_before

    def test_full_coverage_when_all_skills_selected(self, kb_index):
        """When all skills are selected (empty JD), missing_count == 0."""
        from runtime.resume.pipeline import ResumeAssemblyPipeline
        from runtime.resume.review import ResumeReview

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd="")

        review = ResumeReview()
        report = review.review(kb_index, ir)

        assert report["summary"]["missing_count"] == 0

    def test_skill_gap_structure(self, kb_index):
        """Skill gap entries have correct structure."""
        from runtime.resume.pipeline import ResumeAssemblyPipeline
        from runtime.resume.review import ResumeReview

        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd="python")

        review = ResumeReview()
        report = review.review(kb_index, ir)

        skill_gap = report["skill_gaps"][0]
        assert "in_kb" in skill_gap
        assert "in_resume" in skill_gap
        assert "missing" in skill_gap
        assert isinstance(skill_gap["in_kb"], list)
        assert isinstance(skill_gap["in_resume"], list)
        assert isinstance(skill_gap["missing"], list)

        # missing == in_kb - in_resume
        assert set(skill_gap["missing"]) == set(skill_gap["in_kb"]) - set(
            skill_gap["in_resume"]
        )
