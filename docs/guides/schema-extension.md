# Schema Extension Guide

This guide explains how to add a new entity schema to ResumeOS. It implements
[ADR-0002](../decisions/ADR-0002-schema-strategy.md) (schema strategy: JSON Schema superset of
JSON Resume, strict frontmatter).

---

## 1. The rules (non-negotiable)

Every entity schema must:

1. Use **JSON Schema draft 2020-12**.
2. Set `additionalProperties: false` (the user can flip this globally in
   `resumeos.config.yaml: schemas.additional_properties` for gradual adoption).
3. Require `sources[]` and `confidence` on every entity (provenance — ADR-0007).
4. Use a versioned `$id`: `https://resumeos.dev/schemas/<semver>/<entity>.schema.json`.
5. Include an `$resumeos` extension object for ResumeOS-specific metadata (library_hints,
   tailoring_score, etc.).
6. Keep dates in ISO 8601 format (`format: date`).
7. Keep the schema in `schemas/` with the filename `<entity>.schema.json`.

---

## 2. Adding a new entity schema

### Step 1: Draft the schema

Create `schemas/<entity>.schema.json`. Start from an existing schema (e.g. `project.schema.json`)
and adapt. A minimal starting point:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://resumeos.dev/schemas/1.0.0/<entity>.schema.json",
  "title": "<Entity>",
  "type": "object",
  "additionalProperties": false,
  "required": ["entity_type", "title", "sources"],

  "properties": {
    "entity_type": {
      "type": "string",
      "const": "<entity>",
      "description": "Discriminator; inferred from the folder."
    },
    "title": { "type": "string", "minLength": 2 },
    "id": { "type": "string", "pattern": "^[a-z0-9-]+$" },
    "tags": { "type": "array", "items": { "type": "string" }, "default": [] },
    "confidence": {
      "type": "string",
      "enum": ["confirmed", "inferred", "missing"],
      "default": "confirmed"
    },
    "sources": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["kind", "ref"],
        "properties": {
          "kind": { "type": "string" },
          "ref":  { "type": "string" },
          "note": { "type": ["string", "null"] }
        }
      }
    },
    "$resumeos": { "type": "object", "additionalProperties": true }
  }
}
```

### Step 2: Update `schemas/README.md`

Add a row to the entity schema table:

```markdown
| [`<entity>.schema.json`](<entity>.schema.json) | <Entity description> | `vault/career/<entities>/` |
```

### Step 3: Update `resumeos.config.yaml: vault.entities`

Add the entity-type → folder mapping:

```yaml
vault:
  entities:
    <entity>: career/<entities>
```

The validator uses this mapping to infer which schema to apply to a given folder.

### Step 4: Create the template

Create `templates/<entity>.md` using the Templater format. The template's frontmatter must include
every key listed in the schema's `required` array, plus the standard `entity_type`, `sources`, and
`confidence`. The template body should provide guidance for the prose sections.

### Step 5: Add a folder-note README

Create `vault/career/<entities>/README.md` explaining what notes go there and referencing the
template and schema. This also ensures the directory is tracked by Git.

### Step 6: Add example fixtures

Create at least one example entity note under `examples/vault/career/<entities>/` so the schema
validation tests cover it.

### Step 7: Validate

Run the validator locally:

```bash
python scripts/validate-vault.py --vault examples/vault
```

---

## 3. Versioning and bumping

Schemas are versioned via the `$id` path: `https://resumeos.dev/schemas/<semver>/<entity>.schema.json`.

### Patch bump (`1.0.0` → `1.0.1`)

Adding optional fields, tightening descriptions, changing defaults. Existing vault notes still
validate. No migration needed.

### Minor bump (`1.0.0` → `1.1.0`)

Adding new optional fields that are useful but not breaking. Existing vault notes still validate.
No migration needed.

### Major bump (`1.0.0` → `2.0.0`)

Adding required fields, removing fields, changing types, changing enums. **Breaking change.**
Requires:

1. Bump `$id` to `https://resumeos.dev/schemas/2.0.0/<entity>.schema.json`.
2. Write a migration note at `schemas/migrations/<old>→<new>.md` explaining how users should
   update their vault notes.
3. Update `resumeos.config.yaml: schema_version` to the new major version.
4. Update `templates/<entity>.md` to include any new required fields.
5. Update all example vault notes.

The old `$id` remains accessible (never delete it).

---

## 4. Templates must match schema keys

The template's YAML frontmatter must:

- Include every `required` key from the schema.
- Not include keys that are forbidden by `additionalProperties: false` (unless the user has
  opted into `additional_properties: true` in config).
- Use the exact types and formats declared by the schema (e.g. dates as `YYYY-MM-DD`).

If the template and schema disagree, CI fails. This is by design — the schema is the contract,
the template is the UI.

---

## 5. CI validation

The CI pipeline (`scripts/validate-vault.py`) validates:

- Every `examples/vault/**/*.md` frontmatter against the schema matching its folder (via
  `resumeos.config.yaml: vault.entities`).
- Every `skills/*/plugin.json` and the root `plugin.json` against `plugin-manifest.schema.json`.
- Every `examples/output/**/artifacts/*.json` against the artifact schemas in `schemas/artifacts/`.

If a schema change breaks existing examples, the CI job fails. Fix the examples or ship a
migration.

---

## 6. The `$resumeos` extension

The `$resumeos` object is a namespace for ResumeOS-specific metadata that should not pollute the
JSON Resume export. Examples:

```json
{
  "$resumeos": {
    "schema_version": "1.0.0",
    "library_hints": { "tailoring_score":  0.85 },
    "tailoring_score": 0.85
  }
}
```

JSON Resume tools ignore this field. ResumeOS tools (Skills, the library, the UI) read it.
The `$resumeos` object is always optional but always permitted.

---

## 7. Checklist

Before shipping a new or changed schema:

- [ ] JSON Schema draft 2020-12, `$id` versioned.
- [ ] `additionalProperties: false` at the root.
- [ ] `sources[]` and `confidence` are required.
- [ ] `$resumeos` extension object is permitted.
- [ ] Dates use `format: date` (ISO 8601).
- [ ] Registered in `schemas/README.md`, `resumeos.config.yaml`, and a template exists.
- [ ] Folder-note README exists under `vault/`.
- [ ] Example fixtures exist under `examples/vault/`.
- [ ] `python scripts/validate-vault.py --vault examples/vault` passes locally.
- [ ] Breaking changes have a migration note.
