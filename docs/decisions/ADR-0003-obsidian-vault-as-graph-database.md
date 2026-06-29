# ADR-0003: Obsidian Vault as a Graph Database

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers
- **Related:** ADR-0001, ADR-0002

## Context

We need a storage model for career knowledge that is (a) local-first and privacy-preserving,
(b) readable and owned by the user, (c) graph-shaped — careers are inherently relational (project
↔ skill ↔ role ↔ company ↔ competition ↔ award), and (d) navigable by a human, not just a machine.

We compared:
- **Relational DB (PostgreSQL/SQLite).** Great queries, poor human readability, requires a server or
  an embedded runtime; the user does not "own" a readable artifact.
- **Document DB / JSON files.** Readable but flat — no graph, no backlinks, no transclusion.
- **Obsidian vault (Markdown + frontmatter + backlinks + tags + Canvas).** A graph of human-readable
  notes, queryable via Dataview, scriptable via Templater, spatially modelable via Canvas, all
  local, all plain files in Git.

The Obsidian ecosystem (Projects, Dataview, Templater, Canvas, Excalidraw) already solves the
"multiple views over one data model" problem that we would otherwise build from scratch.

## Decision

**Treat the Obsidian vault as a graph database.** Every Markdown file is an entity (node);
frontmatter is structured properties; `[[wikilinks]]` and `#tags` are edges; Dataview is the query
layer; Canvas (`.canvas`) is the spatial view; Excalidraw is the free-form drawing layer.

### Mapping

| DB concept | Vault implementation |
|---|---|
| Table / collection | A folder: `vault/career/projects/`, `vault/jobs/`, … |
| Row / entity | One `.md` file with YAML frontmatter |
| Column / field | A frontmatter key, validated by `schemas/*.schema.json` (ADR-0002) |
| Foreign key / relation | `[[wikilink]]` in frontmatter or body, or an array of ids |
| Index | Dataview index (debounced, cached) |
| View | Dataview (table/board/calendar/gallery), Canvas, Excalidraw |
| Trigger | `career_update` Skill watches file events |
| Transaction | Git commit (the vault is versioned) |

### Folder convention (entity roots)

```
vault/
├── career/
│   ├── projects/        research/      competitions/
│   ├── internships/     opensource/    awards/
│   ├── education/       skills/
├── jobs/                # job applications (job_tracker)
├── inbox/               # raw imports awaiting enrichment
├── canvas/              # career-graph .canvas files
├── daily/  periodic/    # daily & periodic review notes
└── .library/            # tailoring memory (career_update / resume_tailoring)
```

Entity type is inferred from the containing folder, mapping to `resumeos.config.yaml: vault.entities`.

### A read-only DB *cache* is permitted, not canonical

A future embedded index (e.g. SQLite) may cache the vault for fast queries, but the vault remains
the SSOT per ADR-0001. The cache is rebuildable from the vault and is never user-editable.

## Consequences

- **Positive:** the user reads and edits their career as prose + properties; Git diffs are
  meaningful; the graph is navigable in Obsidian's Graph View; no server, no account, no lock-in.
- **Positive:** Dataview/Canvas/Excalidraw give us multi-view for free (the Obsidian Projects
  DataSource pattern: one DataFrame, N views).
- **Negative:** cross-note "joins" are weaker than SQL — mitigated by Dataview DQL and by Skills that
  traverse the graph in code.
- **Negative:** vault size scales with career length; very large vaults need the DB cache. Accepted.

## Alternatives considered

- **SQLite as SSOT.** Rejected: not human-readable; the user wants to own prose, not rows.
- **Notion as SSOT.** Rejected: cloud-first, not local, vendor lock-in (allowed only as an MCP
  adapter — ADR-0008).
- **JSON Resume file as SSOT.** Rejected: flat, no graph, no prose; good as an *export*, not a home.
