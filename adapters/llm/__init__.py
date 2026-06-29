"""LLM adapter implementations.

Each file implements LLMProvider from runtime/llm_provider.py:
    dummy.py   -> DummyLLMProvider  (deterministic, for tests)
    claude.py  -> ClaudeProvider    (Sprint 5+, real API)
    openai.py  -> OpenAIProvider    (Sprint 5+, real API)
    ...

The runtime never imports from this directory -- it receives a
LLMProvider instance via dependency injection.
"""

from adapters.llm.dummy import DummyLLMProvider

__all__ = ["DummyLLMProvider"]
