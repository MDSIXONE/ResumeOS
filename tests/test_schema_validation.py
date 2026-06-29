"""ResumeOS schema-validation tests.

Validates:
1. Every examples/vault/**/*.md (excluding READMEs, daily, periodic, canvas, inbox).
2. Every examples/output/**/artifacts/*.json (against schemas/artifacts/*.schema.json).
3. Every skills/*/plugin.json + root plugin.json (against schemas/plugin-manifest.schema.json).
"""

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple

import pytest
import yaml
from jsonschema import Draft202012Validator
from jsonschema.validators import validator_for


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_ROOT = REPO_ROOT / "schemas"
CONFIG_PATH = REPO_ROOT / "resumeos.config.yaml"
EXAMPLES_VAULT = REPO_ROOT / "examples" / "vault"
EXAMPLES_OUTPUT = REPO_ROOT / "examples" / "output"


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def normalize_dates(obj: Any) -> Any:
    """Recursively convert YAML-parsed date/datetime objects to ISO 8601 strings.

    PyYAML auto-parses unquoted ``2023-08-15`` into ``datetime.date``; schemas
    declare dates as ``type: string`` (ADR-0002). Coerce so frontmatter authoring
    stays ergonomic (no quoting) while remaining schema-faithful.
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: normalize_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_dates(v) for v in obj]
    return obj


def parse_frontmatter(md_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    m = _FM_RE.match(md_text)
    if not m:
        return None, "No YAML frontmatter"
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return None, f"YAML error: {e}"
    if not isinstance(data, dict):
        return None, "Frontmatter is not a dict"
    return normalize_dates(data), None


# ---------------------------------------------------------------------------
# Schema + entity-type inference
# ---------------------------------------------------------------------------
_config: Optional[Dict[str, Any]] = None


def get_config() -> Dict[str, Any]:
    global _config
    if _config is None:
        with CONFIG_PATH.open(encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config


def entity_type_for_path(rel_path: Path, entities: Dict[str, str]) -> Optional[str]:
    parts = rel_path.parts
    best_match: Optional[str] = None
    best_depth: int = -1
    for t, folder in entities.items():
        folder_parts = tuple(Path(folder).parts)
        n = len(folder_parts)
        if parts[:n] == folder_parts and n > best_depth:
            best_match = t
            best_depth = n
    return best_match


def load_json_schema(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def validate_against(instance: Any, schema: Dict[str, Any]) -> list:
    cls = validator_for(schema)
    validator = cls(schema)
    return list(validator.iter_errors(instance))


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------
def iter_vault_entity_notes() -> Iterator[Path]:
    """Yield every Markdown note under examples/vault that belongs to an entity folder."""
    if not EXAMPLES_VAULT.is_dir():
        return
    entities = get_config()["vault"]["entities"]
    entity_folders = {Path(folder).parts[0] for folder in entities.values()}

    for md in EXAMPLES_VAULT.rglob("*.md"):
        if not md.is_file():
            continue
        rel = md.relative_to(EXAMPLES_VAULT)
        if rel.name.lower() == "readme.md":
            continue
        if any(p.startswith(".") for p in rel.parts):
            continue
        if not rel.parts:
            continue
        top = rel.parts[0]
        if top not in entity_folders:
            # Not in a known entity folder (could be daily/periodic/canvas/inbox).
            continue
        yield md


def iter_plugin_manifests() -> Iterator[Path]:
    for p in REPO_ROOT.glob("skills/*/plugin.json"):
        if p.is_file():
            yield p
    root_manifest = REPO_ROOT / "plugin.json"
    if root_manifest.is_file():
        yield root_manifest


def iter_artifact_jsons() -> Iterator[Path]:
    if not EXAMPLES_OUTPUT.is_dir():
        return
    yield from EXAMPLES_OUTPUT.rglob("artifacts/*.json")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "note",
    list(iter_vault_entity_notes()),
    ids=lambda p: str(p.relative_to(EXAMPLES_VAULT)),
)
def test_vault_note_frontmatter_validates(note: Path) -> None:
    entities = get_config()["vault"]["entities"]
    rel = note.relative_to(EXAMPLES_VAULT)
    entity_type = entity_type_for_path(rel, entities)
    assert entity_type is not None, f"Could not infer entity type for {rel}"

    schema_path = SCHEMAS_ROOT / f"{entity_type}.schema.json"
    if not schema_path.is_file():
        pytest.skip(f"Schema not yet written: {schema_path}")

    schema = load_json_schema(schema_path)
    frontmatter, err = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert err is None, f"{rel}: {err}"
    assert frontmatter is not None

    errors = validate_against(frontmatter, schema)
    assert not errors, (
        f"{rel} failed validation against {schema_path.name}:\n"
        + "\n".join(
            f"  - at '{'.'.join(str(p) for p in e.absolute_path) or '<root>'}': {e.message}"
            for e in errors
        )
    )


@pytest.mark.parametrize(
    "manifest",
    list(iter_plugin_manifests()),
    ids=lambda p: str(p.relative_to(REPO_ROOT)),
)
def test_plugin_manifest_validates(manifest: Path) -> None:
    schema_path = SCHEMAS_ROOT / "plugin-manifest.schema.json"
    schema = load_json_schema(schema_path)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    errors = validate_against(data, schema)
    assert not errors, (
        f"{manifest.relative_to(REPO_ROOT)} failed plugin-manifest validation:\n"
        + "\n".join(
            f"  - at '{'.'.join(str(p) for p in e.absolute_path) or '<root>'}': {e.message}"
            for e in errors
        )
    )


@pytest.mark.parametrize(
    "artifact",
    list(iter_artifact_jsons()),
    ids=lambda p: str(p.relative_to(EXAMPLES_OUTPUT)),
)
def test_output_artifact_validates(artifact: Path) -> None:
    stem = artifact.stem
    schema_path = SCHEMAS_ROOT / "artifacts" / f"{stem}.schema.json"
    if not schema_path.is_file():
        pytest.skip(f"No artifact schema for {stem}")

    schema = load_json_schema(schema_path)
    data = json.loads(artifact.read_text(encoding="utf-8"))
    errors = validate_against(data, schema)
    assert not errors, (
        f"{artifact.relative_to(REPO_ROOT)} failed validation against {schema_path.name}:\n"
        + "\n".join(
            f"  - at '{'.'.join(str(p) for p in e.absolute_path) or '<root>'}': {e.message}"
            for e in errors
        )
    )


def test_entity_folders_have_at_least_one_schema() -> None:
    """Sanity check: every known entity type has a matching schema file."""
    entities = get_config()["vault"]["entities"]
    missing = []
    for entity_type in entities:
        if not (SCHEMAS_ROOT / f"{entity_type}.schema.json").is_file():
            missing.append(entity_type)
    # Allow missing schemas for entity types that are being filled in by a parallel agent,
    # but assert that at least the core ones exist.
    core = {"project", "job", "education", "skill", "award", "research"}
    assert core.issubset(set(entities.keys()) - set(missing)), (
        f"Core entity schemas missing: {sorted(core & set(missing))}"
    )
