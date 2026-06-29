"""Demo script for Sprint 2.5 — Importer Runtime.

Runs the ImporterPipeline on a README fixture and prints the resulting
Artifact as serialized JSON. Proves the Importer is alive and working.

Usage:
    python scripts/demo_sprint25.py
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

# Ensure repo root is in sys.path (like conftest.py does for pytest)
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from runtime.importer.pipeline import ImporterPipeline


def main() -> int:
    # Path to the README fixture
    repo_root = Path(__file__).resolve().parent.parent
    readme_path = repo_root / "tests" / "fixtures" / "readme" / "sample-readme.md"

    if not readme_path.exists():
        print(f"ERROR: fixture not found at {readme_path}")
        print("Run: python tests/fixtures/_generate.py")
        return 1

    print(f"Running ImporterPipeline on: {readme_path}")
    print("=" * 60)

    # Run the pipeline
    pipeline = ImporterPipeline()
    try:
        artifact = pipeline.run(readme_path)
    except Exception as exc:
        print(f"Pipeline failed: {exc}")
        import traceback
        traceback.print_exc()
        return 1

    # Serialize and pretty-print
    raw_json = artifact.serialize()
    parsed = json.loads(raw_json)
    pretty = json.dumps(parsed, indent=2, ensure_ascii=False)

    print("\nArtifact (serialized):")
    print("-" * 60)
    print(pretty)
    print("-" * 60)

    # Summary
    print(f"\nSummary:")
    print(f"  artifact_type: {artifact.artifact_type}")
    print(f"  confidence:    {artifact.confidence}")
    print(f"  source_hash:   {artifact.provenance.sha256[:16]}...")
    print(f"  detected_type: {artifact.provenance.detected_type}")
    print(f"  extractor:     {artifact.provenance.extractor}")

    if hasattr(artifact, "title"):
        print(f"  title:         {artifact.title}")
    if hasattr(artifact, "tech_stack"):
        print(f"  tech_stack:    {artifact.tech_stack}")

    print("\n[PASS] Importer Runtime is alive and working.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
