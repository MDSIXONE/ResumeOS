---
fragment: provenance
applies: ADR-0001, ADR-0007
inputs: [vault entities, derived bullets]
outputs: [cited bullets]
---

# Provenance & Citation Rules

Every fact that leaves the vault for a derived document must be traceable.

**Citation format:** `entity_id:field` — e.g. `px4-uav:metrics[0]` means "the first metric of the
project whose id is px4-uav".

**Rules:**
1. Attach a citation to every bullet, every metric, every skill listed in a derived resume.
2. If a bullet combines facts from two entities, cite both: `px4-uav:contribution, ros-nav:role`.
3. A bullet with NO citation is invalid. Do not emit it. Ask the user for the missing source.
4. Never strip `frontmatter.sources[]` from an entity — that is the entity-level provenance and is
   permanent.
5. In phase artifacts (`assembly.json`), store citations under each item's `provenance` field so
   checkpoints can show the user exactly where each bullet came from.

Provenance is what makes a ResumeOS resume defensible in an interview: every claim can be traced
back to a recorded, source-backed fact.
