"""Demo script for Sprint 4 -- Career Builder Pipeline.

Runs the full pipeline:
    README -> Importer -> Artifact -> Builder Pipeline -> .md -> Events

Usage:
    python scripts/demo_sprint4.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Ensure repo root is in sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from adapters.llm.dummy import DummyLLMProvider
from runtime.builder.merger import Merger
from runtime.builder.planner import Planner
from runtime.builder.pipeline import BuilderPipeline
from runtime.builder.retriever import Retriever
from runtime.builder.validator import Validator
from runtime.event_bus import EventBus
from runtime.importer.pipeline import ImporterPipeline
from runtime.knowledge.writer import MarkdownWriter
from runtime.knowledge_index import KnowledgeIndex


def main() -> int:
    # Locate fixture
    readme_path = repo_root / "tests" / "fixtures" / "readme" / "sample-readme.md"
    if not readme_path.exists():
        print(f"ERROR: fixture not found at {readme_path}")
        return 1

    print("=" * 60)
    print("  Sprint 4 Career Builder Demo")
    print("  README -> Importer -> Builder -> .md -> Events")
    print("=" * 60)

    # 1. Run Importer Pipeline on the README fixture
    print("\n[1] Running Importer Pipeline on README fixture...")
    importer = ImporterPipeline()
    try:
        artifact = importer.run(readme_path)
    except Exception as exc:
        print(f"    Importer failed: {exc}")
        return 1

    print(f"    [x] Artifact type:  {artifact.artifact_type}")
    if hasattr(artifact, "title"):
        print(f"    [x] Title:        {artifact.title}")
    if hasattr(artifact, "tech_stack"):
        print(f"    [x] Tech stack:   {artifact.tech_stack}")
    print(f"    [x] SHA-256:      {artifact.source_sha256[:16]}...")

    # 2. Build the Builder Pipeline with DummyLLMProvider
    vault_root = Path(tempfile.mkdtemp(prefix="resumeos_s4_"))
    (vault_root / "career" / "projects").mkdir(parents=True)
    (vault_root / ".library" / "index").mkdir(parents=True)

    bus = EventBus(events_log=vault_root / ".library" / "events.jsonl")
    idx = KnowledgeIndex(vault_root=vault_root)
    writer = MarkdownWriter()

    pipeline = BuilderPipeline(
        planner=Planner(),
        retriever=Retriever(knowledge_index=idx, writer=writer),
        llm=DummyLLMProvider(),
        validator=Validator(schemas_root=repo_root / "schemas"),
        merger=Merger(),
        writer=writer,
        event_bus=bus,
        knowledge_index=idx,
    )

    # 3. Run the Builder Pipeline
    print("\n[2] Running Builder Pipeline...")
    result = pipeline.run(artifact=artifact, vault_root=vault_root)

    if not result.success:
        print(f"    [x] FAILED: {result.error}")
        return 1

    # 4. Print stage outputs
    print(f"    [x] Plan: entity_type={result.knowledge_object.entity_type}, "
          f"entity_id={result.knowledge_object.entity_id}")

    # Draft
    print(f"    [x] Draft: raw_output (first 200 chars):")
    print(f"        {result.draft.raw_output[:200]}...")

    # Validation
    print(f"    [x] Validation: {'PASSED' if result.draft.is_valid else 'FAILED'}")

    # Knowledge Object
    ko = result.knowledge_object
    print(f"    [x] Knowledge: entity_id={ko.entity_id}")
    print(f"        fields keys: {list(ko.fields.keys())}")

    # Markdown
    text = result.written_path.read_text(encoding="utf-8")
    first_lines = text.split("\n")[:5]
    print(f"    [x] Markdown written: {result.written_path}")
    for line in first_lines:
        print(f"        {line}")

    # Events
    print(f"    [x] Events published: {result.events_published}")

    # Knowledge Index
    idx2 = KnowledgeIndex(vault_root=vault_root)
    projects = idx2.query(entity_type="project")
    print(f"    [x] Knowledge Index query: {len(projects)} project(s) found")

    # 5. Conflicts (if any)
    if result.conflicts:
        print(f"\n[3] Conflicts detected: {len(result.conflicts)}")
        for c in result.conflicts:
            print(f"    - {c.field}: existing='{c.existing_value}' vs new='{c.new_value}'")
    else:
        print("\n[3] No conflicts (clean merge).")

    print("\n" + "=" * 60)
    print("[PASS] Sprint 4 Career Builder is alive.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
