---
fragment: stale-detect
inputs: [changed-entity-id, derived-assembly-artifacts]
outputs: [stale-doc-list]
applies: ADR-0001
---

Detect which derived documents in `output/` are stale after a vault entity changes.

Rules:

- Scan every derived doc's assembly artifact (`output/*/artifacts/assembly.json` and
  equivalent provenance-bearing artifacts).
- For each artifact, check whether its provenance citations include the changed entity's
  `id`.
- If yes, mark the doc as stale: record `path`, `source_entity`, and `changed_field`.
- If `output/.stale.json` exists, merge the new stale entries; do not overwrite entries
  the user has already acknowledged.
- If the file does not exist, create it with the initial entries.
- Stale detection is a read-only provenance scan. Do not invent or modify any entity fact.
- Do not remove a stale entry unless the user explicitly regenerates the doc or dismisses
  it.
