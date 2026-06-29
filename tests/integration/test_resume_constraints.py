"""Sprint 5 CI-enforced architecture constraints.

Per user directive (Sprint 5 review):
    1. Resume pipeline MUST NOT import any LLM SDK (no LLM in assembly)
    2. Resume pipeline MUST NOT modify Knowledge (Tailoring = projection, not mutation)
    3. runtime/resume/ MUST NOT import skills/ (dependency direction)
    4. runtime/resume/ MUST NOT import runtime/builder/ (dependency direction)
    5. Renderer MUST be a leaf (only imports runtime/resume/ir.py, nothing upstream)

These are NOT human conventions — they are automated CI guardrails.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import List, Set

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

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


def _imported_modules(source: str) -> Set[str]:
    """Extract all imported module names from Python source via AST."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()

    modules: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
                # Also add full path for dotted checks
                modules.add(node.module.split(".")[0])
    return modules


def _scan_dir(dir_path: Path, forbidden: List[str], label: str) -> List[str]:
    """Scan all .py files in a directory for forbidden import keywords.

    Uses AST to check IMPORTS only (not docstrings/comments) to avoid
    false positives from documentation mentioning LLM names.
    """
    violations: List[str] = []
    if not dir_path.exists():
        return violations  # Directory not yet created — skip gracefully

    for py_file in dir_path.rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        imported = _imported_modules(source)
        for keyword in forbidden:
            for mod in imported:
                if keyword in mod.lower():
                    violations.append(
                        f"{label}: {py_file.relative_to(REPO_ROOT)} imports '{mod}' "
                        f"(matches forbidden '{keyword}')"
                    )
    return violations


# ---------------------------------------------------------------------------
# 1. No LLM in Resume Assembly
# ---------------------------------------------------------------------------

class TestResumeDoesNotImportLLM:
    """runtime/resume/ must NOT import any LLM SDK.

    The assembly pipeline is pure rules: keyword matching, scoring, layout.
    LLM is only for optional bullet rewriting (via Sprint 4 Draft->Validator).
    """

    def test_no_llm_sdk_imports(self):
        resume_dir = REPO_ROOT / "runtime" / "resume"
        if not resume_dir.exists():
            pytest.skip("runtime/resume/ not yet created")
            return

        violations = _scan_dir(resume_dir, _LLM_SDKS, "resume")
        assert violations == [], (
            "runtime/resume/ imports LLM SDKs — assembly must be LLM-agnostic:\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 2. No Knowledge Mutation
# ---------------------------------------------------------------------------

class TestResumeDoesNotMutateKnowledge:
    """runtime/resume/ must NOT call KnowledgeWriter.write() or similar mutation methods.

    The resume pipeline READS Knowledge (via KnowledgeIndex.query) but never
    WRITES to it. Tailoring produces a ResumeIR, not a Knowledge mutation.
    """

    def test_no_writer_write_calls(self):
        resume_dir = REPO_ROOT / "runtime" / "resume"
        if not resume_dir.exists():
            pytest.skip("runtime/resume/ not yet created")
            return

        violations: List[str] = []
        for py_file in resume_dir.rglob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                # Look for .write( calls on any object (knowledge writer pattern)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in ("write", "save", "commit", "update_entity"):
                        # Check if the call is on a writer-like object
                        # (we can't fully resolve types via AST, so we flag
                        #  any .write() call and let the developer verify)
                        # Exception: render_to_file writes to OUTPUT files,
                        # not to Knowledge — so we skip method names that
                        # contain 'render' or 'file'.
                        full_name = ast.dump(node.func)
                        if "render" in full_name.lower() or "file" in full_name.lower():
                            continue
                        # Also skip render_to_file and render_to_dir (Renderer methods)
                        if hasattr(node.func, 'attr') and node.func.attr in (
                            "render_to_file", "render_to_dir"
                        ):
                            continue
                        # Flag knowledge-mutation patterns
                        if node.func.attr in ("write", "save", "commit"):
                            violations.append(
                                f"{py_file.relative_to(REPO_ROOT)}: "
                                f"calls .{node.func.attr}() — "
                                "resume pipeline must not write to Knowledge"
                            )

        # We allow serialize() on ResumeIR (that writes the IR, not Knowledge)
        # Filter out false positives: serialize is on ResumeIR, not Knowledge
        real_violations = [v for v in violations if "serialize" not in v]
        assert real_violations == [], (
            "runtime/resume/ calls write/save/commit — "
            "must not mutate Knowledge:\n" + "\n".join(real_violations)
        )


# ---------------------------------------------------------------------------
# 3. No skills/ imports
# ---------------------------------------------------------------------------

class TestResumeDoesNotImportSkills:
    """runtime/resume/ must NOT import from skills/.

    Dependency direction: skills/ depend on runtime/, not the reverse.
    Resume is a runtime subsystem; it must not import skill implementations.
    """

    def test_no_skills_imports(self):
        resume_dir = REPO_ROOT / "runtime" / "resume"
        if not resume_dir.exists():
            pytest.skip("runtime/resume/ not yet created")
            return

        violations: List[str] = []
        for py_file in resume_dir.rglob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            imported = _imported_modules(source)
            for mod in imported:
                if mod == "skills" or mod.startswith("skills."):
                    violations.append(
                        f"{py_file.relative_to(REPO_ROOT)} imports '{mod}'"
                    )
        assert violations == [], (
            "runtime/resume/ imports skills/ — dependency direction violation:\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 4. No builder/ imports
# ---------------------------------------------------------------------------

class TestResumeDoesNotImportBuilder:
    """runtime/resume/ must NOT import from runtime/builder/.

    Builder produces Knowledge; Resume consumes Knowledge. They are siblings
    under runtime/, but Resume must not depend on Builder's implementation.
    The only shared contract is the Knowledge data (via KnowledgeIndex).
    """

    def test_no_builder_imports(self):
        resume_dir = REPO_ROOT / "runtime" / "resume"
        if not resume_dir.exists():
            pytest.skip("runtime/resume/ not yet created")
            return

        violations: List[str] = []
        for py_file in resume_dir.rglob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            imported = _imported_modules(source)
            for mod in imported:
                if "builder" in mod:
                    violations.append(
                        f"{py_file.relative_to(REPO_ROOT)} imports '{mod}'"
                    )
        assert violations == [], (
            "runtime/resume/ imports builder/ — "
            "Resume must consume Knowledge, not Builder:\n" + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 5. Renderer is a leaf
# ---------------------------------------------------------------------------

class TestRendererIsLeaf:
    """Renderer only imports runtime/resume/ir.py — nothing upstream.

    The Renderer is the final step: ResumeIR -> output format.
    It must not import Selector, Ranker, Layout, Pipeline, or anything
    that produces ResumeIR. It only consumes ResumeIR.
    """

    def test_renderer_only_imports_ir(self):
        renderer_dir = REPO_ROOT / "runtime" / "resume" / "renderer"
        if not renderer_dir.exists():
            pytest.skip("runtime/resume/renderer/ not yet created")
            return

        allowed = {"runtime.resume.ir", "runtime.resume.renderer.base", "runtime.resume"}
        violations: List[str] = []
        for py_file in renderer_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            source = py_file.read_text(encoding="utf-8")
            imported = _imported_modules(source)
            for mod in imported:
                if mod.startswith("runtime.resume") and mod not in allowed:
                    violations.append(
                        f"{py_file.relative_to(REPO_ROOT)} imports '{mod}' "
                        f"(renderer should only import {allowed})"
                    )
        assert violations == [], (
            "Renderer imports non-IR modules — must be a leaf:\n"
            + "\n".join(violations)
        )
