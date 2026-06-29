# career_builder

Enrich `vault/inbox/` notes and existing `vault/career/*` entities into fully validated,
schema-compliant career notes. Detects gaps, asks follow-up questions, never invents.

## When to use

- You have staged notes in `vault/inbox/` from `career_collector`.
- You want to turn raw, `inferred` facts into `confirmed` vault entities.
- You want STAR stories, ATS keywords, and interview questions generated per entity.

## How it works

See [SKILL.md](SKILL.md) for the full pipeline. In short:

1. **Step A — Read & Validate:** ingest inbox notes + existing entities; validate against
   schemas.
2. **Step B — Confidence Classification:** tag each fact as `confirmed`, `inferred`, or
   `missing`.
3. **Step C — Gap Detection & Follow-Up:** emit precise questions for every gap; PAUSE for
   user answers. No entity is written until gaps are resolved.
4. **Step D — Enriched Entity Write:** write schema-validated notes to `vault/career/*`;
   preserve provenance.
5. **Step E — STAR / ATS / Interview Questions:** generate and attach per-entity.
6. **Step F — Knowledge-Graph Diff:** summarize new backlinks and tags.

## Inputs

- `vault/inbox/*.md` (from `career_collector`).
- Existing `vault/career/*` entities.

## Outputs

- Enriched, schema-validated entity notes in `vault/career/*`.
- STAR stories, ATS keywords, interview questions attached to each entity.
- Knowledge-graph diff summary (printed, not persisted).

## Guardrails

- **Anti-hallucination (ADR-0007):** every fact traced to `sources[]`; ask on any gap; never
  invent; `inferred` is never silently promoted to `confirmed`.
- **Least-privilege:** can write only to `vault/career/**`; cannot touch `output/**` or
  `vault/jobs/**`.
- **Schema-validated:** every entity note must pass its schema before being written.

## Related

- [ADR-0001 — knowledge base is SSOT](../../docs/decisions/ADR-0001-knowledge-base-as-single-source-of-truth.md)
- [ADR-0007 — anti-hallucination](../../docs/decisions/ADR-0007-anti-hallucination-contract.md)
- [Skill authoring spec](../../docs/guides/skill-authoring-spec.md)
