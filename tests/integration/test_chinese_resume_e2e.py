"""End-to-end tests for Chinese resume template (Phase 2).

Tests the full pipeline from Knowledge Base through to rendered output,
verifying that the Chinese template produces correct section ordering,
titles, and content.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from runtime.knowledge_index import KnowledgeIndex
from runtime.resume import ResumeAssemblyPipeline
from runtime.resume.renderer.html import HTMLRenderer
from runtime.resume.renderer.json_resume import JSONResumeRenderer
from runtime.resume.renderer.markdown import MarkdownRenderer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def vault_with_kb(tmp_path):
    """Create a vault with 3 projects, 3 skills, 1 education, 1 award.

    Same structure as demo_sprint5.py for consistency.
    """
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
        tags: [ROS, C++, drone, embedded, robotics, 机器人, 无人机, 自动化, 规划]
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
        tags: [Python, PyTorch, OpenCV, computer-vision, 智能体, 工具调用, 向量检索]
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
        tags: [ROS, ROS2, SLAM, navigation, robotics, 机器人, 规划, 决策, 自动化]
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
        ("python", "Python", ["python", "programming", "自动化"]),
        ("ros", "ROS", ["ros", "robotics", "middleware", "机器人"]),
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
        tags: [robotics, engineering, 机器人, 规划]
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
        tags: [robotics, competition, 机器人, 决策]
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
    idx = KnowledgeIndex(vault_root=vault_with_kb)
    idx.build()
    return idx


@pytest.fixture
def zh_jd():
    """A Chinese JD for AI/robotics engineer."""
    return "需要熟悉 智能体 规划 决策 工具调用 向量检索 自动化 python ros 机器人"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestChineseResumeE2E:
    """End-to-end tests for Chinese resume template."""

    def test_chinese_template_section_order(self, kb_index, zh_jd):
        """Chinese template should have education first, not skills."""
        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume")

        # Section order should start with education
        assert ir.section_order[0] == "education"
        assert "skills" in ir.section_order
        # Education should come before skills
        assert ir.section_order.index("education") < ir.section_order.index("skills")

    def test_chinese_section_titles(self, kb_index, zh_jd):
        """Chinese template should use Chinese section titles."""
        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume")

        # Check that sections have Chinese titles
        section_titles = {s.name: s.title for s in ir.sections}
        assert section_titles.get("education") == "教育背景"
        assert section_titles.get("projects") == "项目经验"
        assert section_titles.get("skills") == "技能特长"

    def test_basics_on_ir(self, kb_index, zh_jd):
        """ResumeIR should contain basics (name, gender, etc.)."""
        pipeline = ResumeAssemblyPipeline()

        basics = {
            "name": "张三",
            "gender": "男",
            "birthDate": "2000-06-15",
            "ethnicity": "汉族",
            "politicalStatus": "共青团员",
            "phone": "13800138000",
            "email": "zhangsan@example.com",
            "location": "北京",
        }

        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume", basics=basics)

        assert ir.basics["name"] == "张三"
        assert ir.basics["gender"] == "男"
        assert ir.basics["ethnicity"] == "汉族"

    def test_self_evaluation_on_ir(self, kb_index, zh_jd):
        """ResumeIR should contain self_evaluation text."""
        pipeline = ResumeAssemblyPipeline()

        self_evaluation = "具备扎实的机器人学与计算机视觉基础，熟悉嵌入式开发全流程..."
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume", self_evaluation=self_evaluation)

        assert ir.self_evaluation == self_evaluation
        assert "机器人学" in ir.self_evaluation

    def test_html_render_includes_chinese_name(self, kb_index, zh_jd):
        """HTML output should contain the Chinese name."""
        pipeline = ResumeAssemblyPipeline()
        basics = {"name": "张三", "gender": "男"}
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume", basics=basics)

        html_output = HTMLRenderer().render(ir)
        assert "张三" in html_output

    def test_html_render_includes_personal_info(self, kb_index, zh_jd):
        """HTML output should include personal info fields."""
        pipeline = ResumeAssemblyPipeline()
        basics = {
            "name": "张三",
            "gender": "男",
            "birthDate": "2000-06-15",
            "ethnicity": "汉族",
            "politicalStatus": "共青团员",
        }
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume", basics=basics)

        html_output = HTMLRenderer().render(ir)
        assert "性别" in html_output
        assert "男" in html_output
        assert "汉族" in html_output

    def test_html_render_includes_self_evaluation(self, kb_index, zh_jd):
        """HTML output should include self-evaluation section."""
        pipeline = ResumeAssemblyPipeline()
        self_evaluation = "具备扎实的机器人学与计算机视觉基础，熟悉嵌入式开发全流程..."
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume", self_evaluation=self_evaluation)

        html_output = HTMLRenderer().render(ir)
        assert "自我评价" in html_output
        assert "机器人学" in html_output

    def test_html_render_cjk_font(self, kb_index, zh_jd):
        """HTML output should use CJK fonts."""
        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume")

        html_output = HTMLRenderer().render(ir)
        assert "Microsoft YaHei" in html_output or "微软雅黑" in html_output

    def test_md_render_includes_chinese_name(self, kb_index, zh_jd):
        """Markdown output should contain the Chinese name."""
        pipeline = ResumeAssemblyPipeline()
        basics = {"name": "张三"}
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume", basics=basics)

        md_output = MarkdownRenderer().render(ir)
        assert "# 张三" in md_output

    def test_md_render_includes_personal_info(self, kb_index, zh_jd):
        """Markdown output should include personal info."""
        pipeline = ResumeAssemblyPipeline()
        basics = {
            "name": "张三",
            "gender": "男",
            "ethnicity": "汉族",
        }
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume", basics=basics)

        md_output = MarkdownRenderer().render(ir)
        assert "性别" in md_output
        assert "男" in md_output

    def test_md_render_includes_self_evaluation(self, kb_index, zh_jd):
        """Markdown output should include self-evaluation section."""
        pipeline = ResumeAssemblyPipeline()
        self_evaluation = "具备扎实的机器人学与计算机视觉基础"
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume", self_evaluation=self_evaluation)

        md_output = MarkdownRenderer().render(ir)
        assert "自我评价" in md_output
        assert "机器人学" in md_output

    def test_classic_template_still_works(self, kb_index, zh_jd):
        """Classic ATS template should still work with skills first."""
        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="classic-ats")

        # Classic ATS should have skills first
        assert ir.section_order[0] == "skills"

        # Section titles should be in English
        section_titles = {s.name: s.title for s in ir.sections}
        assert section_titles.get("skills") == "Skills"
        # Should NOT have Chinese title
        assert "教育背景" not in section_titles.values()

    def test_knowledge_unchanged(self, kb_index, zh_jd):
        """Knowledge should be unchanged after assembly."""
        pipeline = ResumeAssemblyPipeline()

        # Snapshot before
        entities_before = kb_index.query()
        ids_before = sorted(e["id"] for e in entities_before)

        # Assemble
        ir = pipeline.assemble(kb_index, jd=zh_jd, template_id="chinese-resume")

        # Snapshot after
        entities_after = kb_index.query()
        ids_after = sorted(e["id"] for e in entities_after)

        assert ids_before == ids_after
