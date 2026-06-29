"""ResumeOS provenance test.

Enforces the anti-hallucination contract (ADR-0007): every bullet in a derived resume assembly
must cite provenance that references an entity_id that exists in the vault.

Loads each examples/output/**/artifacts/assembly.json and asserts:
- Every bullet has a non-empty provenance array.
- Each provenance citation references an entity_id that exists in examples/vault/.

A bullet without provenance is a build failure, not a warning.
"""

import json
import re
from pathlib import Path
from typing import Dict, Iterator, Optional, Set, Tuple

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_VAULT = REPO_ROOT / "examples" / "vault"
EXAMPLES_OUTPUT = REPO_ROOT / "examples" / "output"


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(md_text: str) -> Tuple[Optional[Dict], Optional[str]]:
    m = _FM_RE.match(md_text)
    if not m:
        return None, "No frontmatter"
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return None, f"YAML error: {e}"
    if not isinstance(data, dict):
        return None, "Frontmatter not a dict"
    return data, None


# ---------------------------------------------------------------------------
# Vault entity index
# ---------------------------------------------------------------------------
def iter_vault_notes() -> Iterator[Path]:
    if not EXAMPLES_VAULT.is_dir():
        return
    for md in EXAMPLES_VAULT.rglob("*.md"):
        if md.is_file() and md.name.lower() != "readme.md":
            yield md


def collect_entity_ids() -> Set[str]:
    """Collect all entity IDs from examples/vault. An entity ID is the 'id' field in frontmatter."""
    ids: Set[str] = set()
    for note in iter_vault_notes():
        rel = note.relative_to(EXAMPLES_VAULT)
        if any(p.startswith(".") for p in rel.parts):
            continue
        frontmatter, err = parse_frontmatter(note.read_text(encoding="utf-8"))
        if err is not None or frontmatter is None:
            continue
        eid = frontmatter.get("id")
        if eid and isinstance(eid, str):
            ids.add(eid)
    return ids


# ---------------------------------------------------------------------------
# Assembly discovery
# ---------------------------------------------------------------------------
def iter_assembly_artifacts() -> Iterator[Path]:
    if not EXAMPLES_OUTPUT.is_dir():
        return
    yield from EXAMPLES_OUTPUT.rglob("artifacts/assembly.json")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "assembly_path",
    list(iter_assembly_artifacts()),
    ids=lambda p: str(p.relative_to(EXAMPLES_OUTPUT)),
)
def test_assembly_bullets_have_provenance(assembly_path: Path) -> None:
    """Every bullet in assembly.json must have a non-empty provenance array."""
    data = json.loads(assembly_path.read_text(encoding="utf-8"))

    for section_idx, section in enumerate(data.get("sections", [])):
        for item_idx, item in enumerate(section.get("items", [])):
            entity_id = item.get("entity_id", "<unknown>")
            for bullet_idx, bullet in enumerate(item.get("bullets", [])):
                provenance = bullet.get("provenance")
                assert provenance is not None, (
                    f"{assembly_path.relative_to(EXAMPLES_OUTPUT)}: "
                    f"section[{section_idx}].items[{item_idx}] (entity_id={entity_id}).bullets[{bullet_idx}] "
                    f"has no 'provenance' field"
                )
                assert isinstance(provenance, list), (
                    f"{assembly_path.relative_to(EXAMPLES_OUTPUT)}: "
                    f"section[{section_idx}].items[{item_idx}] (entity_id={entity_id}).bullets[{bullet_idx}].provenance "
                    f"is not a list"
                )
                assert len(provenance) > 0, (
                    f"{assembly_path.relative_to(EXAMPLES_OUTPUT)}: "
                    f"section[{section_idx}].items[{item_idx}] (entity_id={entity_id}).bullets[{bullet_idx}].provenance "
                    f"is empty (anti-hallucination violation — ADR-0007)"
                )


@pytest.mark.parametrize(
    "assembly_path",
    list(iter_assembly_artifacts()),
    ids=lambda p: str(p.relative_to(EXAMPLES_OUTPUT)),
)
def test_assembly_provenance_references_existing_entities(assembly_path: Path) -> None:
    """Every provenance citation must reference an entity_id that exists in examples/vault/."""
    vault_entity_ids = collect_entity_ids()
    data = json.loads(assembly_path.read_text(encoding="utf-8"))

    missing_refs = []
    for section_idx, section in enumerate(data.get("sections", [])):
        for item_idx, item in enumerate(section.get("items", [])):
            entity_id = item.get("entity_id", "<unknown>")
            for bullet_idx, bullet in enumerate(item.get("bullets", [])):
                provenance = bullet.get("provenance", [])
                for citation in provenance:
                    # Citation format: "entity_id:field" or just "entity_id"
                    if isinstance(citation, str) and ":" in citation:
                        cited_entity_id = citation.split(":")[0]
                    else:
                        cited_entity_id = citation
                    if cited_entity_id not in vault_entity_ids:
                        missing_refs.append(
                            f"  - {assembly_path.relative_to(EXAMPLES_OUTPUT)}: "
                            f"section[{section_idx}].items[{item_idx}] (entity_id={entity_id}).bullets[{bullet_idx}].provenance "
                            f"cites '{cited_entity_id}' which does not exist in examples/vault/"
                        )

    assert not missing_refs, (
        "Anti-hallucination violation (ADR-0007): provenance references non-existent entities:\n"
        + "\n".join(missing_refs)
    )


def test_examples_vault_exists() -> None:
    """Sanity check: examples/vault/ must exist for provenance tests to run."""
    assert EXAMPLES_VAULT.is_dir(), "examples/vault/ does not exist"
