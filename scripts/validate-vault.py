"""ResumeOS Vault Validator.

Walks the vault, parses frontmatter from each Markdown note, infers the entity type from the
containing folder (per resumeos.config.yaml: vault.entities), and validates the frontmatter
against the matching schema under schemas/*.schema.json.

Also validates:
- skills/*/plugin.json and the root plugin.json against plugin-manifest.schema.json
- examples/output/**/artifacts/*.json against schemas/artifacts/*.schema.json

Exits non-zero on any violation. Prints a summary at the end.
"""

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validator_for


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_ROOT = REPO_ROOT / "schemas"
CONFIG_PATH = REPO_ROOT / "resumeos.config.yaml"


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------
_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def normalize_dates(obj: Any) -> Any:
    """Recursively convert YAML-parsed date/datetime objects to ISO 8601 strings.

    PyYAML auto-parses unquoted ``2023-08-15`` into ``datetime.date``. Schemas
    declare date fields as ``type: string`` (ADR-0002 ISO 8601). A parsed date is
    semantically an ISO date, so coerce it to a string to keep authoring ergonomic
    (no quoting required) while staying schema-faithful.
    """
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: normalize_dates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize_dates(v) for v in obj]
    return obj


def parse_frontmatter(md_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Return (frontmatter_dict, error_message). error_message is None on success."""
    m = _FM_RE.match(md_text)
    if not m:
        return None, "No YAML frontmatter found"
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"
    if not isinstance(data, dict):
        return None, "Frontmatter is not a mapping"
    return normalize_dates(data), None


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------
_SCHEMA_CACHE: Dict[str, Dict[str, Any]] = {}


def load_schema(path: Path) -> Dict[str, Any]:
    if str(path) in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[str(path)]
    with path.open(encoding="utf-8") as f:
        schema = json.load(f)
    # Register $id so $ref resolution within the same file works; also make it discoverable.
    _SCHEMA_CACHE[str(path)] = schema
    return schema


def infer_entity_type(rel_path: Path, entities: Dict[str, str]) -> Optional[str]:
    """Infer entity type from the folder path using the vault.entities mapping."""
    parts = rel_path.parts
    # Match the longest entity folder path first to avoid career/ matching career/projects/
    best_match: Optional[str] = None
    best_depth: int = -1
    for entity_type, folder in entities.items():
        folder_parts = tuple(Path(folder).parts)
        n = len(folder_parts)
        if parts[:n] == folder_parts and n > best_depth:
            best_match = entity_type
            best_depth = n
    return best_match


def schema_for_entity(entity_type: str) -> Path:
    return SCHEMAS_ROOT / f"{entity_type}.schema.json"


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------
def validate_instance(instance: Any, schema: Dict[str, Any], source: str) -> Iterator[str]:
    """Yield validation error messages."""
    cls = validator_for(schema)
    validator = cls(schema)
    for error in validator.iter_errors(instance):
        path = ".".join(str(p) for p in error.absolute_path) or "<root>"
        yield f"{source}: {path} - {error.message}"


def iter_markdown_files(vault_root: Path) -> Iterator[Path]:
    for p in vault_root.rglob("*.md"):
        if p.is_file():
            yield p


def iter_json_files(root: Path, pattern: str) -> Iterator[Path]:
    for p in root.rglob(pattern):
        if p.is_file():
            yield p


# ---------------------------------------------------------------------------
# Main validation passes
# ---------------------------------------------------------------------------
def load_config() -> Dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_vault(vault_path: Path, entities: Dict[str, str]) -> list:
    """Validate every markdown note under vault_path. Returns a list of error strings."""
    errors = []
    for md in iter_markdown_files(vault_path):
        rel = md.relative_to(vault_path)
        # Skip READMEs (folder-notes, not entities), hidden folders, and periodic/daily notes
        if rel.name.lower() == "readme.md":
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        # Skip daily/periodic/canvas/inbox (they are operational folders, not entity folders)
        if rel.parts and rel.parts[0] in {"daily", "periodic", "canvas", "inbox"}:
            continue

        entity_type = infer_entity_type(rel, entities)
        if entity_type is None:
            # Not in a known entity folder -> nothing to validate against
            continue

        schema_path = schema_for_entity(entity_type)
        if not schema_path.is_file():
            # Schema not yet written (e.g. competition, internship, opensource may be missing
            # depending on which agent has created them). Warn, do not fail.
            errors.append(f"WARN: no schema at {schema_path} for entity '{entity_type}' (file: {rel})")
            continue

        schema = load_schema(schema_path)
        frontmatter, err = parse_frontmatter(md.read_text(encoding="utf-8"))
        if err is not None:
            errors.append(f"{rel}: {err}")
            continue
        if frontmatter is None:
            continue

        errors.extend(validate_instance(frontmatter, schema, str(rel)))

    return errors


def validate_plugin_manifests() -> list:
    """Validate every plugin.json under skills/ and the root plugin.json."""
    errors = []
    manifest_schema = load_schema(SCHEMAS_ROOT / "plugin-manifest.schema.json")

    candidates = list(REPO_ROOT.glob("skills/*/plugin.json"))
    root_manifest = REPO_ROOT / "plugin.json"
    if root_manifest.is_file():
        candidates.append(root_manifest)

    for p in candidates:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{p.relative_to(REPO_ROOT)}: invalid JSON: {e}")
            continue
        errors.extend(validate_instance(data, manifest_schema, str(p.relative_to(REPO_ROOT))))

    return errors


def validate_artifacts(examples_path: Path) -> list:
    """Validate every examples/output/**/artifacts/*.json against schemas/artifacts/*.schema.json."""
    errors = []
    output_dir = examples_path / "output"
    if not output_dir.is_dir():
        return errors

    for json_file in iter_json_files(output_dir, "artifacts/*.json"):
        # Infer artifact schema: file stem -> schemas/artifacts/<stem>.schema.json
        stem = json_file.stem
        artifact_schema_path = SCHEMAS_ROOT / "artifacts" / f"{stem}.schema.json"
        if not artifact_schema_path.is_file():
            # Not every artifact kind has its own schema; skip unknown ones.
            continue
        schema = load_schema(artifact_schema_path)
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{json_file.relative_to(REPO_ROOT)}: invalid JSON: {e}")
            continue
        errors.extend(
            validate_instance(data, schema, str(json_file.relative_to(REPO_ROOT)))
        )

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="ResumeOS Vault Validator")
    parser.add_argument(
        "--vault",
        type=Path,
        default=None,
        help="Path to the vault to validate (default: resumeos.config.yaml vault.path)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help="Path to resumeos.config.yaml (default: repo root)",
    )
    args = parser.parse_args()

    config = load_config()
    entities: Dict[str, str] = config["vault"]["entities"]
    vault_rel: str = config["vault"]["path"]

    if args.vault is not None:
        vault_path = args.vault.resolve()
    else:
        vault_path = (REPO_ROOT / vault_rel).resolve()

    if not vault_path.is_dir():
        print(f"ERROR: vault directory does not exist: {vault_path}", file=sys.stderr)
        return 2

    print(f"ResumeOS Vault Validator")
    print(f"  Vault : {vault_path}")
    print(f"  Schemas: {SCHEMAS_ROOT}")
    print()

    all_errors: list = []

    print("[1/3] Validating vault entities ...")
    vault_errors = validate_vault(vault_path, entities)
    all_errors.extend(vault_errors)
    if vault_errors:
        for e in vault_errors:
            print(f"  {e}")
    else:
        print("  OK")
    print()

    print("[2/3] Validating plugin manifests ...")
    manifest_errors = validate_plugin_manifests()
    all_errors.extend(manifest_errors)
    if manifest_errors:
        for e in manifest_errors:
            print(f"  {e}")
    else:
        print("  OK")
    print()

    # Artifact validation: only against examples/output when the vault being validated is examples/
    examples_path = REPO_ROOT / "examples"
    examples_out = examples_path / "output"
    print("[3/3] Validating output artifacts ...")
    if examples_out.is_dir():
        artifact_errors = validate_artifacts(examples_path)
        all_errors.extend(artifact_errors)
        if artifact_errors:
            for e in artifact_errors:
                print(f"  {e}")
        else:
            print("  OK")
    else:
        print("  SKIP (no examples/output/ found)")
    print()

    # Summary
    real_errors = [e for e in all_errors if not e.startswith("WARN:")]
    warnings = [e for e in all_errors if e.startswith("WARN:")]

    print("=" * 60)
    print(f"Summary: {len(real_errors)} error(s), {len(warnings)} warning(s)")
    if warnings:
        for w in warnings:
            print(f"  {w}")
    if real_errors:
        print("FAILED")
        return 1

    print("PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
