---
fragment: json-resume-convert
inputs: [rendered resume sections]
outputs: [json-resume object]
applies: ADR-0002
---

# JSON Resume Conversion (round-trip)

Map a rendered master resume into the [JSON Resume](https://jsonresume.org/) schema so the output
is portable and round-trippable.

**Mapping rules:**
- `basics` -- name, label, email, phone, website, summary. Pull from vault if available; leave empty
  if not confirmed.
- `education[]` -- each `education` entity. Map `institution` -> `institution`, degree -> `studyType`,
  field -> `area`, dates -> `startDate`/`endDate`.
- `work[]` -- each entity of type `internship` or `project` that has an org. Map title -> `position`,
  org -> `name`, dates -> `startDate`/`endDate`, bullets -> `highlights[]`.
- `projects[]` -- each `project` entity. Map title -> `name`, stack -> `keywords[]`, contribution ->
  `description`, metrics -> `highlights[]`.
- `skills[]` -- each skill cluster from the `skill` entity. Map cluster name -> `name`, skills ->
  `keywords[]`.
- `awards[]` -- each `award` entity. Map title -> `title`, issuer -> `issuer`, date -> `date`.
- `publications[]` -- each `research` entity with a publication. Map title -> `name`, venue ->
  `publisher`, date -> `releaseDate`.
- `volunteer[]`, `interests[]`, `references[]` -- OMIT unless confirmed in the vault.

**Hard rules:**
- Do not invent any field. If a JSON Resume field has no vault source, omit it (do not fill with
  a placeholder or guess).
- Every `highlights[]` entry must trace to a vault bullet. If a bullet was dropped for lack of
  citation, do not include it here.
- Preserve the entity-id citation in a `_provenance` extension field for audit (JSON Resume custom
  extension: `x_resumeos_provenance`).

**Output:** a single JSON Resume object, ready to write to `master.json`.
