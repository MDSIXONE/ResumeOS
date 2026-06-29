# ResumeOS Schemas

JSON Schema (draft 2020-12) for every entity in the vault, every plugin manifest, and every pipeline
artifact. See [ADR-0002](../docs/decisions/ADR-0002-schema-strategy.md) for the strategy.

## Entity schemas (validate vault frontmatter)

| Schema | Entity | Folder |
|---|---|---|
| [`project.schema.json`](project.schema.json) | Career project | `vault/career/projects/` |
| [`job.schema.json`](job.schema.json) | Job application | `vault/jobs/` |
| [`education.schema.json`](education.schema.json) | Education | `vault/career/education/` |
| [`skill.schema.json`](skill.schema.json) | Competency note | `vault/career/skills/` |
| [`award.schema.json`](award.schema.json) | Award | `vault/career/awards/` |
| [`research.schema.json`](research.schema.json) | Research output | `vault/career/research/` |
| [`competition.schema.json`](competition.schema.json) | Competition | `vault/career/competitions/` |
| [`internship.schema.json`](internship.schema.json) | Internship | `vault/career/internships/` |
| [`opensource.schema.json`](opensource.schema.json) | Open-source contribution | `vault/career/opensource/` |

## Manifest schemas

| Schema | Validates |
|---|---|
| [`plugin-manifest.schema.json`](plugin-manifest.schema.json) | Every `plugin.json` (ADR-0004/0005) |
| [`vault-meta.schema.json`](vault-meta.schema.json) | `vault/vault.meta.yaml` (vault-level metadata) |

## Pipeline artifact schemas

| Schema | Phase |
|---|---|
| [`artifacts/research.schema.json`](artifacts/research.schema.json) | resume_tailoring Phase 1 |
| [`artifacts/gaps.schema.json`](artifacts/gaps.schema.json) | resume_tailoring Phase 2 |
| [`artifacts/assembly.schema.json`](artifacts/assembly.schema.json) | resume_tailoring Phase 3 |

## Conventions

- **Draft 2020-12**, `$id` versioned (`/schemas/1.0.0/...`).
- **`additionalProperties: false`** by default (flip via `resumeos.config.yaml: schemas.additional_properties`).
- **`sources[]` required** on every entity (provenance — ADR-0007).
- **`confidence` enum** `confirmed | inferred | missing` on every entity.
- **`$resumeos`** extension map for ResumeOS-specific metadata (ignored by JSON Resume tools).
- **Dates ISO 8601** (`format: date`).

## Migrations

Breaking schema changes bump the major version and ship a migration note under `migrations/`.
Past versions remain available under their versioned `$id`.
