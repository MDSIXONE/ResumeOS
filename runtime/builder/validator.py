"""Validator -- validates a Draft against a JSON schema.

Per Sprint 4 Principle 3: LLM outputs Draft, then Validator checks it
against the entity schema. If invalid, validation_errors are populated
and the pipeline can retry with error feedback.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

import jsonschema
from jsonschema import Draft202012Validator

from runtime.knowledge.draft import Draft


# Extra keys that the LLM may produce but the schema does not declare.
# These are carried through by the Writer into frontmatter but should
# not cause validation to fail. We strip them before schema validation,
# then put them back into draft.fields so the Merger sees everything.
_IGNORED_KEYS: Set[str] = {"description"}


class Validator:
    """Validates Draft.fields against the entity JSON schema.

    Loads the schema from schemas_root/<entity_type>.schema.json and uses
    jsonschema.Draft202012Validator to check the draft fields.
    """

    def __init__(self, schemas_root: Path) -> None:
        """Initialize with the path to the schemas directory.

        Args:
            schemas_root: Path to the directory containing entity schemas
                (e.g. schemas/).
        """
        self.schemas_root = Path(schemas_root)

    def validate(self, draft: Draft) -> Draft:
        """Validate draft.fields against the entity schema.

        If valid: clear draft.validation_errors, return draft.
        If invalid: fill draft.validation_errors with error messages.

        Returns:
            The same Draft object (modified).
        """
        schema_path = self.schemas_root / f"{draft.entity_type}.schema.json"
        errors: List[str] = []

        if not schema_path.exists():
            errors.append(f"schema not found: {schema_path}")
            draft.validation_errors = errors
            return draft

        try:
            schema_text = schema_path.read_text(encoding="utf-8")
            schema = json.loads(schema_text)
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"failed to load schema: {exc}")
            draft.validation_errors = errors
            return draft

        # Extract declared schema properties to filter the draft fields
        # before validation (schemas with additionalProperties: false would
        # otherwise reject keys the LLM legitimately wants to carry through
        # like ``description``).
        allowed_keys = set(schema.get("properties", {}).keys())
        schema_fields: Dict[str, Any] = {
            k: v for k, v in draft.fields.items() if k in allowed_keys
        }

        validator_cls = Draft202012Validator
        validator = validator_cls(schema)
        validation_errors = sorted(
            validator.iter_errors(schema_fields), key=lambda e: list(e.path)
        )

        if validation_errors:
            draft.validation_errors = [e.message for e in validation_errors]
        else:
            draft.validation_errors = []

        return draft
