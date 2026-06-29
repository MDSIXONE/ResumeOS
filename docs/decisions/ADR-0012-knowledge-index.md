# ADR-0012: Knowledge Index — Formal Projection Layer for Fast Skill Reads

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS lead, Runtime track
- **Related:** ADR-0001, ADR-0002, ADR-0003, ADR-0011
- **Supersedes:** none
- **Superseded by:** none

## Context

ADR-0003 (line 61–64) already permits a read-only DB cache: *"A future embedded index (e.g.
SQLite) may cache the vault for fast queries, but the vault remains the SSOT per ADR-0001. The
cache is rebuildable from the vault and is never user-editable."* ADR-0011 (Rule 7, line 93–95)
placed transient cache at `vault/.library/cache/` and established `vault/.library/` as the
library root. But neither ADR *specifies* the index — its format, location, rebuild trigger, or
the contract Skills rely on.

The force driving this now: as the vault grows past ~100 entity notes, every Skill that needs
"rank my projects" or "find awards for role X" or "dashboard of recent activity" must either
scan the whole vault (O(n) per query, slow, repeated) or lean on Dataview (only available inside
Obsidian — CLI and MCP paths can't use it). The Phase 2 UX design (`resume_tailoring` candidate
ranking, dashboard aggregation, proactive nudges) all assume fast entity lookup that a full
vault scan cannot deliver at scale.

A second force: the Phase 3 runtime adds Embedding Cache (ADR-0013), AI Memory (ADR-0020), and
Event Bus log (ADR-0014). These all need a home. ADR-0011's `vault/.library/cache/` is too
narrow a name (it implies transient OCR/hash cache, not a knowledge projection). The runtime
needs a consolidated data root with typed subfolders, or we end up with cache scattered across
`.index/`, `.cache/`, `.memory/` ad-hoc — exactly the sprawl ADR-0011's single-`.library/` rule
was meant to prevent.

## Decision

Formalize a **Knowledge Index**: a read-only, rebuildable JSON projection of the vault's
career entities, stored under `vault/.library/`, consumed by Skills for O(1) lookup. The index
is a cache, never canonical (ADR-0001/0003); the vault remains SSOT.

### Location and runtime data root

`vault/.library/` becomes the **runtime data root** with typed subfolders. ADR-0011's
`cache/` is one sibling; this ADR adds `index/`. Later ADRs add `embeddings/` (ADR-0013) and
`memory/` (ADR-0020), and `events.jsonl` (ADR-0014) sits at the `.library/` root.

```
vault/.library/
├── cache/              # ADR-0011: transient OCR/hash/parse cache (git-ignored)
├── index/              # ADR-0012: knowledge index (this ADR, git-ignored)
│   ├── knowledge-index.json
│   └── .stale.json
├── embeddings/         # ADR-0013: vector cache (git-ignored)
├── memory/             # ADR-0020: conversation memory (git-ignored)
└── events.jsonl        # ADR-0014: event bus audit log (git-ignored)
```

All of `.library/` is git-ignored (rebuildable from `vault/career/**` + `logs/`). The index is
never user-editable and never committed.

### Index format

A single JSON object at `vault/.library/index/knowledge-index.json`, validated by
`schemas/runtime/knowledge-index.schema.json`. Structure:

```json
{
  "schema_version": "1.0.0",
  "built_at": "2026-06-29T09:14:00+08:00",
  "entity_count": 47,
  "entities": {
    "projects": [
      {
        "id": "px4-uav",
        "title": "PX4 UAV Autonomous Flight",
        "type": "project",
        "folder": "vault/career/projects/",
        "path": "vault/career/projects/px4-uav.md",
        "tags": ["robotics", "px4", "autonomous"],
        "updated": "2026-07-28",
        "summary": "Autonomous drone flight with PX4 + ROS2 + YOLO detection.",
        "key_fields": {
          "role": "Lead Engineer",
          "company": "Robotics Lab",
          "timeline": {"start": "2023-08-01", "end": "2024-01-15"},
          "stack": ["PX4", "ROS2", "YOLOv8", "Python"]
        }
      }
    ],
    "awards": [ /* ... */ ],
    "research": [ /* ... */ ],
    "skills": [ /* ... */ ],
    "jobs": [ /* ... */ ]
  }
}
```

Each entity-type array mirrors a `vault.entities.*` folder from `resumeos.config.yaml`. The
`key_fields` object carries the few high-signal fields per type (role/company/stack for
projects; issuer/date for awards; DOI/venue for research; proficiency/last_used for skills).
The full frontmatter stays in the vault note; the index carries only what Skills need to
filter and rank without opening every file.

### Concrete rules

1. **Vault is canonical; the index is a projection.** Skills MUST treat
   `vault/career/**/*.md` as the source of truth. The index is an optimization for read-heavy,
   filter-heavy operations (ranking, dashboards, candidate selection). When a Skill needs the
   full, authoritative content of one entity, it reads the note, not the index.

2. **Only the indexer writes the index.** A runtime component (the indexer) owns
   `knowledge-index.json`. Skills read it; they never write it directly. A Skill that creates
   or updates an entity writes the vault note (its permitted path); the indexer picks up the
   change via the `onVaultChange` hook (ADR-0004) and updates the index.

3. **Stale flag + lazy rebuild.** When a vault write occurs, the indexer (or `career_update`
   via the `onVaultChange` hook) sets `vault/.library/index/.stale.json` with the changed
   entity ids. A Skill reading the index may (a) use the stale index for a fast approximate
   answer, or (b) trigger `resume index` to rebuild before reading. The choice is the Skill's,
   documented per Skill. `resume_tailoring` always rebuilds (correctness-critical); the
   dashboard may use stale (approximate is fine).

4. **Rebuild is explicit or debounced-auto.** `resume index` rebuilds synchronously. In watch
   mode (ADR-0011 V2), the indexer rebuilds debounced after `onVaultChange`. A deleted index
   file is regenerated from the vault on the next `resume index` or next stale-triggered
   rebuild — never a data-loss event.

5. **Scope.** The index covers `vault/career/**` and `vault/jobs/**` only. It does NOT index
   `vault/inbox/` (transient), `vault/assets/` (binaries), or `output/` (derived). Those have
   their own access patterns (import log, asset hash index).

6. **Schema versioning.** The index carries `schema_version` matching the ADR-0002 schema
   version it was built against. A schema bump invalidates the index; the next rebuild picks up
   the new shape.

7. **No SQL runtime in v1.** The index is JSON, inspectable, git-diff-friendly, and readable
   by any tool. SQLite (per ADR-0003's "future embedded index") remains a documented future
   option if the vault exceeds ~5000 notes and JSON lookup latency becomes a problem. The
   JSON→SQL swap is a runtime implementation detail; the Skill read contract (an index object
   keyed by entity type) stays stable.

## Consequences

- **Positive:** O(1) entity lookup for `resume_builder` ranking, `resume_tailoring` candidate
  selection, dashboard aggregation, and proactive nudges — no full vault scan per query.
  Foundation for semantic search (ADR-0013 embeddings are keyed by the same entity ids).
- **Positive:** Consolidates runtime data under `vault/.library/` with typed subfolders — no
  cache sprawl. ADR-0011's `cache/` becomes one sibling under a clear root.
- **Positive:** CLI and MCP paths get fast lookup without Dataview (which is Obsidian-internal
  only). The runtime works the same inside and outside Obsidian.
- **Negative:** Index can be stale between a vault write and the next rebuild — mitigated by
  the stale flag and per-Skill rebuild policy. Correctness-critical Skills rebuild; approximate
  ones tolerate stale.
- **Negative:** One more runtime component to maintain (the indexer). Accepted — the
  alternative (every Skill scanning the vault) is slower and more duplicated.
- **Neutral:** `.library/` is now the runtime data root, not just the tailoring library
  (ADR-0006). ADR-0011's `cache/` rule is unchanged in path, only broadened in siblings.

## Alternatives considered

- **Separate `vault/.index/knowledge-index.json` (user proposal).** Rejected: duplicates the
  `.library/` root ADR-0011 established and scatters runtime data across two hidden dirs.
  Consolidating under `vault/.library/index/` keeps one runtime data root with typed
  subfolders — easier to git-ignore, back up, and reason about.

- **SQLite embedded index as v1.** Rejected for now: adds a binary runtime dependency and a
  non-human-inspectable artifact. JSON is readable, diffable, and sufficient at personal-vault
  scale. SQLite remains the documented upgrade path past ~5000 notes (ADR-0003 foresaw this).

- **Dataview as the only index.** Rejected: Dataview runs inside Obsidian only. CLI
  (`resume build`), MCP servers, and headless CI cannot query it. The Knowledge Index must be
  available wherever the runtime runs.

- **Scan the vault per query.** Rejected: O(n) per query does not scale. Tailoring a resume
  already needs to rank ~20–50 projects by relevance; doing that by opening 50 files per
  generation is unacceptable and worsens as the career grows.

- **Index committed to git.** Rejected: the index is rebuildable from the vault (SSOT).
  Committing it creates a churny, merge-conflict-prone derived artifact — the same reason
  ADR-0001 git-ignores `output/`.
