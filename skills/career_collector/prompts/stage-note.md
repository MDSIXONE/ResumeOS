---
fragment: stage-note
inputs: [extracted-facts, source-kind, source-ref]
outputs: [inbox-note]
applies: ADR-0007
---

Assemble a staged note in `vault/inbox/` from a set of extracted facts.

Rules:

- The note MUST include `sources[]` in its frontmatter with at least one entry. Each entry
  needs `kind` (source kind string) and `ref` (path, URL, or identifier). A note with empty
  `sources[]` is a staging failure — do not write it.
- Set `confidence: inferred` on the note. The collector does NOT upgrade confidence.
- Set `entity_type: inbox` and `kind` to the guessed entity type (project, education, skill,
  etc.).
- Include `created_at` (ISO 8601 date) and `tags[]` (lowercase, kebab-case).
- Body: list extracted facts as bullet points. Prefix each bullet with its source tag
  (e.g. `[src:pdf:p3]`).
- End with an `## Open Questions` section listing any ambiguous or incomplete items.
- Filename format: `<source-slug>_<YYYY-MM-DD>.md` under `vault/inbox/`.
- Do not write to `vault/career/*` or `vault/jobs/*`.
