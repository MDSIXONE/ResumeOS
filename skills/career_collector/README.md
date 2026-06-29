# career_collector

Collect raw career material from external sources and stage it as provenanced notes in
`vault/inbox/`.

## When to use

- You have a resume PDF, a GitHub profile, a LinkedIn export, a certificate image, or any raw
  career material you want to bring into ResumeOS.
- You want the system to extract structured facts and prepare them for enrichment — without
  writing directly to the canonical career vault.

## How it works

See [SKILL.md](SKILL.md) for the full pipeline. In short:

1. **Step 1 — Source Classification:** identify the source kind (PDF, DOCX, GitHub, LinkedIn, image,
   blog, etc.).
2. **Step 2 — Extraction:** extract structured facts per source kind using the matching prompt
   fragment; all facts tagged `confidence: inferred`.
3. **Step 3 — Staging:** assemble one inbox note per source with `sources[]` provenance.
4. **Step 4 — Collection Report:** summarize what was ingested and flag low-confidence extractions.

## Inputs

- Any of: PDF, DOCX, Markdown file, GitHub repo or Gist URL, LinkedIn data export, certificate
  image, blog post, README.

## Outputs

- Staged notes in `vault/inbox/<source-slug>_<timestamp>.md`, each with `sources[]` and
  `confidence: inferred`.
- A collection report printed to the terminal (not persisted).

## Guardrails

- **Anti-hallucination (ADR-0007):** every fact tagged `inferred`; `sources[]` required; nothing
  silently omitted or invented.
- **Least-privilege:** can write only to `vault/inbox/**`; cannot touch `vault/career/**` or
  `vault/jobs/**`.
- **Downstream dependency:** run `career_builder` after collection to validate and enrich staged
  notes into canonical entities.

## Related

- [ADR-0001 — knowledge base is SSOT](../../docs/decisions/ADR-0001-knowledge-base-as-single-source-of-truth.md)
- [ADR-0007 — anti-hallucination](../../docs/decisions/ADR-0007-anti-hallucination-contract.md)
- [Skill authoring spec](../../docs/guides/skill-authoring-spec.md)
