"""JSONResumeRenderer -- renders ResumeIR to JSON Resume schema (Sprint 5).

Phase 2: Template-aware rendering with support for:
    - Dynamic basics from ir.basics (name, email, phone, location, profiles)
    - Summary from ir.summary

Core principle: Resume is just a projection of Knowledge.
ResumeIR is the intermediate; Renderer is the final step.

    ResumeIR -> JSONResumeRenderer -> JSON Resume (jsonresume.org)

No LLM. Pure template rendering. stdlib only.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from runtime.resume.ir import ResumeIR
from runtime.resume.renderer.base import Renderer


class JSONResumeRenderer(Renderer):
    """Render a ResumeIR as a JSON Resume (jsonresume.org schema)."""

    def __init__(self) -> None:
        pass

    # -- Renderer ABC -------------------------------------------------------

    def render(self, ir: ResumeIR) -> str:  # noqa: D401
        """Produce a JSON Resume string from *ir*."""
        # Build basics from ir.basics
        basics_dict = {
            "name": ir.basics.get("name", "ResumeOS User"),
            "label": ir.target_company or "Software Engineer",
            "email": ir.basics.get("email", ""),
            "phone": ir.basics.get("phone", ""),
            "website": ir.basics.get("website", ""),
        }

        # Location (if available)
        if ir.basics.get("location"):
            basics_dict["location"] = {"city": ir.basics.get("location")}

        # Profiles (GitHub, LinkedIn, etc.)
        profiles = []
        if ir.basics.get("linkedin"):
            profiles.append({"network": "LinkedIn", "username": "", "url": ir.basics["linkedin"]})
        if ir.basics.get("github"):
            profiles.append({"network": "GitHub", "username": "", "url": ir.basics["github"]})
        if profiles:
            basics_dict["profiles"] = profiles

        # Summary (if available)
        if ir.summary:
            basics_dict["summary"] = ir.summary

        data: Dict[str, Any] = {
            "basics": basics_dict,
            "work": [],
            "projects": [],
            "education": [],
            "skills": [],
            "awards": [],
        }

        for section in ir.sections:
            sname = section.name
            for item in section.items:
                content: Dict[str, Any] = item.content or {}
                title: str = item.title or ""

                if sname == "experience" or item.entity_type in ("job", "experience"):
                    entry = self._render_work(title, content)
                    if entry:
                        data["work"].append(entry)

                elif sname == "projects" or item.entity_type == "project":
                    entry = self._render_project(title, content)
                    if entry:
                        data["projects"].append(entry)

                elif sname == "education" or item.entity_type == "education":
                    entry = self._render_education(title, content)
                    if entry:
                        data["education"].append(entry)

                elif sname == "skills" or item.entity_type == "skill":
                    entry = self._render_skill(title, content)
                    if entry:
                        data["skills"].append(entry)

                elif sname == "awards" or item.entity_type == "award":
                    entry = self._render_award(title, content)
                    if entry:
                        data["awards"].append(entry)

        return json.dumps(data, indent=2, ensure_ascii=False)

    def file_extension(self) -> str:  # noqa: D102
        return "json"

    def format_name(self) -> str:  # noqa: D102
        return "JSON Resume"

    # -- Helpers ------------------------------------------------------------

    @staticmethod
    def _safe_timeline(content: Dict[str, Any]) -> Dict[str, str]:
        tl = content.get("timeline") or {}
        if isinstance(tl, dict):
            return {"start": tl.get("start", ""), "end": tl.get("end", "")}
        return {"start": "", "end": ""}

    @classmethod
    def _render_work(cls, title: str, content: Dict[str, Any]) -> Dict[str, str]:
        tl = cls._safe_timeline(content)
        return {
            "name": title,
            "position": content.get("role", ""),
            "startDate": tl["start"],
            "endDate": tl["end"],
        }

    @classmethod
    def _render_project(cls, title: str, content: Dict[str, Any]) -> Dict[str, Any]:
        tl = cls._safe_timeline(content)
        stack = content.get("stack") or {}
        if isinstance(stack, dict):
            software: list = stack.get("software", []) or []
        elif isinstance(stack, list):
            software = stack
        else:
            software = []
        return {
            "name": title,
            "description": content.get("contribution", ""),
            "keywords": list(software),
            "startDate": tl["start"],
            "endDate": tl["end"],
        }

    @classmethod
    def _render_education(cls, title: str, content: Dict[str, Any]) -> Dict[str, str]:
        tl = cls._safe_timeline(content)
        return {
            "institution": content.get("institution", ""),
            "area": title,
            "studyType": content.get("degree", ""),
            "startDate": tl["start"],
            "endDate": tl["end"],
        }

    @classmethod
    def _render_skill(cls, title: str, content: Dict[str, Any]) -> Dict[str, Any]:
        level = content.get("level", content.get("proficiency", ""))
        tags: list = []
        raw_tags = content.get("tags")
        if isinstance(raw_tags, list):
            tags = raw_tags
        elif isinstance(raw_tags, str):
            tags = [raw_tags]
        return {
            "name": title,
            "level": level,
            "keywords": tags,
        }

    @classmethod
    def _render_award(cls, title: str, content: Dict[str, Any]) -> Dict[str, str]:
        return {
            "title": title,
            "date": content.get("date", ""),
            "summary": content.get("rank", ""),
        }
