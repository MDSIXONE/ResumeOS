"""Knowledge Index — rebuildable JSON projection of vault career entities.

Per ADR-0012: The Knowledge Index is a read-only, rebuildable JSON file stored at
vault/.library/index/knowledge-index.json. The vault remains the source of truth;
the index is an optimization for read-heavy, filter-heavy operations.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Frontmatter regex — matches YAML between --- delimiters at the start of a file.
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Entity directory names under vault/career/ (order matches schema).
_ENTITY_DIRS: List[str] = [
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

# Mapping from folder name to singular entity type.
_FOLDER_TO_SINGULAR: Dict[str, str] = {
    "projects": "project",
    "awards": "award",
    "research": "research",
    "skills": "skill",
    "jobs": "job",
    "education": "education",
    "competitions": "competition",
    "internships": "internship",
    "opensource": "opensource",
}


def _parse_frontmatter(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse YAML frontmatter from a Markdown string.

    Returns None if no valid frontmatter block is found.
    """
    m = _FM_RE.match(text)
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    return data


class KnowledgeIndex:
    """Build and query the knowledge index for ResumeOS career entities.

    Per ADR-0012: Scans vault_root/career/** for Markdown notes with YAML
    frontmatter and produces a JSON index at
    vault_root/.library/index/knowledge-index.json.
    """

    def __init__(self, vault_root: Path) -> None:
        """Initialize with the vault root directory.

        Args:
            vault_root: Path to the vault directory containing career/,
                .library/, etc.
        """
        self.vault_root = Path(vault_root)
        self._index_path = (
            self.vault_root / ".library" / "index" / "knowledge-index.json"
        )
        self._index_data: Optional[Dict[str, Any]] = None

    def _scan(self) -> Dict[str, Any]:
        """Full scan of vault_root/career/**, parsing YAML frontmatter.

        Returns:
            The complete index dictionary ready for serialisation.
        """
        entities: Dict[str, List[Dict[str, Any]]] = {
            folder: [] for folder in _ENTITY_DIRS
        }

        career_dir = self.vault_root / "career"
        if career_dir.exists():
            for folder_name in _ENTITY_DIRS:
                folder_path = career_dir / folder_name
                if not folder_path.exists():
                    continue
                singular_type = _FOLDER_TO_SINGULAR[folder_name]

                for md_file in sorted(folder_path.rglob("*.md")):
                    # Skip README.md files.
                    if md_file.name == "README.md":
                        continue

                    try:
                        text = md_file.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        continue

                    fm = _parse_frontmatter(text)
                    if fm is None:
                        continue
                    if "id" not in fm:
                        continue

                    tags = fm.get("tags", [])
                    if tags is None:
                        tags = []

                    # Relative to vault_root, forward slashes (cross-platform).
                    rel_path_str = md_file.relative_to(self.vault_root).as_posix()

                    entity: Dict[str, Any] = {
                        "id": fm["id"],
                        "title": fm.get("title", ""),
                        "type": singular_type,
                        "tags": tags,
                        "path": rel_path_str,
                    }
                    entities[folder_name].append(entity)

        entity_count = sum(len(v) for v in entities.values())

        index_data: Dict[str, Any] = {
            "schema_version": "1.0",
            "built_at": datetime.now(timezone.utc).isoformat(),
            "entity_count": entity_count,
            "entities": entities,
            "edges": {"outgoing": {}, "incoming": {}},
        }
        return index_data

    def build(self) -> None:
        """Full scan and write the index to vault_root/.library/index/knowledge-index.json.

        Per ADR-0012: The index is a rebuildable projection of vault/career/**.
        Parent directories are created if they do not exist.
        """
        self._index_data = self._scan()
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._index_path.write_text(
            json.dumps(self._index_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def update(self) -> None:
        """Re-scan and update the index.

        Per ADR-0012: For Sprint 1, a full re-scan is acceptable; true
        incremental diff is a later optimisation.
        """
        self.build()

    def query(
        self,
        entity_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Query the in-memory index.

        Args:
            entity_type: Filter by entity type (e.g. ``"project"`` matches
                entities whose ``type`` field is ``"project"``).
            tags: If given, return only entities whose tags list contains
                ALL specified tags.

        Returns:
            List of matching entity summaries.  Empty list if no index is
            loaded or the index file does not exist on disk.
        """
        # Lazy-load from disk if needed.
        if self._index_data is None:
            if not self._index_path.exists():
                return []
            try:
                self._index_data = json.loads(
                    self._index_path.read_text(encoding="utf-8")
                )
            except (json.JSONDecodeError, OSError):
                return []

        entities_dict = self._index_data.get("entities", {})
        results: List[Dict[str, Any]] = []

        for _collection_name, collection in entities_dict.items():
            if not isinstance(collection, list):
                continue
            for entity in collection:
                # Filter by entity type.
                if entity_type is not None and entity.get("type") != entity_type:
                    continue
                # Filter by tags (AND logic: all requested tags must be present).
                if tags is not None:
                    entity_tags = entity.get("tags", [])
                    if not all(t in entity_tags for t in tags):
                        continue
                results.append(entity)

        return results
