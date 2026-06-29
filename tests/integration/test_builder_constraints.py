"""Sprint 4 CI-enforced architecture constraints.

These tests are NOT negotiable -- they enforce the user's architectural
principles at the CI level. If any of these fail, the build is broken.

Enforced rules:
    1. runtime/builder/ does NOT import from skills/
       (dependency direction: skills depend on runtime, not vice versa)
    2. runtime/builder/ does NOT import from adapters/
       (runtime knows LLMProvider ABC, never concrete providers)
    3. runtime/knowledge/ does NOT import from runtime/builder/
       (knowledge is a leaf layer; builder depends on it, not vice versa)
    4. runtime/builder/ + runtime/knowledge/ do NOT import LLM SDKs
       (no anthropic, openai, langchain, etc.)
    5. runtime/knowledge/writer.py does NOT import from runtime/builder/
       (Writer is a leaf; Builder uses Writer, not vice versa)
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RUNTIME = REPO_ROOT / "runtime"


def _imported_modules(source: str) -> list[str]:
    """Extract all imported module paths from Python source via AST."""
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.append(node.module)
    return modules


def _scan_dir(dir_path: Path) -> list[tuple[Path, str]]:
    """Return [(file_path, source_text)] for all .py files in dir_path."""
    if not dir_path.exists():
        return []
    results = []
    for py in sorted(dir_path.rglob("*.py")):
        try:
            results.append((py, py.read_text(encoding="utf-8")))
        except (OSError, UnicodeDecodeError):
            continue
    return results


# Forbidden LLM SDK keywords in runtime/ source.
_LLM_SDKS = [
    "anthropic",
    "openai",
    "google.generativeai",
    "dashscope",
    "qwen",
    "deepseek",
    "zhipuai",
    "litellm",
    "langchain",
]


class TestBuilderDoesNotImportSkills:
    """Rule 1: runtime/builder/ must NOT import from skills/."""

    def test_no_skills_imports(self):
        files = _scan_dir(RUNTIME / "builder")
        if not files:
            pytest.skip("runtime/builder/ not yet created")
        for path, source in files:
            modules = _imported_modules(source)
            for mod in modules:
                assert not mod.startswith("skills"), (
                    f"{path} imports '{mod}' from skills/ -- "
                    "runtime/builder/ must not depend on skills/ "
                    "(dependency direction: skills -> runtime)"
                )


class TestBuilderDoesNotImportAdapters:
    """Rule 2: runtime/builder/ must NOT import from adapters/.

    The builder receives a LLMProvider instance via dependency injection.
    It never imports a concrete provider. This is the seam that makes
    every LLM swappable without touching runtime/.
    """

    def test_no_adapters_imports(self):
        files = _scan_dir(RUNTIME / "builder")
        if not files:
            pytest.skip("runtime/builder/ not yet created")
        for path, source in files:
            modules = _imported_modules(source)
            for mod in modules:
                assert not mod.startswith("adapters"), (
                    f"{path} imports '{mod}' from adapters/ -- "
                    "runtime/builder/ must use LLMProvider ABC, "
                    "never a concrete provider (user directive)"
                )


class TestKnowledgeDoesNotImportBuilder:
    """Rule 3: runtime/knowledge/ must NOT import from runtime/builder/."""

    def test_no_builder_imports(self):
        files = _scan_dir(RUNTIME / "knowledge")
        if not files:
            pytest.skip("runtime/knowledge/ not yet created")
        for path, source in files:
            modules = _imported_modules(source)
            for mod in modules:
                assert "runtime.builder" not in mod, (
                    f"{path} imports '{mod}' from runtime/builder/ -- "
                    "knowledge is a leaf layer; builder depends on it, "
                    "not the reverse"
                )


class TestBuilderAndKnowledgeAreLLMAgnostic:
    """Rule 4: runtime/builder/ + runtime/knowledge/ have zero LLM SDK imports.

    Checks IMPORT statements only (via AST), not comments/docstrings.
    This avoids false positives from mentioning provider names as examples.
    """

    @pytest.mark.parametrize("subdir", ["builder", "knowledge"])
    def test_no_llm_sdk_imports(self, subdir):
        files = _scan_dir(RUNTIME / subdir)
        if not files:
            pytest.skip(f"runtime/{subdir}/ not yet created")
        for path, source in files:
            modules = _imported_modules(source)
            for mod in modules:
                mod_lower = mod.lower()
                for keyword in _LLM_SDKS:
                    assert keyword not in mod_lower, (
                        f"{path} imports '{mod}' -- "
                        f"runtime/{subdir}/ must be LLM-agnostic "
                        "(user directive: Runtime does not depend on LLM)"
                    )


class TestWriterIsLeaf:
    """Rule 5: runtime/knowledge/writer.py does NOT import from runtime/builder/."""

    def test_writer_no_builder_import(self):
        writer_path = RUNTIME / "knowledge" / "writer.py"
        if not writer_path.exists():
            pytest.skip("runtime/knowledge/writer.py not yet created")
        source = writer_path.read_text(encoding="utf-8")
        modules = _imported_modules(source)
        for mod in modules:
            assert "runtime.builder" not in mod, (
                f"writer.py imports '{mod}' from runtime/builder/ -- "
                "Writer is a leaf; Builder uses Writer, not vice versa"
            )
