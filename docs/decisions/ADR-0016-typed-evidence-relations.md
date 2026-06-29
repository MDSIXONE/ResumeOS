# ADR-0016: Typed Evidence Relations — Structured Edges Alongside Untyped Wikilinks

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS lead, Runtime track
- **Related:** ADR-0001, ADR-0002, ADR-0003, ADR-0004, ADR-0007, ADR-0012
- **Supersedes:** none
- **Superseded by:** none

## Context

ADR-0003 (line 38) maps the vault's foreign keys / relations to `[[wikilink]]` in
frontmatter or body, plus `related: []` id arrays. Entity schemas (ADR-0002, see
`project.schema.json` lines 124-129) declare `related` as an **untyped** array of
note ids/titles. This is enough for Obsidian Graph View to render edges and for a human
to navigate. It is not enough for the runtime to *query by relation semantics*.

The user's Phase 2 review asked for typed evidence relations, specifically:

- **Award → 引用 → Project** — "this award recognized project X."
- **Paper → 引用 → Research** — "this paper cites that prior work."
- **Project → 引用 → GitHub** — "this project is hosted at this repo."
- More generally: "show me all evidence for project P," "list every project that derived
  from research R," "which competitions does award A correspond to?"

Untyped `related: []` cannot distinguish "this award is evidence FOR this project" from
"this project was derived FROM that research" from "this skill was used in this project."
They collapse into the same `related` item. Dataview can traverse but cannot filter by
semantic type without a frontmatter field carrying the type. The Knowledge Index
(ADR-0012) projects `tags`, `key_fields`, `summary` — without typed edges, it cannot
answer "find all evidence for X" as an O(1) index lookup; it falls back to scanning every
note's `related[]` and inferring direction from context (fragile, wrong half the time).

ADR-0003 (line 63-64) already permits read-only derived stores: *"A future embedded index
may cache the vault for fast queries, but the vault remains the SSOT."* This ADR is the
next step: the typed relation lives in the note's frontmatter so the vault itself is the
queryable graph; the Knowledge Index projects it for speed.

## Decision

Add a `relations[]` frontmatter field to all career entity schemas, **coexisting** with the
existing `related[]`. `related` remains the simple, untyped, Obsidian-native case
(backward compatible — does not break existing notes). `relations` is the typed superset
for cases where the relation's semantics carry meaning for queries, tailoring, or
evidence presentation.

### Concrete rules

1. **Schema field.** Every career entity schema gains a `relations` property (see JSON Schema
   snippet below). Array of `{type, target, note}`. `relations` is **not** required;
   schemas use `"default": []`. An entity may have `related` only, `relations` only,
   both, or neither — all four combinations are valid.
2. **Target is a wikilink.** `target` MUST be a string of the form `"[[entity-id]]"` or
   `"[[entity-id|alias]]"`. This is the constraint that keeps ADR-0003's graph intact:
   Obsidian's Graph View renders the edge regardless of whether it came from `related` or
   `relations`, so no visualization is lost. The runtime resolves the wikilink to the
   target note path via the same resolver Dataview uses.
3. **Type from a defined enum (extensible).** Initial values:

   | type | semantics | typical direction |
   |------|-----------|-------------------|
   | `evidence` | source entity is *evidence for* target | Award → Project, Competition → Project |
   | `reference` | source entity *references / cites* target | Paper → Research, Project → Project |
   | `derived_from` | source entity *was derived from* target | Project → Research, Skill → Project |
   | `part_of` | source entity *is a part of* target | Opensource → Project, Internship → Job |
   | `award_for` | source award *is awarded for* target project/competition | Award → Project, Award → Competition |
   | `author_of` | source person entity *authored* target paper/research | (person note) → Paper |
   | `contributes_to` | source entity *contributes to* target | Skill → Project, Opensource → Project |

   Community Skills adding new relation types MUST go through the ADR-0004 community
   extension process — never invent a new type inline. New types MUST be documented in
   the table above via ADR amendment before use.
4. **`note` is optional free-text context.** `null` or a short human-readable string
   explaining the relation ("awarded Q3 2025 for mAP 0.87 on val set"). Renderers that
   show the edge as a tooltip or citation use this field; traversals that don't need it
   ignore it.
5. **Anti-hallucination per relation.** ADR-0007 applies to edges as well as facts. A
   `relations` entry MUST point to a real entity — the runtime (or a Skill writing the
   relation) MUST resolve the target wikilink to an existing entity note before emitting.
   A dangling wikilink (target does not exist) is a validation warning, and the relation
   MUST NOT be emitted by a Skill until the target exists. This prevents hallucinated
   edges from polluting the Knowledge Index.
6. **`related` is preserved.** Existing notes and templates with `related: []` remain valid
   and unchanged. Do not migrate automatically. When a user or Skill authors a new note
   where relation type carries meaning, they use `relations`; for plain "these are loosely
   connected" links, they use `related`. Documented preference: `relations` for new notes
   where the type is known; `related` for ad-hoc, low-stakes connections.
7. **Knowledge Index integration (ADR-0012).** The indexer projects `relations[]` into
   two lookup structures (added to `knowledge-index.json` under a new `edges` key):
   - `outgoing[<entity-id>]` — relations declared by this entity.
   - `incoming[<entity-id>]` — relations pointing *to* this entity (reverse index).

   "Find all evidence for project X" becomes an O(1) lookup on
   `incoming["px4-uav"]` filtered to `type == "evidence" || type == "award_for"`. No
   vault scan required. Reverse index is built at index-rebuild time, mirroring ADR-0012
   rule 2 ("only the indexer writes the index") and rule 4 (rebuild on stale trigger).
8. **Event Bus integration (ADR-0014).** When a Skill or importer adds or removes a
   `relations` entry, the resulting `onVaultChange` diff produces `KnowledgeUpdated`.
   The indexer refreshes both `outgoing` and `incoming` on rebuild. Subscribers that need
   edge-level events (e.g. a future "evidence missing" nudge when a project has no
   inbound `evidence` edge) subscribe to `KnowledgeUpdated` and filter by entity id.
9. **Direction convention.** All relations are *outgoing from the source entity* — from
   the note whose frontmatter carries the `relations[]` entry, *toward* the `target`.
   Backlinks (incoming edges) are not stored redundantly in frontmatter; they are
   computed by the Knowledge Index via the reverse index (rule 7). If a future Skill
   needs to *declare* a backlink explicitly (e.g. a user says "project X is evidenced by
   award A"), they write the entry on award A's note, not on project X's.

### Scope (which schemas)

Apply to the **9 career entity schemas**: `project`, `job`, `education`, `skill`, `award`,
`research`, `competition`, `internship`, `opensource`. Same reasoning as ADR-0015 §Scope
— these are the graph nodes; these are the entities whose edges the Knowledge Index must
project.

**Exempt:**
- `vault-meta.schema.json` — vault-level metadata, not a graph node. Has no entity edges.
- `plugin-manifest.schema.json` — Skill manifest, declarative static config. Does not
  participate in the career graph.

Same assumption as ADR-0015: of the 11 schemas listed in ADR-0002, 9 are career entities
and 2 are meta. This ADR edits the 9 career schemas; the orchestrator performs the
mechanical paste below into each.

### JSON Schema snippet (paste into each career entity schema's `properties`)

```json
"relations": {
  "type": "array",
  "description": "Typed directed relations from this entity to another, via [[wikilink]]. Coexists with the untyped 'related' field (which remains for backward-compatible simple links). ADR-0016.",
  "items": {
    "type": "object",
    "additionalProperties": false,
    "required": ["type", "target"],
    "properties": {
      "type": {
        "type": "string",
        "enum": ["evidence", "reference", "derived_from", "part_of", "award_for", "author_of", "contributes_to"],
        "description": "Semantic type of the relation. Extensible via ADR-0004 community process."
      },
      "target": {
        "type": "string",
        "pattern": "^\\[\\[[^\\]]+\\]\\]$",
        "description": "Target entity as a wikilink, e.g. '[[px4-uav]]' or '[[px4-uav|PX4 project]]'. Must resolve to an existing entity note (ADR-0007 — no hallucinated edges)."
      },
      "note": {
        "type": ["string", "null"],
        "description": "Optional human-readable context for the edge (rendered as tooltip/citation). Null if no context needed."
      }
    }
  },
  "default": []
}
```

Paste location: add as a sibling of `related`, `sources`, `$resumeos` in each career
entity schema. Do not add to `required`. Do not remove or modify the existing `related`
property — both fields coexist in the schema and in notes.

### Template update

`templates/*.md` gain two additional default lines after `related: []`:

```yaml
related: []
relations: []
```

The existing `related` field is untouched. Adding `relations: []` to templates encourages
new notes to use the typed superset from the start; existing notes without `relations`
remain valid because of `"default": []`.

## Consequences

- **Positive:** "Show all evidence for project X," "list what derived from research R,"
  and "which competitions has this award been tied to?" become O(1) Knowledge Index
  lookups (rule 7) — a concrete answer to the user's Phase 2 typed-evidence ask.
- **Positive:** Vault remains the graph (ADR-0003): the wikilink-shaped `target` keeps
  Obsidian Graph View rendering every edge, typed or not. No split-store, no external
  graph DB.
- **Positive:** Backward compatible — `related[]` is unchanged, existing notes and
  templates keep working, migration is optional and organic (new notes use `relations`,
  old notes keep `related`).
- **Positive:** Enum-driven, extensible via ADR-0004 community process. New relation types
  are discoverable (read the enum), validatable (JSON Schema rejects unknowns), and
  governed.
- **Negative:** Two fields for graph edges (`related` and `relations`) — a small cognitive
  overhead. Mitigated by the documented preference (rule 6): `relations` when type
  carries meaning, `related` otherwise. The ADR explicitly refuses to force-migrate, to
  keep the overhead optional.
- **Negative:** The indexer must now maintain an `incoming` reverse index in addition to
  per-entity `outgoing`. Accepted — the reverse index is cheap to rebuild (one pass per
  rebuild) and is what makes "find evidence for X" O(1) instead of a vault scan.
  Consistent with ADR-0012's index-allocation principle (the index is rebuildable from
  vault, never SSOT).
- **Negative:** Wikilink resolution becomes a hard runtime dependency for any Skill
  writing `relations`. Accepted — the resolver is the same one Dataview uses and the
  Knowledge Index already depends on vault path resolution. Anti-hallucination (rule 5)
  turns this dependency into a safety feature rather than a cost.
- **Neutral:** The `target` pattern `^\[\[[^\]]+\]\]$` is stricter than "contains a
  wikilink somewhere" — it requires the *entire* target string to be exactly one
  wikilink. This is deliberate: one relation, one target, no ambiguity. Authors who want
  to link to multiple targets use multiple `relations` entries.

## Alternatives considered

- **Replace `related` with `relations` (breaking migration).** Rejected: invalidates every
  existing note and template; breaks the backward-compatibility guarantee implicit in
  ADR-0002 §6 ("required fields are required" — but *existing* optional fields stay
  optional). A coexistence policy preserves existing notes and allows organic migration.

- **Separate `vault/career/.relations/` graph store (one file per entity, or one monolith
  graph file).** Rejected: ADR-0003 (line 27-29) establishes the vault itself as the graph
  — frontmatter edges, not a sidecar. A `.relations/` directory would split the graph
  from the notes that carry it, creating a second sync problem and breaking the git-
  diffable, human-readable contract. The runtime already has one hidden data root
  (`.library/`, ADR-0011/ADR-0012) and that is for *rebuildable* projections only —
  canonical graph data stays in frontmatter.

- **Untyped-only `related` forever (status quo).** Rejected: does not answer the user's
  Phase 2 typed-evidence ask. "Show all evidence for X" degenerates to "open every note's
  `related[]` and heuristically classify" — fragile, wrong half the time, and violates
  the O(1) lookup guarantee ADR-0012 promises the runtime.

- **Obsidian Canvas as the only typed-relation view.** Rejected: Canvas is spatial and
  human-authored — excellent for visualization but not queryable from CLI, MCP, or CI
  paths. The runtime must work outside Obsidian (ADR-0012, ADR-0008), so the typed edge
  must live in frontmatter. Canvas can *consume* `relations[]` as a data source in a
  future plugin, but cannot be the source of truth.

- **Embed relation type in the wikilink itself (e.g. `[[px4-uav|evidence]]`).** Rejected:
  pollutes the wikilink display syntax, breaks Dataview's default wikilink parsing
  assumptions, and conflates presentation (alias) with semantics (type). A dedicated
  `relations[]` array is explicit, parseable, and does not compete with plain wikilinks
  scattered in the body.

- **Full RDF / property-graph model (subject-predicate-object triples in a separate
  store).** Rejected: over-engineered for personal-vault scale; introduces an external
  ontology the user must learn; violates ADR-0003's "one row = one note" principle. The
  7-type enum in this ADR covers every relation the Phase 2 UX review asked for;
  community extension (ADR-0004 process) handles the long tail.
