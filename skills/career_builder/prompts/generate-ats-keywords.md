---
fragment: generate-ats-keywords
inputs: [enriched-entity]
outputs: [ats-keyword-list]
applies: ADR-0007
---

Extract and confirm ATS-relevant keywords from an enriched entity.

Rules:

- Pull keywords only from fields with `confidence: confirmed` in the entity (stack,
  metrics, contribution, tags).
- Do not invent keywords. If a technology, framework, or method is not in the entity's
  `stack` or body, do not add it to `ats_keywords[]`.
- Prefer the canonical form used in the entity (e.g. if the entity says "PyTorch", do not
  expand it to "deep learning framework" in ats_keywords).
- Store the keyword list in the entity's `ats_keywords[]` frontmatter field.
- Keep the list concise: 5–15 keywords per entity.
