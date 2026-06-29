"""Architecture constraint test — dependency direction.

Enforces the user's most important principle:
    "No component may directly depend on downstream components."

    Importer  ──does not know──>  Career Builder
    Career Builder  ──does not know──>  Resume Builder
    Resume Builder  ──does not know──>  Cover Letter

    Components communicate ONLY through:
        - Event Bus
        - Artifact
        - Knowledge Base

This test scans source code for forbidden imports and fails CI if any
component reaches across the dependency boundary. It is the automated
guardrail for the principle — not a human-memory rule.

Rules checked:
    1. runtime/ does NOT import anything from skills/
    2. runtime/artifacts/ does NOT import from runtime/importer/ or skills/
    3. runtime/importer/ does NOT import from skills/
    4. runtime/ does NOT import any LLM SDK (reaffirms Sprint 1 rule)
"""

import ast
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _python_files(root: Path):
    """Yield all .py files under root, excluding __pycache__."""
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        yield p


def _imports_in(file_path: Path) -> list:
    """Return a list of imported module names (top-level + alias)."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


# ---------------------------------------------------------------------------
# 1. runtime/ does NOT import skills/
# ---------------------------------------------------------------------------

class TestRuntimeDoesNotImportSkills:
    """runtime/ is infrastructure; it must not depend on skills/."""

    def test_no_skills_import_in_runtime(self):
        runtime_dir = REPO_ROOT / "runtime"
        if not runtime_dir.exists():
            pytest.skip("runtime/ not yet created")
        violations = []
        for py in _python_files(runtime_dir):
            for imp in _imports_in(py):
                if imp.startswith("skills") or imp.startswith("skills."):
                    violations.append(f"{py.relative_to(REPO_ROOT)}: imports '{imp}'")
        assert not violations, (
            "runtime/ must not import skills/ (dependency direction):\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 2. runtime/artifacts/ is a leaf — no importer or skills imports
# ---------------------------------------------------------------------------

class TestArtifactsAreLeafContract:
    """Artifacts are depended ON, never depend towards consumers."""

    def test_no_importer_import_in_artifacts(self):
        art_dir = REPO_ROOT / "runtime" / "artifacts"
        if not art_dir.exists():
            pytest.skip("runtime/artifacts/ not yet created")
        violations = []
        for py in _python_files(art_dir):
            for imp in _imports_in(py):
                if "importer" in imp:
                    violations.append(f"{py.relative_to(REPO_ROOT)}: imports '{imp}'")
        assert not violations, (
            "runtime/artifacts/ must not import runtime/importer/ (leaf contract):\n"
            + "\n".join(violations)
        )

    def test_no_skills_import_in_artifacts(self):
        art_dir = REPO_ROOT / "runtime" / "artifacts"
        if not art_dir.exists():
            pytest.skip("runtime/artifacts/ not yet created")
        violations = []
        for py in _python_files(art_dir):
            for imp in _imports_in(py):
                if imp.startswith("skills"):
                    violations.append(f"{py.relative_to(REPO_ROOT)}: imports '{imp}'")
        assert not violations, (
            "runtime/artifacts/ must not import skills/ (leaf contract):\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 3. runtime/importer/ does NOT import skills/
# ---------------------------------------------------------------------------

class TestImporterDoesNotImportSkills:
    """Importers produce Artifacts; they never reach into Skills."""

    def test_no_skills_import_in_importer(self):
        imp_dir = REPO_ROOT / "runtime" / "importer"
        if not imp_dir.exists():
            pytest.skip("runtime/importer/ not yet created (Sprint 2.5)")
        violations = []
        for py in _python_files(imp_dir):
            for imp in _imports_in(py):
                if imp.startswith("skills"):
                    violations.append(f"{py.relative_to(REPO_ROOT)}: imports '{imp}'")
        assert not violations, (
            "runtime/importer/ must not import skills/ (dependency direction):\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 4. runtime/ is LLM-agnostic (reaffirms Sprint 1 rule)
# ---------------------------------------------------------------------------

class TestRuntimeIsLLMAgnostic:
    """No runtime/ file may import an LLM SDK."""

    FORBIDDEN = [
        "anthropic", "openai", "google.generativeai", "dashscope",
        "qwen", "deepseek", "zhipuai", "litellm", "langchain",
    ]

    def test_no_llm_sdk_in_runtime(self):
        runtime_dir = REPO_ROOT / "runtime"
        if not runtime_dir.exists():
            pytest.skip("runtime/ not yet created")
        violations = []
        for py in _python_files(runtime_dir):
            for imp in _imports_in(py):
                for kw in self.FORBIDDEN:
                    if kw in imp.lower():
                        violations.append(
                            f"{py.relative_to(REPO_ROOT)}: imports '{imp}'"
                        )
        assert not violations, (
            "runtime/ must not import any LLM SDK (LLM-agnostic):\n"
            + "\n".join(violations)
        )
