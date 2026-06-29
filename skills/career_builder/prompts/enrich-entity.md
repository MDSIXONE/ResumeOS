---
fragment: enrich-entity
inputs: [classified-facts, user-answers, entity-schema]
outputs: [enriched-entity-note]
applies: ADR-0007
---

Build a canonical entity note in `vault/career/*` from classified facts and user answers.

Rules:

- Frontmatter must include: `entity_type`, `title`, `id`, all schema-required fields,
  `sources[]` (preserving the full provenance chain from inbox notes and user answers),
  `confidence`.
- Upgrade `confidence` to `confirmed` ONLY for facts the user explicitly confirmed. Leave
  omitted facts as `missing`.
- Validate the assembled frontmatter against the entity's JSON schema before writing. If
  validation fails, report the error; do not write a partial note.
- Body: structured sections matching the entity template (overview, contributions, metrics,
  references).
- Never remove a `sources[]` entry once recorded.
- Never write to `vault/career/*` without passing schema validation first.
