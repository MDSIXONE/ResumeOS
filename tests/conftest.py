"""Pytest configuration for tests."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from adapters.llm.dummy import DummyLLMProvider

_FIXTURES_ROOT = Path(__file__).parent / "fixtures"
_GIT_FIXTURE = _FIXTURES_ROOT / "github" / "sample-repo"


def _ensure_git_fixture() -> None:
    """Ensure the git fixture repo has a .git directory.

    The fixture files (README.md, main.py) are committed to the ResumeOS
    repo, but the .git directory is NOT (it would be an embedded repo).
    On a fresh clone, we recreate it with a single commit so the git_log
    extractor has something to parse.
    """
    git_dir = _GIT_FIXTURE / ".git"
    if git_dir.exists():
        return
    _GIT_FIXTURE.mkdir(parents=True, exist_ok=True)
    env = {"GIT_AUTHOR_NAME": "Fixture", "GIT_AUTHOR_EMAIL": "fixture@test.local",
           "GIT_COMMITTER_NAME": "Fixture", "GIT_COMMITTER_EMAIL": "fixture@test.local",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}
    subprocess.run(["git", "init"], cwd=_GIT_FIXTURE, capture_output=True, env=env, check=True)
    subprocess.run(["git", "add", "-A"], cwd=_GIT_FIXTURE, capture_output=True, env=env, check=True)
    subprocess.run(["git", "commit", "-m", "Initial fixture commit"],
                   cwd=_GIT_FIXTURE, capture_output=True, env=env, check=True)


@pytest.fixture(scope="session", autouse=True)
def _git_fixture_ready():
    """Auto-create the git fixture before any tests run."""
    _ensure_git_fixture()
    yield


@pytest.fixture
def dummy_provider():
    """A DummyLLMProvider for testing."""
    return DummyLLMProvider()
