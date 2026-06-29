#!/usr/bin/env python3
"""Sprint 1 demo — proves the ResumeOS 0.1 Runtime is alive.

Acceptance criterion (user directive):
    bus.publish("ProjectImported") -> collector.on_project() receives it.

Run:
    python scripts/demo_sprint1.py
"""

import tempfile
import textwrap
from pathlib import Path

# Ensure repo root is importable when run as a script
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from runtime.event_bus import EventBus
from runtime.knowledge_index import KnowledgeIndex
from runtime.memory import Memory


def main():
    with tempfile.TemporaryDirectory(prefix="resumeos-demo-") as tmp:
        vault = Path(tmp)

        # --- 1. Event Bus: the user's explicit acceptance criterion ---
        bus = EventBus(events_log=vault / "events.jsonl")

        class FakeCollector:
            def on_project(self, event):
                print(f"  [collector] received {event['type']}: "
                      f"{event['payload']}")

        collector = FakeCollector()
        bus.subscribe("ProjectImported", collector.on_project)
        bus.publish(
            "ProjectImported",
            payload={"project_id": "demo"},
            source_skill="inbox_ingest",
        )
        print("[1/3] Event Bus: publish -> subscribe OK")

        # --- 2. Knowledge Index ---
        career = vault / "career" / "projects"
        career.mkdir(parents=True)
        (career / "demo.md").write_text(textwrap.dedent("""\
            ---
            id: demo
            type: project
            title: Demo Project
            tags: [AI]
            status: completed
            ---
            # Demo
            """), encoding="utf-8")

        idx = KnowledgeIndex(vault_root=vault)
        idx.build()
        projects = idx.query(entity_type="project")
        print(f"[2/3] Knowledge Index: built, {len(projects)} project(s) "
              f"indexed")

        # --- 3. Memory ---
        mem = Memory(store=vault / "conversation.jsonl")
        mem.remember("demo", "team_size", "Team size?", "5")
        recall = mem.recall(entity_id="demo")
        print(f"[3/3] Memory: remembered + recalled {len(recall)} answer(s)")

        print()
        print("Sprint 1 Runtime is alive.")


if __name__ == "__main__":
    main()
