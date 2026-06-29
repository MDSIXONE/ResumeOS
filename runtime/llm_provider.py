"""LLMProvider — the adapter interface for language models.

Sprint 4 prep (user directive): define the interface NOW, implement
later. The Runtime knows only ``LLMProvider``, never which concrete
model (Claude / OpenAI / DeepSeek / Gemini / Qwen) is behind it.

Rules:
    1. runtime/ imports ONLY this ABC — never a concrete provider.
    2. Concrete providers live in ``adapters/llm/`` (Sprint 4), injected
       at runtime via config or constructor.
    3. The ABC has no default implementation — providers must implement
       all three methods (generate, embed, summarize).
    4. This file has ZERO third-party imports (no anthropic, no openai).
       It is pure interface.

This is the seam that makes every LLM swappable without touching
runtime/, skills/, or importers/.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMProvider(ABC):
    """Abstract interface for language model providers.

    Concrete implementations (Sprint 4):
        adapters/llm/claude.py   -> class ClaudeProvider(LLMProvider)
        adapters/llm/openai.py   -> class OpenAIProvider(LLMProvider)
        adapters/llm/deepseek.py -> class DeepSeekProvider(LLMProvider)
        adapters/llm/qwen.py     -> class QwenProvider(LLMProvider)

    The runtime and skills reference ``LLMProvider`` only. Swapping
    providers is a config change, not a code change.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate text from a prompt.

        Returns the generated text string. Must be deterministic given
        the same inputs + temperature=0 (for testability).
        """
        ...

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate an embedding vector for the given text.

        Returns a list of floats. Dimension is provider-specific but
        consistent within a provider.
        """
        ...

    @abstractmethod
    def summarize(self, text: str, *, max_length: int = 500) -> str:
        """Summarize the given text.

        Returns a shorter text string preserving key information.
        """
        ...

    # ------------------------------------------------------------------
    # Optional capabilities (default to False — provider overrides)
    # ------------------------------------------------------------------

    @property
    def supports_vision(self) -> bool:
        """Whether this provider can process images."""
        return False

    @property
    def supports_tools(self) -> bool:
        """Whether this provider supports tool/function calling."""
        return False

    @property
    def name(self) -> str:
        """Provider name for logging (e.g. 'claude', 'openai')."""
        return self.__class__.__name__

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Verify the provider is reachable and configured.

        Default: return True. Providers override to ping their API.
        """
        return True
