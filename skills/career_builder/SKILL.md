---
name: career_builder
version: 0.1.0
description: Enrich the vault from inbox notes, detect gaps, ask follow-ups, and emit STAR stories, ATS keywords, and interview questions.
schema_version: 1.0.0
inputs: [inbox-note, project, education, skill, award, research, competition, internship, opensource]
outputs: [project, education, skill, award, research, competition, internship, opensource]
mcp_tools: []
anti_hallucination: true
---

# career_builder

Read `vault/inbox/` notes and existing `vault/career/*` entities, validate them against their
schemas, detect missing fields, ASK follow-up questions for every gap (never invent), then write
enriched, schema-validated entities back to `vault/career/*`.

**career_builder updates `confidence` to `confirmed` ONLY when the user explicitly confirms.**

Optionally generates STAR stories, ATS keyword lists, and interview questions attached to each
entity.

**Obey ADR-0007 at every step: state only confirmed vault facts; ask on any gap; never invent.**

---

## Inputs

- `vault/inbox/*.md` — staged notes from `career_collector` (all `confidence: inferred`).
- `vault/career/*` — existing canonical entities (may be partial or confirmed).
- `schemas/*.schema.json` — the entity schemas to validate against.
- Run parameters from `resumeos.config.yaml` (entity roots, defaults).

## Outputs

- Enriched entity notes in `vault/career/*` (one note per entity), validated against their
  schemas.
- STAR stories stored in entity `$resumeos.star_stories[]`.
- ATS keywords stored in entity `ats_keywords[]`.
- Interview questions stored in entity `interview_questions[]`.
- A knowledge-graph diff summary (new backlinks, tags, cross-references).

---

## Pipeline

### Step A — Read & Validate

- **Inputs:** all `vault/inbox/*.md` and `vault/career/*` entities.
- **Work:** for each inbox note, infer the target entity type from `kind` (or ask the user if
  unclear). For each existing entity, validate its frontmatter against the matching schema.
- Report invalid entities (skip them; do not abort). Report inbox notes whose `kind` cannot be
  mapped.
- **Outputs:** a validated working set of inbox notes + existing entities, plus a list of items
  that could not be validated.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step B — Confidence Classification

- **Compose:** `prompts/core/anti-hallucination.md`.
- **Work:** for each fact in each inbox note, classify its confidence level:
  - `confirmed` — a fact the user has explicitly stated or that comes from a primary source
    (e.g. a GitHub commit the user authored).
  - `inferred` — a plausible extraction that needs human confirmation.
  - `missing` — a field the schema requires but no source provides.
- Preserve the original `sources[]` from the inbox note; never discard provenance.
- **Outputs:** a classified fact map per entity.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step C — Gap Detection & Follow-Up Questions

- **Compose:** `prompts/gap-detect.md` + `prompts/follow-up-question.md` +
  `prompts/core/ask-never-invent.md`.
- **Work:** for each `missing` or low-confidence field, emit a precise follow-up question:
  - name the entity and field,
  - explain why it matters (e.g. required by schema, needed for tailoring),
  - offer a concrete prompt the user can answer in one or two sentences,
  - never suggest a fabricated answer.
- **PAUSE.** Present the questions to the user. Do not write any enriched entity until the
  user has answered or explicitly chosen to omit the field.
- If the user omits, mark the field `confidence: missing` and proceed; do not invent.
- **Outputs:** a set of answered (or omitted) gaps.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step D — Enriched Entity Write

- **Compose:** `prompts/enrich-entity.md` + `prompts/core/anti-hallucination.md` +
  `prompts/core/provenance.md`.
- **Work:** for each entity, build the canonical note:
  - Frontmatter: `entity_type`, `title`, `id`, all schema-required fields, `sources[]`
    (preserved from inbox notes + any new sources from user answers), `confidence`.
  - Upgrade `confidence` to `confirmed` ONLY for facts the user confirmed in Step C. Leave
    omitted facts as `missing`.
  - Validate the assembled frontmatter against the entity's schema. If validation fails,
    report the error and ask the user to fix — do not silently drop required fields.
  - Body: structured sections (overview, contributions, metrics, references) as specified by
    the entity template.
- **Outputs:** one enriched note per entity written to `vault/career/<entity-type-plural>/<id>.md`.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step E — STAR / ATS / Interview Question Generation

- **Compose:** `prompts/generate-star.md` + `prompts/generate-ats-keywords.md` +
  `prompts/generate-interview-questions.md` + `prompts/core/anti-hallucination.md`.
- **Work:** for each enriched entity, optionally generate:
  - **STAR stories** (`$resumeos.star_stories[]`): each story cites the entity field it draws
    from. Only `confirmed` facts may be used.
  - **ATS keywords** (`ats_keywords[]`): extract / confirm relevant keywords from the entity's
    stack, metrics, and contribution. Only facts present in the entity.
  - **Interview questions** (`interview_questions[]`): generate questions this entity is likely
    to invite. Questions trace to confirmed fields.
- All generated artifacts are stored in the entity note itself (under the appropriate
  frontmatter key or `$resumeos` namespace), never in a separate output file.
- **Outputs:** enriched entity notes augmented with STAR / ATS / interview-question fields.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step F — Knowledge-Graph Diff

- **Inputs:** the set of entities written in Step D.
- **Work:** compute a diff of the knowledge graph:
  - new `[[wikilinks]]` and `related[]` edges,
  - new or changed `tags[]`,
  - back-links from other entities affected by the new/updated notes.
- Present the diff to the user as a summary (not persisted).
- **Outputs:** a Markdown diff summary printed to the terminal.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

---

## Prompt Fragments

| Step | Prompt |
|------|--------|
| Gap detection | `prompts/gap-detect.md` |
| Follow-up question | `prompts/follow-up-question.md` |
| Entity enrichment | `prompts/enrich-entity.md` |
| STAR story generation | `prompts/generate-star.md` |
| ATS keyword extraction | `prompts/generate-ats-keywords.md` |
| Interview question generation | `prompts/generate-interview-questions.md` |

Always compose local fragments with the relevant global fragments from `prompts/core/`.

---

## Anti-hallucination Enforcement

- `confidence` is upgraded to `confirmed` only on explicit user confirmation.
- Every enriched entity carries `sources[]` preserving the full provenance chain.
- STAR / ATS / interview-question generation uses only `confirmed` facts.
- Schema validation is run before writing; invalid entities are not written.
- An omitted field is marked `missing`, never silently filled.
