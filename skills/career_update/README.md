# career_update

Watch the vault for new or changed files. On each event, validate the entity, enrich it via
`career_builder`, and mark any derived documents in `output/` that cited the changed entity
as stale.

## When to use

- You add a new project to `vault/career/projects/` or edit an existing entity.
- You want the system to detect which resumes, cover letters, or interview packs need
  regeneration because they cited the changed entity.

## How it works

See [SKILL.md](SKILL.md) for the full pipeline. In short:

1. **Step a — Infer Entity Type:** map the changed file's folder to an entity type via
   `resumeos.config.yaml: vault.entities`.
2. **Step b — Schema Validation:** validate frontmatter against the entity's schema. If
   invalid, ask the user to fix.
3. **Step c — Enrichment:** delegate to `career_builder` for confidence reclassification,
   gap detection, and entity rewrite.
4. **Step d — Stale Detection:** scan `output/*/artifacts/assembly.json` provenance; mark
   docs that cited the changed entity as stale in `output/.stale.json`.
5. **Step e — Regeneration Prompt:** prompt the user to regenerate each stale doc. Never
   auto-regenerate.

## Inputs

- A vault change event (file create / modify under `vault/career/*` or `vault/jobs/*`).

## Outputs

- Enriched entity note in `vault/career/*` (delegated to `career_builder`).
- Updated `output/.stale.json` listing stale derived docs.
- A terminal prompt to regenerate affected docs.

## Guardrails

- **Anti-hallucination (ADR-0007):** delegates enrichment to `career_builder`; never
  invents facts.
- **Least-privilege:** can write only to `vault/career/**` and `output/.stale.json`; cannot
  touch `vault/.obsidian/**`.
- **No auto-regeneration:** always prompts the user before regenerating any derived doc.
- **Hook-driven:** triggered automatically on vault change via `onVaultChange`.

## Related

- [ADR-0001 — knowledge base is SSOT](../../docs/decisions/ADR-0001-knowledge-base-as-single-source-of-truth.md)
- [ADR-0007 — anti-hallucination](../../docs/decisions/ADR-0007-anti-hallucination-contract.md)
- [Skill authoring spec](../../docs/guides/skill-authoring-spec.md)
