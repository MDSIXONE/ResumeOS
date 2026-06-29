"""Sprint 3 — LLMProvider interface test.

Verifies the adapter interface is defined and usable without any
concrete provider. The Runtime knows only LLMProvider, never which
model is behind it. A dummy provider proves the interface works.
"""

import pytest

from runtime.llm_provider import LLMProvider


class DummyProvider(LLMProvider):
    """A no-op provider for testing — no network, no API key."""

    def generate(self, prompt, *, system="", max_tokens=4096,
                 temperature=0.7, **kwargs):
        return f"[dummy] {prompt[:50]}"

    def embed(self, text):
        return [0.1, 0.2, 0.3]

    def summarize(self, text, *, max_length=500):
        return text[:max_length]


class TestLLMProvider:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            LLMProvider()

    def test_dummy_provider_implements_interface(self):
        p = DummyProvider()
        assert p.generate("hello world") == "[dummy] hello world"
        assert p.embed("test") == [0.1, 0.2, 0.3]
        assert p.summarize("long text") == "long text"

    def test_default_capabilities(self):
        p = DummyProvider()
        assert p.supports_vision is False
        assert p.supports_tools is False
        assert p.health_check() is True

    def test_name_property(self):
        p = DummyProvider()
        assert p.name == "DummyProvider"

    def test_runtime_references_only_abc(self):
        """runtime/ imports LLMProvider (the ABC), never a concrete provider."""
        import ast
        from pathlib import Path
        repo_root = Path(__file__).resolve().parent.parent.parent
        runtime_dir = repo_root / "runtime"
        violations = []
        for py in runtime_dir.rglob("*.py"):
            if "__pycache__" in py.parts:
                continue
            tree = ast.parse(py.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ("anthropic", "openai"):
                            violations.append(f"{py}: imports {alias.name}")
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module in ("anthropic", "openai"):
                        violations.append(f"{py}: imports {node.module}")
        assert not violations, (
            "runtime/ must not import concrete LLM providers:\n"
            + "\n".join(violations)
        )
