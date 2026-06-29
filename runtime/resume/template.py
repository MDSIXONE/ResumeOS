"""TemplateConfig — resume layout template configuration.

A template defines:
    - Section ordering (Chinese: education→experience→projects→skills→self_evaluation)
    - Section display titles (Chinese: "教育背景" instead of "Education")
    - Item caps per section
    - Style options (font, color, photo position)
    - Which personal info fields to show (photo, gender, birthDate, etc.)

Templates are YAML files under templates/. The registry is templates/registry.yaml.
The Pipeline accepts a template_id and passes the TemplateConfig to Layout + Renderers.

Design (per Reactive Resume 39K★ pattern):
    Layout = section→page-region mapping, NOT hardcoded per template.
    Same ResumeIR renders differently depending on which TemplateConfig is active.

NO LLM — pure configuration loading. stdlib + yaml only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# Repository root (this file is at runtime/resume/template.py)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_TEMPLATES_DIR = _REPO_ROOT / "templates"
_REGISTRY_PATH = _TEMPLATES_DIR / "registry.yaml"


@dataclass
class TemplateConfig:
    """A resume layout template configuration.

    Loaded from a YAML file under templates/. Drives Layout section ordering
    and Renderer styling. The same ResumeIR produces different visual output
    depending on which TemplateConfig is active.
    """

    template_id: str = ""
    """Unique identifier, e.g. 'classic-ats', 'chinese-resume'."""

    name: str = ""
    """Human-readable name, e.g. '中文简历'."""

    description: str = ""
    """Short description of the template."""

    ats_safe: bool = True
    """Whether this template is ATS-parseable (single-column, no tables)."""

    cjk: bool = False
    """Whether this template uses CJK fonts and Chinese conventions."""

    section_order: List[str] = field(default_factory=list)
    """Ordered section names, e.g. ['education', 'experience', 'projects', ...]."""

    section_titles: Dict[str, str] = field(default_factory=dict)
    """Section name -> display title, e.g. {'education': '教育背景'}."""

    caps: Dict[str, int] = field(default_factory=dict)
    """Max items per section for one-page layout."""

    style: Dict[str, Any] = field(default_factory=dict)
    """Style options: font_family, primary_color, photo_position, photo_size."""

    fields: Dict[str, Any] = field(default_factory=dict)
    """Personal info config: show_photo, show_personal_info, personal_info[], etc."""

    # -- Loading -----------------------------------------------------------

    @classmethod
    def load(cls, template_id: str) -> "TemplateConfig":
        """Load a template by its ID from the templates/ directory.

        Args:
            template_id: e.g. 'classic-ats', 'chinese-resume'.

        Returns:
            TemplateConfig instance.

        Raises:
            FileNotFoundError: If the template YAML doesn't exist.
            ValueError: If the template_id is not in the registry.
        """
        registry = cls._load_registry()
        entry = None
        for t in registry:
            if t.get("id") == template_id:
                entry = t
                break
        if entry is None:
            raise ValueError(
                f"Template '{template_id}' not found in registry. "
                f"Available: {[t['id'] for t in registry]}"
            )

        yaml_path = _TEMPLATES_DIR / entry["file"]
        if not yaml_path.exists():
            raise FileNotFoundError(f"Template file not found: {yaml_path}")

        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        return cls._from_dict(data)

    @classmethod
    def default(cls) -> "TemplateConfig":
        """Return the default template (classic-ats).

        This ensures backward compatibility: callers that don't specify a
        template_id get the same layout as before the template system existed.
        """
        return cls.load("classic-ats")

    @classmethod
    def list_available(cls) -> List[Dict[str, Any]]:
        """List all available templates from the registry.

        Returns:
            List of dicts with keys: id, name, description, ats_safe, cjk, default.
        """
        return cls._load_registry()  # type: ignore[return-value]

    # -- Internal helpers --------------------------------------------------

    @staticmethod
    def _load_registry() -> List[Dict[str, Any]]:
        """Load the template registry YAML."""
        if not _REGISTRY_PATH.exists():
            return []
        data = yaml.safe_load(_REGISTRY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return []
        return data.get("templates", []) or []

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "TemplateConfig":
        """Construct from parsed YAML dict."""
        return cls(
            template_id=data.get("template_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            ats_safe=data.get("ats_safe", True),
            cjk=data.get("cjk", False),
            section_order=data.get("section_order", []) or [],
            section_titles=data.get("section_titles", {}) or {},
            caps=data.get("caps", {}) or {},
            style=data.get("style", {}) or {},
            fields=data.get("fields", {}) or {},
        )

    # -- Convenience accessors ---------------------------------------------

    def get_section_title(self, section_name: str) -> str:
        """Get the display title for a section, falling back to title-cased name."""
        return self.section_titles.get(section_name, section_name.title())

    def get_cap(self, section_name: str) -> Optional[int]:
        """Get the item cap for a section, or None if no cap."""
        return self.caps.get(section_name)

    @property
    def show_photo(self) -> bool:
        """Whether to show a photo."""
        return bool(self.fields.get("show_photo", False))

    @property
    def show_personal_info(self) -> bool:
        """Whether to show personal info block."""
        return bool(self.fields.get("show_personal_info", False))

    @property
    def personal_info_fields(self) -> List[str]:
        """List of personal info fields to display (e.g. gender, birthDate, ...)."""
        return self.fields.get("personal_info", []) or []

    @property
    def show_summary(self) -> bool:
        """Whether to show a professional summary section."""
        return bool(self.fields.get("show_summary", False))

    @property
    def show_self_evaluation(self) -> bool:
        """Whether to show a self-evaluation (自我评价) section."""
        return bool(self.fields.get("show_self_evaluation", False))

    @property
    def font_family(self) -> str:
        """CSS font-family string."""
        return self.style.get("font_family", "'Segoe UI', Helvetica, Arial, sans-serif")

    @property
    def primary_color(self) -> str:
        """Primary CSS color."""
        return self.style.get("primary_color", "#2a6496")

    @property
    def photo_position(self) -> str:
        """Photo position: 'none', 'top-right', or 'top-left'."""
        return self.style.get("photo_position", "none")

    @property
    def photo_size(self) -> str:
        """Photo size as CSS dimension."""
        return str(self.style.get("photo_size", "100px"))
