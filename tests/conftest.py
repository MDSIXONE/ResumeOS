"""Pytest configuration for tests."""
from __future__ import annotations

import pytest

from adapters.llm.dummy import DummyLLMProvider


@pytest.fixture
def dummy_provider():
    """A DummyLLMProvider for testing."""
    return DummyLLMProvider()
