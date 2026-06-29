"""AI Memory — append-only conversation store for ResumeOS runtime.

Per ADR-0020: Memory stores user-confirmed answers as JSON Lines
(conversation.jsonl). Confidence is ALWAYS "confirmed" — only confirmed
answers are recorded. The store is append-only; no entries are ever deleted
or overwritten.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class Memory:
    """Append-only conversation memory for ResumeOS AI workflows.

    Per ADR-0020: each entry records a user-confirmed Q&A pair scoped to an
    entity and topic.  Entries are written as JSON Lines to
    ``conversation.jsonl`` and are never deleted.
    """

    def __init__(self, store: Path) -> None:
        """Initialize with the path to the conversation JSONL file.

        Args:
            store: Path to ``conversation.jsonl`` (created on first write).
        """
        self.store = Path(store)

    def remember(
        self,
        entity_id: str,
        topic: str,
        question: str,
        answer: str,
    ) -> None:
        """Append a confirmed conversation entry to the store.

        Per ADR-0020: confidence is ALWAYS ``"confirmed"``. Only
        user-confirmed answers are stored.

        Args:
            entity_id: The career entity this Q&A relates to (e.g. project id).
            topic: Short topic key (e.g. ``"team_size"``, ``"metrics"``).
            question: The question that was asked.
            answer: The user-confirmed answer.
        """
        entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entity_id": entity_id,
            "topic": topic,
            "question": question,
            "answer": answer,
            "confidence": "confirmed",
        }

        # Ensure parent directories exist.
        self.store.parent.mkdir(parents=True, exist_ok=True)

        # Append a single JSON line.
        with self.store.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def recall(
        self,
        entity_id: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query past conversation entries.

        Args:
            entity_id: If given, filter by entity id.
            topic: If given, filter by topic.

        Returns:
            Matching entries in insertion order.  Empty list if the store
            file does not exist.
        """
        if not self.store.exists():
            return []

        results: List[Dict[str, Any]] = []
        try:
            lines = self.store.read_text(encoding="utf-8").strip().split("\n")
        except OSError:
            return []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Apply filters.
            if entity_id is not None and entry.get("entity_id") != entity_id:
                continue
            if topic is not None and entry.get("topic") != topic:
                continue

            results.append(entry)

        return results
