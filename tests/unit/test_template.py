"""Unit tests for TemplateConfig (Phase 1.5).

Tests the template loading, validation, and accessor methods.
"""
from __future__ import annotations

import pytest

from runtime.resume.template import TemplateConfig


class TestTemplateConfig:
    """Test TemplateConfig dataclass and its methods."""

    def test_load_chinese_resume(self):
        """Load chinese-resume template and verify key properties."""
        template = TemplateConfig.load("chinese-resume")

        assert template.template_id == "chinese-resume"
        assert template.name == "中文简历"
        assert template.cjk is True
        assert template.ats_safe is True
        assert template.section_order[0] == "education"
        assert "skills" in template.section_order
        assert template.get_section_title("education") == "教育背景"
        assert template.get_section_title("skills") == "技能特长"

    def test_load_classic_ats(self):
        """Load classic-ats template (default) and verify key properties."""
        template = TemplateConfig.load("classic-ats")

        assert template.template_id == "classic-ats"
        assert template.name == "Classic ATS"
        assert template.cjk is False
        assert template.ats_safe is True
        assert template.section_order[0] == "skills"
        assert "projects" in template.section_order
        assert template.get_section_title("skills") == "Skills"
        assert template.get_section_title("projects") == "Projects"

    def test_default_returns_classic_ats(self):
        """TemplateConfig.default() should return classic-ats."""
        template = TemplateConfig.default()

        assert template.template_id == "classic-ats"

    def test_list_available(self):
        """list_available() should return at least 2 templates."""
        templates = TemplateConfig.list_available()

        assert isinstance(templates, list)
        assert len(templates) >= 2

        # Check that both classic-ats and chinese-resume are present
        ids = [t["id"] for t in templates]
        assert "classic-ats" in ids
        assert "chinese-resume" in ids

    def test_load_nonexistent_raises(self):
        """Loading a non-existent template should raise ValueError."""
        with pytest.raises(ValueError, match="Template .* not found"):
            TemplateConfig.load("nonexistent-template-xyz")

    def test_get_section_title(self):
        """get_section_title() should return the configured title or title-cased name."""
        template = TemplateConfig.load("chinese-resume")

        # Chinese titles
        assert template.get_section_title("education") == "教育背景"
        assert template.get_section_title("experience") == "工作经历"
        assert template.get_section_title("projects") == "项目经验"
        assert template.get_section_title("skills") == "技能特长"
        assert template.get_section_title("awards") == "获奖情况"

        # Fallback for unknown section
        assert template.get_section_title("unknown") == "Unknown"

    def test_show_photo_true_for_chinese(self):
        """chinese-resume should have show_photo=True, classic-ats should have False."""
        chinese = TemplateConfig.load("chinese-resume")
        classic = TemplateConfig.load("classic-ats")

        assert chinese.show_photo is True
        assert classic.show_photo is False

    def test_personal_info_fields(self):
        """chinese-resume should include gender, birthDate, etc."""
        template = TemplateConfig.load("chinese-resume")

        fields = template.personal_info_fields
        assert isinstance(fields, list)
        assert "gender" in fields
        assert "birthDate" in fields
        assert "ethnicity" in fields
        assert "politicalStatus" in fields
        assert "phone" in fields
        assert "email" in fields
        assert "location" in fields

    def test_font_family_cjk(self):
        """chinese-resume font_family should contain Microsoft YaHei or similar CJK font."""
        template = TemplateConfig.load("chinese-resume")

        # Should contain a CJK font
        assert "Microsoft YaHei" in template.font_family or "黑体" in template.font_family or "sans-serif" in template.font_family

    def test_font_family_classic(self):
        """classic-ats font_family should be a standard sans-serif."""
        template = TemplateConfig.load("classic-ats")

        assert "Segoe UI" in template.font_family or "sans-serif" in template.font_family

    def test_primary_color(self):
        """Templates should have a primary_color property."""
        chinese = TemplateConfig.load("chinese-resume")
        classic = TemplateConfig.load("classic-ats")

        assert chinese.primary_color.startswith("#")
        assert classic.primary_color.startswith("#")

    def test_photo_position(self):
        """chinese-resume should have photo_position=top-right."""
        chinese = TemplateConfig.load("chinese-resume")
        classic = TemplateConfig.load("classic-ats")

        assert chinese.photo_position == "top-right"
        assert classic.photo_position == "none"

    def test_caps(self):
        """Templates should have caps for limiting items per section."""
        template = TemplateConfig.load("classic-ats")

        assert template.get_cap("skills") == 10
        assert template.get_cap("projects") == 4
        assert template.get_cap("experience") == 3
        assert template.get_cap("unknown") is None

    def test_section_order_complete(self):
        """chinese-resume section_order should include self_evaluation."""
        template = TemplateConfig.load("chinese-resume")

        assert "education" in template.section_order
        assert "experience" in template.section_order
        assert "projects" in template.section_order
        assert "skills" in template.section_order
        assert "awards" in template.section_order
        assert "self_evaluation" in template.section_order
