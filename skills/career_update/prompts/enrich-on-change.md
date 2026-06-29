---
fragment: enrich-on-change
inputs: [validated-entity, career-builder-pipeline]
outputs: [enriched-entity]
applies: ADR-0007
---

Re-enrich an entity after a vault change using the career_builder pipeline.

Rules:

- Invoke career_builder on the validated entity: re-classify confidence, detect gaps, emit
  follow-up questions, and on user confirmation rewrite the entity note.
- Preserve `sources[]` provenance; do not strip or replace it.
- If new information came from the change, add a new source entry; do not discard existing
  sources.
- Upgrade `confidence` to `confirmed` only for facts the user explicitly confirms.
- If a gap is detected, emit a follow-up question and PAUSE. Do not auto-fill the gap.
- Validate the rewritten entity against its schema before writing.
