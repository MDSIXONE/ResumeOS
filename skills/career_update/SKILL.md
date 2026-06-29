---
name: career_update
version: 0.1.0
description: Watch the vault for new or changed files; validate, enrich via career_builder, and mark derived docs stale.
schema_version: 1.0.0
inputs: [project, education, skill, award, research, competition, internship, opensource, job]
outputs: [project, education, skill, award, research, competition, internship, opensource, stale-marker]
mcp_tools: []
anti_hallucination: true
---

# career_update

Watch the vault for new or changed files. On each event:

1. Infer the entity type from the folder (per `resumeos.config.yaml: vault.entities`).
2. Validate the file's frontmatter against the matching schema.
3. Enrich the entity via `career_builder`.
4. Detect which derived documents in `output/` cited the changed entity and mark them stale.
5. Prompt the user to regenerate — never auto-regenerate without consent.

**career_update is a vault watcher, not a phased pipeline. It has no checkpoints.**

**Obey ADR-0007 at every step: state only confirmed vault facts; ask on any gap; never invent.**

---

## Inputs

- A vault change event (file created or modified under `vault/career/*` or `vault/jobs/*`).
- The changed file's frontmatter and body.
- `schemas/*.schema.json` — entity schemas for validation.
- `resumeos.config.yaml: vault.entities` — mapping of entity types to folder paths.
- `output/*/artifacts/assembly.json` — derived-document provenance (used to find stale docs).

## Outputs

- Enriched entity note in `vault/career/*` (delegated to `career_builder`).
- `output/.stale.json` — updated stale-marker registry listing which derived docs need
  regeneration.
- A user-facing prompt to regenerate affected docs (not persisted).

---

## Pipeline

### Step a — Infer Entity Type from Folder

- **Inputs:** the changed file's path.
- **Work:** resolve the file's parent folder against `resumeos.config.yaml: vault.entities`.
  - `vault/career/projects/*` → `project`
  - `vault/career/research/*` → `research`
  - `vault/career/competitions/*` → `competition`
  - `vault/career/internships/*` → `internship`
  - `vault/career/opensource/*` → `opensource`
  - `vault/career/awards/*` → `award`
  - `vault/career/education/*` → `education`
  - `vault/career/skills/*` → `skill`
  - `vault/jobs/*` → `job`
  - `vault/inbox/*` → handled by `career_builder`, not re-enriched here.
- If the folder cannot be mapped, report the event and skip enrichment.
- **Outputs:** the resolved `entity_type` label.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step b — Schema Validation

- **Compose:** `prompts/core/anti-hallucination.md`.
- **Work:** validate the file's frontmatter against the schema for the resolved entity type
  (`schemas/<entity_type>.schema.json`).
- If validation fails:
  - Report the exact fields that failed.
  - Ask the user to fix the frontmatter. Do not auto-correct and do not skip — the entity
    must be schema-compliant before downstream skills can consume it.
- **Outputs:** a validated entity frontmatter, or a validation error report waiting on the
  user.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step c — Enrichment via career_builder

- **Compose:** `prompts/enrich-on-change.md` + `prompts/core/anti-hallucination.md`.
- **Work:** invoke `career_builder`'s enrichment flow on the validated entity:
  - re-classify confidence,
  - detect new gaps introduced by the change,
  - emit follow-up questions for any gap,
  - on user confirmation, rewrite the entity note with validated frontmatter and preserved
    `sources[]`.
- **Outputs:** an enriched, schema-validated entity note in `vault/career/*`.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step d — Stale Detection

- **Compose:** `prompts/stale-detect.md`.
- **Work:** scan every `output/*/artifacts/assembly.json` (and equivalent assembly artifacts
  for other derived doc types). For each derived doc whose provenance references the
  changed entity (`entity_id`), mark it stale.
- Update `output/.stale.json` with the list of stale docs: path, source entity, and the
  field that changed.
- **Outputs:** an updated `output/.stale.json`.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step e — Regeneration Prompt

- **Inputs:** the stale doc list from Step d.
- **Work:** if any docs are stale, present a prompt to the user:
  - listing each stale doc and the entity change that caused it,
  - offering to regenerate each one (by re-running the relevant generator skill),
  - refusing to regenerate without the user's explicit consent.
- If no docs are stale, report "no derived docs affected" and stop.
- **Outputs:** a terminal prompt (not persisted).

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

---

## Hooks

- `onVaultChange` — declared in `plugin.json`. The runtime invokes career_update when a
  file under `vault/` is created or modified.

## Prompt Fragments

| Step | Prompt |
|------|--------|
| Stale detection | `prompts/stale-detect.md` |
| Enrich on change | `prompts/enrich-on-change.md` |

Always compose local fragments with `prompts/core/anti-hallucination.md`.

---

## Anti-hallucination Enforcement

- career_update never writes entity facts on its own; it delegates enrichment to
  `career_builder`, which is bound by ADR-0007.
- Schema validation is enforced on every change; invalid entities are not enriched or
  propagated.
- Stale detection is a read-only provenance scan — no facts are invented.

## Failure Modes

- Unmapped folder on change: report and skip.
- Schema validation failure: ask user to fix (never auto-correct).
- Missing `output/.stale.json`: create it on the first stale event.
- `career_builder` pause for follow-up: career_update surfaces the pause transparently to
  the user.
