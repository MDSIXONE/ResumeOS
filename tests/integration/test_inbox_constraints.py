"""Sprint 3 CI constraints — enforced architectural boundaries.

These tests auto-enforce the user's Sprint 3 hard constraints:
    1. Inbox Orchestrator has ZERO file-parsing logic (no pypdf/docx/PIL).
       It may only call ImporterPipeline.run() — parsing is the Importer's job.
    2. Artifacts are IMMUTABLE — no setter methods, no mutation methods.
       Skills can only create Knowledge from Artifacts, never modify them.
    3. runtime/inbox/ does NOT import skills/ (dependency direction reaffirmed).
    4. runtime/ still has ZERO LLM SDK imports (reaffirmed from Sprint 1).

If any of these fail in CI, the PR is blocked — these are not conventions,
they are automated guardrails.
"""

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _python_files(root: Path):
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        yield p


def _imports_in(file_path: Path) -> list:
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


def _has_method(cls_node: ast.ClassDef, name: str) -> bool:
    for item in ast.walk(cls_node):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if item.name == name:
                return True
    return False


# ---------------------------------------------------------------------------
# 1. Inbox Orchestrator — ZERO file-parsing logic
# ---------------------------------------------------------------------------

class TestInboxNoParsing:
    """Inbox may only call ImporterPipeline.run(); no direct parsing imports."""

    FORBIDDEN_PARSING = ["pypdf", "docx", "PIL", "Pillow", "fitz", "pdfplumber"]

    def test_no_parsing_imports_in_inbox(self):
        inbox_dir = REPO_ROOT / "runtime" / "inbox"
        if not inbox_dir.exists():
            pytest.skip("runtime/inbox/ not yet created (Sprint 3)")
        violations = []
        for py in _python_files(inbox_dir):
            for imp in _imports_in(py):
                for kw in self.FORBIDDEN_PARSING:
                    if kw in imp:
                        violations.append(
                            f"{py.relative_to(REPO_ROOT)}: imports '{imp}'"
                        )
        assert not violations, (
            "runtime/inbox/ must not import file-parsing libraries "
            "(pypdf/docx/PIL). Inbox orchestrates; Importer parses:\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 2. Artifact Immutability — no setters, no mutation methods
# ---------------------------------------------------------------------------

class TestArtifactImmutability:
    """Artifacts are immutable — no setter methods, no mutation methods.

    Skills create Knowledge from Artifacts; they never modify the
    Artifact itself. This keeps Importers deterministic (same file →
    same Artifact, always).
    """

    MUTATION_PREFIXES = ("set_", "update_", "add_", "remove_", "delete_", "clear_")
    MUTATION_NAMES = {"mutate", "modify", "append_to", "pop", "remove"}

    def test_no_setter_methods_on_artifacts(self):
        art_dir = REPO_ROOT / "runtime" / "artifacts"
        if not art_dir.exists():
            pytest.skip("runtime/artifacts/ not yet created")
        violations = []
        for py in _python_files(art_dir):
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and "Artifact" in node.name:
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            name = item.name
                            if name.startswith("__") and name.endswith("__"):
                                continue  # dunder methods OK
                            if name.startswith("to_") or name == "serialize":
                                continue  # serialization OK
                            if name == "deserialize" or name == "from_dict":
                                continue  # construction OK
                            if any(name.startswith(p) for p in self.MUTATION_PREFIXES):
                                violations.append(
                                    f"{py.relative_to(REPO_ROOT)}: "
                                    f"{node.name}.{name}() looks like a setter"
                                )
                            if name in self.MUTATION_NAMES:
                                violations.append(
                                    f"{py.relative_to(REPO_ROOT)}: "
                                    f"{node.name}.{name}() looks like a mutation"
                                )
        assert not violations, (
            "Artifacts must be immutable — no setter/mutation methods:\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 3. runtime/inbox/ does NOT import skills/
# ---------------------------------------------------------------------------

class TestInboxDoesNotImportSkills:
    def test_no_skills_import_in_inbox(self):
        inbox_dir = REPO_ROOT / "runtime" / "inbox"
        if not inbox_dir.exists():
            pytest.skip("runtime/inbox/ not yet created (Sprint 3)")
        violations = []
        for py in _python_files(inbox_dir):
            for imp in _imports_in(py):
                if imp.startswith("skills"):
                    violations.append(
                        f"{py.relative_to(REPO_ROOT)}: imports '{imp}'"
                    )
        assert not violations, (
            "runtime/inbox/ must not import skills/ (dependency direction):\n"
            + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 4. runtime/ is still LLM-agnostic
# ---------------------------------------------------------------------------

class TestRuntimeStillLLMAgnostic:
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
