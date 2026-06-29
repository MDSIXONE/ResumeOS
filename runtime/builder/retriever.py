"""Retriever -- checks for existing entities in the knowledge base.

Before the Builder creates or updates an entity, the Retriever queries
the KnowledgeIndex and filesystem to see if an entity with the same
entity_type and entity_id already exists. This information is passed
to the Merger for conflict detection.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from runtime.knowledge.writer import KnowledgeWriter
from runtime.knowledge_index import KnowledgeIndex


class Retriever:
    """Retrieves existing entities from the knowledge base.

    Uses the KnowledgeWriter to read the existing .md file (if any)
    and the KnowledgeIndex to query for related entities.
    """

    def __init__(
        self, knowledge_index: KnowledgeIndex, writer: KnowledgeWriter
    ) -> None:
        """Initialize with a knowledge index and writer.

        Args:
            knowledge_index: The KnowledgeIndex for querying entities.
            writer: The KnowledgeWriter for reading existing .md files.
        """
        self.knowledge_index = knowledge_index
        self.writer = writer

    def retrieve(self, plan: Dict[str, Any], vault_root: Path) -> Dict[str, Any]:
        """Check for existing entity and related entities.

        Args:
            plan: The plan dict from the Planner stage.
            vault_root: Root of the Obsidian vault.

        Returns:
            dict with keys:
                - existing: Existing entity frontmatter dict, or None if new.
                - related: List of related entities from the index.
        """
        entity_type = plan["entity_type"]
        entity_id = plan["entity_id"]

        # 1. Check if entity already exists on disk
        existing = self.writer.read(entity_type, entity_id, vault_root)

        # 2. Query index for related entities (same type)
        related = self.knowledge_index.query(entity_type=entity_type)

        return {
            "existing": existing,
            "related": related,
        }
