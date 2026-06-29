---
fragment: generate-star
inputs: [enriched-entity]
outputs: [star-stories]
applies: ADR-0007
---

Generate STAR (Situation, Task, Action, Result) stories from a confirmed entity.

Rules:

- Use ONLY facts with `confidence: confirmed` from the entity. Never use `inferred` or
  `missing` facts.
- Each STAR story must cite the entity field(s) it draws from (stored as a `citations[]`
  annotation alongside the story in `$resumeos.star_stories[]`).
- A STAR story without a citation is a build failure — drop it.
- Do not invent metrics, team sizes, dates, or technologies. If the entity lacks a Result
  metric, mark the Result section as "not quantified in vault" rather than guessing a
  number.
- Preserve the original source tags from the entity's `sources[]`.
- Write the stories into the entity note under `$resumeos.star_stories[]`.
