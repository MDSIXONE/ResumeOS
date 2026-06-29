# ResumeOS Tests

This directory contains the automated test suite for ResumeOS. Three layers of testing enforce
the system's invariants.

---

## 1. Schema-validation tests

`test_schema_validation.py` — a pytest test file that:

- Loads every `examples/vault/**/*.md` (excluding READMEs, daily/periodic/canvas/inbox).
- Parses the YAML frontmatter from each note.
- Infers the entity type from the containing folder via the `vault.entities` mapping in
  `resumeos.config.yaml`.
- Validates the frontmatter against the matching `schemas/<entity>.schema.json` using the
  `jsonschema` library (Draft 2020-12).
- Validates every `examples/output/**/artifacts/*.json` against `schemas/artifacts/*.schema.json`.
- Validates every `skills/*/plugin.json` and the root `plugin.json` against
  `schemas/plugin-manifest.schema.json`.

Run it locally:

```bash
pip install -r scripts/requirements.txt
pytest
```

Failures mean a vault note, plugin manifest, or artifact does not conform to its schema. Fix the
note/manifest/artifact, not the schema (unless the schema itself is wrong — in which case follow
the [schema extension guide](../docs/guides/schema-extension.md)).

---

## 2. Provenance tests

`test_provenance.py` — a pytest test that loads every `examples/output/**/artifacts/assembly.json`
and asserts:

- Every bullet has a non-empty `provenance` array.
- Each citation in `provenance` references an `entity_id` that exists somewhere in
  `examples/vault/`.

This enforces the anti-hallucination contract (ADR-0007): a derived resume bullet without a vault
citation is a build failure, not a warning.

Run it:

```bash
pytest tests/test_provenance.py -v
```

---

## 3. Skill behavior contracts

`contracts/<skill-name>.contract.md` — a Markdown contract per Skill. Each contract describes:

- **Happy path:** a vault fixture produces the expected output.
- **Anti-hallucination path:** a vault with a gap causes the Skill to ask, not to invent.
- **Checkpoint path** (for phased-pipeline Skills like `resume_tailoring`): the pipeline pauses at
  each checkpoint and waits for user review.

These are *specifications*, not runnable tests. They exist so a reviewer can see at a glance what
a Skill is supposed to do and what it is supposed to refuse. The Skill's `SKILL.md` body is the
mechanical implementation of its contract.

---

## How CI runs the validator

The CI pipeline (`.github/workflows/ci.yml`) installs Python, `pip install -r scripts/requirements.txt`,
then runs:

1. `pytest` — schema-validation and provenance tests.
2. `python scripts/validate-vault.py --vault examples/vault` — the standalone validator.

Both must pass. The standalone validator (`scripts/validate-vault.py`) is the same algorithm as
the pytest suite but is runnable without pytest; it prints a summary and exits non-zero on any
violation.

---

## Adding a new test

- Schema or manifest validation: extend `test_schema_validation.py`.
- Provenance rule: extend `test_provenance.py`.
- Skill behavior: write a new `contracts/<skill-name>.contract.md`.

---

## conftest note

No `conftest.py` is required for the basic suite. If you add fixtures (e.g. temporary vault
trees for Skill tests), place shared pytest fixtures in a `conftest.py` at this level.
