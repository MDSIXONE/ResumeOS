#!/usr/bin/env python3
"""Demo: Chinese Resume Template is alive.

Demonstrates Phase 2 template-aware rendering with a complete Chinese resume:
    - Knowledge Base with 3 projects, 3 skills, 1 education, 1 award
    - Chinese template (chinese-resume) with education-first ordering
    - Chinese personal info (gender, birthDate, ethnicity, politicalStatus)
    - Self-evaluation (自我评价) section
    - Renders to Markdown, HTML, and JSON Resume

Run:
    python scripts/demo_chinese_resume.py

Expected output:
    [ALL PASS] Chinese Resume Template is alive.
"""
from __future__ import annotations

import sys
import tempfile
import textwrap
from pathlib import Path

# Ensure repo root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runtime.knowledge_index import KnowledgeIndex
from runtime.resume import ResumeAssemblyPipeline
from runtime.resume.renderer.html import HTMLRenderer
from runtime.resume.renderer.json_resume import JSONResumeRenderer
from runtime.resume.renderer.markdown import MarkdownRenderer


# ---------------------------------------------------------------------------
# Build Knowledge Base (same as demo_sprint5.py)
# ---------------------------------------------------------------------------


def build_vault(vault: Path) -> None:
    """Create a vault with 3 projects, 3 skills, 1 education, 1 award."""
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
        ("python", "Python", ["python", "programming", "自动化"]),
        ("ros", "ROS", ["ros", "robotics", "middleware", "机器人"]),
        ("pytorch", "PyTorch", ["pytorch", "deep-learning", "ai", "智能体"]),
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
        tags: [robotics, competition]
        rank: "1st"
        date: 2024-08-01
        ---
        # RoboMaster 2024
        """), encoding="utf-8")

    # Library dirs
    (vault / ".library" / "index").mkdir(parents=True)


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------


def main():
    with tempfile.TemporaryDirectory(prefix="resumeos-chinese-") as tmp:
        vault = Path(tmp)
        build_vault(vault)

        # Build Knowledge Index
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        all_entities = idx.query()
        print(f"Knowledge Base: {len(all_entities)} entities indexed")
        print(f"  projects:  {len(idx.query(entity_type='project'))}")
        print(f"  skills:    {len(idx.query(entity_type='skill'))}")
        print(f"  education: {len(idx.query(entity_type='education'))}")
        print(f"  awards:    {len(idx.query(entity_type='award'))}")
        print()

        # --- Snapshot Knowledge BEFORE assembly (to prove immutability) ---
        kb_before = sorted(e["id"] for e in all_entities)

        # Chinese basics and self-evaluation
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

        self_evaluation = "具备扎实的机器人学与计算机视觉基础，熟悉嵌入式开发全流程。熟练掌握 ROS/ROS2 机器人操作系统，具备无人机飞控系统与自主导航系统的开发经验。在深度学习与目标检测领域有丰富实践，曾主导多个基于 YOLO 的视觉项目。具备团队协作精神，乐于学习新技术，追求工程卓越。"

        zh_jd = "需要熟悉 智能体 规划 决策 工具调用 向量检索 自动化 python ros 机器人"

        # Assemble with Chinese template
        pipeline = ResumeAssemblyPipeline()
        ir = pipeline.assemble(
            idx,
            jd=zh_jd,
            company="AI Robotics Company",
            template_id="chinese-resume",
            basics=basics,
            self_evaluation=self_evaluation,
        )

        print("=" * 60)
        print("场景: 中文简历模板 (Chinese Resume Template)")
        print("=" * 60)
        print(f"ResumeIR: {ir.ir_id[:8]}... ({ir.item_count} items)")
        print()

        # Show section order
        print("Section Order:")
        for i, name in enumerate(ir.section_order, 1):
            section = next((s for s in ir.sections if s.name == name), None)
            title = section.title if section else name
            print(f"  {i}. {title}")
        print()

        # Show top items
        print("Top items:")
        for item in sorted(ir.all_items, key=lambda i: i.rank_score, reverse=True)[:5]:
            print(f"  [{item.rank_score:.3f}] {item.section:10s} | {item.title}")
        print()

        # Render to 3 formats
        out_dir = vault / "output"
        out_dir.mkdir(parents=True)

        renderers = [
            MarkdownRenderer(),
            JSONResumeRenderer(),
            HTMLRenderer(),
        ]

        print("Rendered files:")
        for r in renderers:
            path = r.render_to_dir(ir, out_dir, filename="resume-zh")
            print(f"  [{r.format_name():12s}] {path.name}  ({path.stat().st_size}B)")
        print()

        # Verification checks
        print("=" * 60)
        print("Verification Checks")
        print("=" * 60)

        checks = []

        # Check 1: Section order starts with education
        checks.append(("Section order starts with education",
                      ir.section_order[0] == "education"))

        # Check 2: Section titles are in Chinese
        section_titles = {s.name: s.title for s in ir.sections}
        checks.append(("Section titles in Chinese (教育背景)",
                      section_titles.get("education") == "教育背景"))

        # Check 3: Chinese name in basics
        checks.append(("Basics contains Chinese name (张三)",
                      ir.basics.get("name") == "张三"))

        # Check 4: Self-evaluation on IR
        checks.append(("Self-evaluation on IR",
                      "机器人学" in ir.self_evaluation))

        # Check 5: HTML contains Chinese name
        html_output = HTMLRenderer().render(ir)
        checks.append(("HTML contains Chinese name (张三)",
                      "张三" in html_output))

        # Check 6: HTML contains personal info
        checks.append(("HTML contains personal info (性别: 男)",
                      "性别" in html_output and "男" in html_output))

        # Check 7: HTML contains self-evaluation
        checks.append(("HTML contains self-evaluation (自我评价)",
                      "自我评价" in html_output and "机器人学" in html_output))

        # Check 8: HTML uses CJK fonts
        checks.append(("HTML uses CJK fonts (Microsoft YaHei)",
                      "Microsoft YaHei" in html_output or "微软雅黑" in html_output))

        # Check 9: Markdown contains Chinese name
        md_output = MarkdownRenderer().render(ir)
        checks.append(("Markdown contains Chinese name (# 张三)",
                      "# 张三" in md_output))

        # Check 10: Markdown contains personal info
        checks.append(("Markdown contains personal info (性别)",
                      "性别" in md_output))

        # Check 11: Markdown contains self-evaluation
        checks.append(("Markdown contains self-evaluation (自我评价)",
                      "自我评价" in md_output))

        # Check 12: Knowledge unchanged
        idx_after = KnowledgeIndex(vault_root=vault)
        idx_after.build()
        kb_after = sorted(e["id"] for e in idx_after.query())
        checks.append(("Knowledge unchanged after assembly",
                      kb_before == kb_after))

        # Print checks
        all_pass = True
        for label, passed in checks:
            status = "[PASS]" if passed else "[FAIL]"
            print(f"  {status} {label}")
            if not passed:
                all_pass = False

        print()
        if all_pass:
            print("[ALL PASS] Chinese Resume Template is alive.")
            print()
            print("  [x] Template-aware rendering (chinese-resume)")
            print("  [x] Education-first section order (教育背景→工作经历→...")
            print("  [x] Chinese section titles (项目经验, 技能特长, 获奖情况)")
            print("  [x] Personal info block (性别, 出生年月, 民族, 政治面貌)")
            print("  [x] Self-evaluation section (自我评价)")
            print("  [x] CJK fonts (Microsoft YaHei)")
            print("  [x] Three renderers: Markdown + HTML + JSON Resume")
            print("  [x] Knowledge immutability (unchanged after assembly)")
        else:
            print("[FAIL] Some checks did not pass.")
            sys.exit(1)


if __name__ == "__main__":
    main()
