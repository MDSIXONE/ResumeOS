# ADR-0015: Entity Versioning — Field-Level History for Career Entities

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS lead, Runtime track
- **Related:** ADR-0001, ADR-0002, ADR-0003, ADR-0007, ADR-0012, ADR-0014
- **Supersedes:** none
- **Superseded by:** none

## Context

`data-lifecycle.md` §5 (Phase 2) already describes incremental entity update with version
history, merge rules, and an entity state diagram at the UX level. This ADR promotes that
pattern to an architectural decision and pins down the **schema field shape** so the runtime
can record, query, and render history — not just the UX spec.

Careers are incremental. A project's mAP metric goes 0.71 → 0.87; a skill's proficiency
grows from `beginner` to `intermediate`; an award's note learns which project it cited. A
resume regenerated six months later must reflect the current values. But the prior values
("mAP was 0.71 at the time of the 2025-03 talk") are required for:

- **provenance** — ADR-0007 forbids hallucinated facts; when a fact *changed*, the old value
  was still a fact at capture time — discarding it silently erases provenance.
- **"what did I know when" queries** — `interview_prep` and `resume_tailoring` both rely on
  the state of knowledge at a point in time to validate answers or explain trajectory.
- **audit after merge** — `career_update` merges updates from multiple sources; when a
  merge conflicts with the current value, the operator needs to see both sides.

Git versions the vault file. But git history (a) is not queryable by the runtime without
shelling out and parsing diffs, (b) is not field-level — a git diff shows which lines
changed, not *which frontmatter field was updated and why*, and (c) carries no machine-
readable **reason** (import vs. user edit vs. skill-driven update vs. merge). The runtime
needs a structured, field-level, reason-tagged history *inside* the frontmatter, next to
the entity it describes.

## Decision

Add a `history[]` frontmatter field to all career entity schemas. Each entry is a version
snapshot recording the previous values that changed, tagged with a reason. The vault note
continues to hold the current state at top-level frontmatter (ADR-0003: the note is the
present); `history[]` archives past states for provenance, queries, and merge audit.

### Concrete rules

1. **Schema field.** Every career entity schema gains a `history` property (see JSON Schema
   snippet below). It is an array of snapshot objects. `history` is **not** required;
   schemas use `"default": []` so an entity with no recorded history is still valid with
   `history: []` or with the field omitted (ADR-0002 §3 `additionalProperties: false`
   still applies — unknown keys are rejected, so once the property is in the schema, only
   the declared shape is accepted).
2. **Snapshot shape.** Each entry:
   `{version, captured_at, changed_fields, previous_values, reason}`.
   - `version` — monotonic integer per entity, starting at 1 on first programmatic update.
     `career_builder` and `career_update` increment on each merge. Hand-edits do not write
     to `history[]` (see rule 4).
   - `captured_at` — ISO 8601 datetime (ADR-0002 §5), `format: date-time`, with timezone.
   - `changed_fields` — array of frontmatter keys whose values were replaced. Top-level
     keys use dotted form for nested values (e.g. `timeline.end`, `stack.software`).
   - `previous_values` — map of `field: <previous value>`. Only fields that *actually
     changed* and whose new value was *confirmed* (ADR-0007 anti-hallucination) are
     recorded. Never inferred or fabricated values.
   - `reason` — one of: `import`, `user_edit`, `skill_update`, `merge`. See §Reason enum.
3. **Current values live at top-level frontmatter, as today.** `history[]` archives prior
   states only. The vault note is always the *present* (ADR-0003). Skills, the Knowledge
   Index (ADR-0012), and renderers read top-level fields for the current truth; they read
   `history[]` only for provenance/queries.
4. **Only programmatic writers append to `history[]`.** `career_builder` and other runtime
   writers (importers, ADR-0019) append a snapshot whenever they *update* an existing
   entity's frontmatter. Hand-edits by the user in Obsidian are versioned by git alone —
   the runtime does not instrument editor keystrokes. This is an explicit boundary: git is
   the user-edit history, `history[]` is the *runtime-action* history.
5. **Anti-hallucination applies per-field.** ADR-0007 requires confirmed facts only. A
   `previous_values` entry MUST contain a fact that was (a) actually stored in frontmatter
   at the prior version, and (b) replaced by a confirmed new value. The writer MUST NOT
   record a `previous_values` entry for a field it did not actually overwrite, and MUST
   NOT invent a prior value it did not observe.
6. **`version` is per-entity, not global.** Two entities updated in the same `career_update`
   run each increment their own `version` independently. `version == 1` means "one
   programmatic update has occurred on this entity since creation."
7. **Knowledge Index integration (ADR-0012).** The indexer MAY include the latest
   `version` and `captured_at` in `key_fields` per entity type so "stale dashboard" and
   "recent activity" queries avoid re-opening every note. Full `history[]` content stays
   in the vault note; the index carries only the summary it needs.
8. **Event Bus integration (ADR-0014).** When a writer appends to `history[]`, the
   resulting `onVaultChange` diff produces a `KnowledgeUpdated` event whose `changed_fields`
   mirror the snapshot's `changed_fields`. Subscribers (dashboard, nudges) can react to the
   domain event without re-parsing `history[]`.

### Reason enum

| value | meaning | writer |
|-------|---------|--------|
| `import` | Entity created or substantially overwritten by an importer (ADR-0019) | `inbox_ingest`, sibling importers |
| `user_edit` | Programmatic re-apply of a user-confirmed edit (e.g. `career_update` after the user answers a clarification question) | `career_update` |
| `skill_update` | A Skill derived a new value from existing confirmed facts (e.g. `ats_keywords` re-extracted) | any deriving Skill |
| `merge` | `career_builder` merged two representations of the same entity (e.g. LinkedIn import + manual note) | `career_builder` |

Community Skills adding new writers MUST pick one of these four or request a new value via
the ADR-0004 community-extension process — never invent a fifth value inline.

### Scope (which schemas)

Apply to the **9 career entity schemas**: `project`, `job`, `education`, `skill`, `award`,
`research`, `competition`, `internship`, `opensource`. These are the graph nodes ADR-0003
models as DB rows and the entities the Knowledge Index (ADR-0012) projects.

**Exempt:**
- `vault-meta.schema.json` — metadata about the vault itself (counters, last sync times),
  not a career entity. It has no per-entity provenance semantics; its own updates are
  already recorded by ADR-0014 events and git.
- `plugin-manifest.schema.json` — declarative Skill manifest, versioned by its own
  `version` field per ADR-0005. Adding `history[]` there would conflate manifest releases
  with career-entity provenance.

Assumption stated for the orchestrator: the 11 schemas listed in ADR-0002 are 9 career
entities + `vault-meta` + `plugin-manifest`. This ADR edits the 9 career schemas; the
orchestrator performs the mechanical paste below into each.

### JSON Schema snippet (paste into each career entity schema's `properties`)

```json
"history": {
  "type": "array",
  "description": "Field-level version snapshots recorded by runtime writers (career_builder, career_update, importers) on each programmatic update. Hand-edits are versioned by git alone. ADR-0015.",
  "items": {
    "type": "object",
    "additionalProperties": false,
    "required": ["version", "captured_at", "changed_fields", "previous_values", "reason"],
    "properties": {
      "version": {
        "type": "integer",
        "minimum": 1,
        "description": "Monotonic per-entity version. Incremented by the writer on each update."
      },
      "captured_at": {
        "type": "string",
        "format": "date-time",
        "description": "ISO 8601 datetime with timezone of the snapshot."
      },
      "changed_fields": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Frontmatter keys replaced in this snapshot. Nested keys use dotted form (e.g. 'timeline.end')."
      },
      "previous_values": {
        "type": "object",
        "additionalProperties": true,
        "description": "Map of field → previous value for each entry in changed_fields. Only actually-observed prior values, never inferred (ADR-0007)."
      },
      "reason": {
        "type": "string",
        "enum": ["import", "user_edit", "skill_update", "merge"],
        "description": "Why this snapshot was recorded."
      }
    }
  },
  "default": []
}
```

Paste location: add as a sibling of `related`, `sources`, `$resumeos` in each career entity
schema. Do not add to `required`. `previous_values` is `additionalProperties: true` because
the values may be any JSON type (string, number, array, object, null) depending on the
field being snapshotted — the field's own schema governs the per-value shape.

## Consequences

- **Positive:** "What did I know when?" becomes a structured frontmatter query; no git-log
  parsing, no field-diff reconstruction. `resume_tailoring` and `interview_prep` can
  validate trajectory answers against recorded prior states.
- **Positive:** Merge audit is explicit — each `reason: merge` snapshot shows the prior
  value and the confirmed replacement, directly supporting ADR-0007 provenance.
- **Positive:** History lives with the entity, so it survives vault moves, is included in
  git (unlike `.library/` rebuildables), and is readable by any tool that parses YAML
  frontmatter.
- **Positive:** Knowledge Index (ADR-0012) can surface latest `version`/`captured_at` for
  activity dashboards without re-opening every note.
- **Negative:** Frontmatter size grows with an entity's change count. Mitigated by `history`
  being optional and defaulting to `[]`; personal-vault scale (dozens to low hundreds of
  entities, each with tens of snapshots) stays well under YAML parse cost. A future
  retention policy (e.g. keep last N snapshots) can be added per-`resumeos.config.yaml` if
  needed — out of scope for v1.
- **Negative:** User hand-edits leave no `history[]` trace, only a git diff. Accepted by
  design (rule 4): instrumenting the editor would break ADR-0003's "human-readable prose"
  contract and create an arms race with Obsidian plugins.
- **Negative:** One more frontmatter key per schema to validate, migrate, and document.
  Accepted — the alternative (no history) silently loses the information this decision
  protects.
- **Neutral:** `previous_values` uses `additionalProperties: true` (the one intentional
  relaxation in a strict schema set) because values are field-polymorphic. The field-level
  schemas still govern shape; this is a map-of-any, not a free-form escape hatch.

## Alternatives considered

- **Git as the only history.** Rejected: git diffs are file-level, not field-level; not
  queryable by the runtime without shelling out and parsing; carry no machine-readable
  *reason* (import vs. merge vs. skill_update). `career_builder` merge audit in particular
  becomes fragile — two entities can share a git commit but have unrelated provenance.

- **Separate `vault/career/.history/<entity-id>.json` sidecar files.** Rejected: splits
  provenance from the entity it describes, creating a second sync problem (if the entity
  note is moved, renamed, or deleted, the sidecar must follow). ADR-0003 models the vault
  note as the row; keeping `history[]` in the same note keeps the row self-contained. The
  runtime already has one hidden data root — `.library/` (ADR-0011, ADR-0012) — and that is
  for *rebuildable* projections, not for canonical provenance.

- **Full entity snapshot per version (clone the entire frontmatter into `history[]`).**
  Rejected: storage-heavy and redundant — every snapshot duplicates unchanged fields.
  Field-level diff (`changed_fields` + `previous_values`) compresses the same information
  linearly and makes "what changed in version N" a direct read instead of a diff.

- **Overwrite-without-history (current state).** Rejected: silently discards prior facts,
  breaking provenance (ADR-0007) and making "what did I know when" queries impossible.
  Re-introducing history later would require a migration across every existing entity.

- **Event log (ADR-0014 `events.jsonl`) as the only history source.** Rejected: the event
  log is git-ignored, runtime-owned, rebuildable — the right home for *transient* domain
  events, not for durable provenance that must survive `.library/` deletion (ADR-0012 rule
  4: a deleted index is never a data-loss event; the same principle applies to history).
  `events.jsonl` records that a change happened; `history[]` records what the prior value
  *was* at that moment.
