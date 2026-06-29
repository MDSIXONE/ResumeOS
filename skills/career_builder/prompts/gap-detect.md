---
fragment: gap-detect
inputs: [classified-facts, entity-schema]
outputs: [gap-list]
applies: ADR-0007
---

Detect gaps between classified facts and the target entity schema.

Rules:

- Compare each schema-required field against the classified fact set.
- Classify each gap:
  - `missing` — the schema requires it and no source provides it.
  - `inferred` — a fact exists but is tagged `confidence: inferred`.
  - `partial` — a field is filled but incomplete (e.g. a start date without an end date on
    a completed project).
- For each gap, record: entity id, field name, gap class, and the JD / schema requirement
  that motivates it.
- Do not attempt to fill gaps. Hand the gap list to `follow-up-question.md` for question
  generation.
- Never fabricate a value for a gap.
