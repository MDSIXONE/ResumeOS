"""Unit tests for runtime.knowledge_index (beyond acceptance tests).

Per ADR-0012: These tests verify KnowledgeIndex correctly scans the vault,
writes the JSON index, skips invalid files (README, no frontmatter, no id),
includes edges, handles multiple entity types, and is idempotent.
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from runtime.knowledge_index import KnowledgeIndex


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    """Set up a multi-entity vault for unit tests."""
    vault_root = tmp_path / "vault"
    # Create career subdirectories.
    for folder in [
        "projects",
        "awards",
        "skills",
        "jobs",
    ]:
        (vault_root / "career" / folder).mkdir(parents=True, exist_ok=True)

    # Library/index must exist for the fixture to mirror acceptance setup.
    (vault_root / ".library" / "index").mkdir(parents=True, exist_ok=True)

    # Project note 1
    (vault_root / "career" / "projects" / "proj-a.md").write_text(
        textwrap.dedent(
            """\
            ---
            id: proj-a
            type: project
            title: Project A
            tags: [AI, Python]
            ---
            # Project A
            """
        ),
        encoding="utf-8",
    )

    # Project note 2 (different tags)
    (vault_root / "career" / "projects" / "proj-b.md").write_text(
        textwrap.dedent(
            """\
            ---
            id: proj-b
            type: project
            title: Project B
            tags: [C++]
            ---
            # Project B
            """
        ),
        encoding="utf-8",
    )

    # Award note
    (vault_root / "career" / "awards" / "award-1.md").write_text(
        textwrap.dedent(
            """\
            ---
            id: award-1
            type: award
            title: Robotics Award 2024
            tags: [Robotics]
            ---
            # Award
            """
        ),
        encoding="utf-8",
    )

    # Skill note (missing explicit type but has id)
    (vault_root / "career" / "skills" / "skill-py.md").write_text(
        textwrap.dedent(
            """\
            ---
            id: skill-py
            title: Python
            tags: [Language]
            ---
            # Python
            """
        ),
        encoding="utf-8",
    )

    # Job note
    (vault_root / "career" / "jobs" / "job-1.md").write_text(
        textwrap.dedent(
            """\
            ---
            id: job-1
            type: job
            title: Senior Engineer
            tags: [Full-time]
            ---
            # Job
            """
        ),
        encoding="utf-8",
    )

    # README.md that must be skipped
    (vault_root / "career" / "projects" / "README.md").write_text(
        "---\nid: should-skip\ntitle: README\n---\n# Projects Index\n",
        encoding="utf-8",
    )

    # Note without frontmatter (must be skipped)
    (vault_root / "career" / "projects" / "plain.md").write_text(
        "# Plain Markdown\nNo frontmatter here.\n",
        encoding="utf-8",
    )

    # Note with frontmatter but missing id (must be skipped)
    (vault_root / "career" / "projects" / "no-id.md").write_text(
        textwrap.dedent(
            """\
            ---
            title: No ID Note
            tags: [misc]
            ---
            # No ID
            """
        ),
        encoding="utf-8",
    )

    return vault_root


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestKnowledgeIndexUnit:
    """Unit tests covering ADR-0012 rules."""

    def test_multiple_entity_types(self, vault: Path) -> None:
        """Builder indexes entities from different career/* folders."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()

        projects = idx.query(entity_type="project")
        awards = idx.query(entity_type="award")
        skills = idx.query(entity_type="skill")
        jobs = idx.query(entity_type="job")

        assert len(projects) == 2
        assert len(awards) == 1
        assert len(skills) == 1
        assert len(jobs) == 1

    def test_skip_readme(self, vault: Path) -> None:
        """README.md files are never indexed."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        # README had id: should-skip, ensure it is NOT present.
        projects = idx.query(entity_type="project")
        ids = [p["id"] for p in projects]
        assert "should-skip" not in ids

    def test_skip_no_frontmatter(self, vault: Path) -> None:
        """Files without frontmatter are skipped."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        projects = idx.query(entity_type="project")
        ids = [p["id"] for p in projects]
        assert "plain" not in ids

    def test_skip_missing_id(self, vault: Path) -> None:
        """Frontmatter without an id field is skipped."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        projects = idx.query(entity_type="project")
        ids = [p["id"] for p in projects]
        assert "no-id" not in ids

    def test_index_file_is_valid_json(self, vault: Path) -> None:
        """The written index is a valid JSON document."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        path = vault / ".library" / "index" / "knowledge-index.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_edges_structure_present(self, vault: Path) -> None:
        """The index always contains an edges object with outgoing/incoming."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        path = vault / ".library" / "index" / "knowledge-index.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "edges" in data
        assert "outgoing" in data["edges"]
        assert "incoming" in data["edges"]

    def test_all_nine_collections_present(self, vault: Path) -> None:
        """All 9 required entity type collections are present."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        path = vault / ".library" / "index" / "knowledge-index.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        expected = [
            "projects",
            "awards",
            "research",
            "skills",
            "jobs",
            "education",
            "competitions",
            "internships",
            "opensource",
        ]
        for coll in expected:
            assert coll in data["entities"], f"missing collection {coll}"
            assert isinstance(data["entities"][coll], list)

    def test_build_is_idempotent(self, vault: Path) -> None:
        """Building twice yields the same entity count and ids."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        first = idx.query()
        idx.build()
        second = idx.query()
        assert len(first) == len(second)
        assert sorted(e["id"] for e in first) == sorted(e["id"] for e in second)

    def test_query_returns_empty_when_no_index_file(self, tmp_path: Path) -> None:
        """query() returns [] when the index file does not exist."""
        vault = tmp_path / "empty_vault"
        vault.mkdir()
        idx = KnowledgeIndex(vault_root=vault)
        assert idx.query() == []
        assert idx.query(entity_type="project") == []

    def test_schema_version_and_built_at(self, vault: Path) -> None:
        """The index carries schema_version and built_at timestamp."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        path = vault / ".library" / "index" / "knowledge-index.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        assert data["built_at"]  # non-empty ISO timestamp

    def test_entity_count_matches(
        self, vault: Path
    ) -> None:
        """entity_count matches the sum of all collections."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        path = vault / ".library" / "index" / "knowledge-index.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        total = sum(
            len(v) for v in data["entities"].values()
        )
        assert data["entity_count"] == total

    def test_path_uses_forward_slashes(self, vault: Path) -> None:
        """Paths stored in entities use forward slashes (cross-platform)."""
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        projects = idx.query(entity_type="project")
        for p in projects:
            assert "\\" not in p["path"]
            assert "career/projects" in p["path"]

    def test_tags_default_to_empty_list(self, tmp_path: Path) -> None:
        """Frontmatter without tags should default to []."""
        vault = tmp_path / "vault"
        (vault / "career" / "projects").mkdir(parents=True)
        (vault / ".library" / "index").mkdir(parents=True)
        (vault / "career" / "projects" / "no-tags.md").write_text(
            "---\nid: no-tags\ntitle: No Tags\n---\n# No Tags\n",
            encoding="utf-8",
        )
        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        projects = idx.query(entity_type="project")
        assert len(projects) == 1
        assert projects[0]["tags"] == []
