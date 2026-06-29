# ADR-0019: Importer Family — `inbox_ingest` plus sibling source importers

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS lead, Runtime track
- **Supersedes:** none
- **Superseded by:** none

## Context

ADR-0011 Rule 10 introduced `inbox_ingest` as the Tier-1 Skill owning the physical file lifecycle for items dropped into `vault/inbox/`: hash → dedup → classify → OCR/extract → move to Assets → log → staged pointer. The cli-specification §2 defines `resume import [path]` as dispatching `inbox_ingest` + `career_collector`, and §6 pins the `inbox_ingest` manifest block (permissions, reads, writes).

The Phase 2 review observed that `inbox` is one entry point, not the only one. Anticipated sources — `resume import github`, `resume import notion`, `resume import drive` — are distinct systems with distinct adapters (MCP tools, browser scrapers, OAuth flows). The question: do we RENAME `inbox_ingest` to a generic `importer`, or keep it and add SIBLING importers?

Forces:

1. **ADR-0011 is a signed contract.** Rule 10 named `inbox_ingest`; the cli-specification §6 manifest is written against that name. Renaming breaks both.
2. **ADR-0004 requires independent installability.** Each importer must be its own plugin — installable, removable, and replaceable without touching core.
3. **ADR-0005 fixes the skill structure.** Every importer must follow SKILL.md + plugin.json + README.md + prompts/.
4. **Single handoff point.** All importers must produce the same output contract so `career_collector` can consume them uniformly. Writing directly to `vault/career/**` would violate `career_collector`'s single responsibility (ADR-0011 Rule 10).
5. **Cross-source dedup.** The hash index (ADR-0011, data-lifecycle §3) is shared. A README fetched via `github_importer` and the same README dropped into `vault/inbox/` must be detected as duplicates.

## Decision

`inbox_ingest` is NOT renamed. It is the inbox-specialized importer in a FAMILY of importer plugins. Each importer source is a separate Tier-1 Skill following ADR-0005 structure. All importers share a common contract: they write staged pointers into `vault/inbox/` and hand off to `career_collector`. The CLI `resume import <source>` dispatches to the matching importer.

### Concrete rules

1. **`inbox_ingest` remains the inbox/file-drop importer.** ADR-0011 Rule 10 is unchanged. It owns the physical file lifecycle for files dropped into `vault/inbox/`.

2. **A new importer is a sibling Tier-1 Skill.** `skills/github_importer/` (example) contains the full ADR-0005 structure: SKILL.md + plugin.json + README.md + prompts/. It is registered in `skills/registry.yaml` like any other Skill. Adding an importer = adding an entry + a folder; the core never changes (ADR-0004 §4).

3. **Common contract — single handoff point.** ALL importers (including `inbox_ingest`) write staged source pointers into `vault/inbox/`. `career_collector` then builds notes from the pointers. No importer writes directly to `vault/career/**` (enforced by plugin.json `deny`, rule 10).

4. **Source-specific adapters via MCP.** Each importer uses the MCP tools appropriate to its source: `github_importer` uses `github:get_commits` / `github:get_repo`; `notion_importer` uses a notion MCP adapter; `linkedin_importer` uses a browser/scrape adapter. Each declares its `mcp_tools` in plugin.json per ADR-0008. An importer with no configured MCP adapter is disabled (ADR-0008 optional — the runtime degrades gracefully).

5. **CLI dispatch.** The CLI maps `resume import <source>` to the importer Skill via `resumeos.config.yaml: importers` mapping:

   | CLI invocation | Dispatched Skill | Notes |
   |----------------|------------------|-------|
   | `resume import` (no source) | `inbox_ingest` | Default — processes items waiting in `vault/inbox/` |
   | `resume import github` | `github_importer` | Fetches commits, repos, PRs via MCP |
   | `resume import notion` | `notion_importer` | Pulls notion pages via MCP adapter |
   | `resume import drive` | `drive_importer` | Lists/drive files via MCP adapter |
   | `resume import scholar` | `scholar_importer` | Fetches publications via MCP/scrape |
   | `resume import linkedin` | `linkedin_importer` | Scrapes profile via browser adapter |

6. **Naming convention.** Importer skills are named `<source>_importer` (snake_case, matching the existing skill naming convention from ADR-0005). `inbox_ingest` is the sole exception — it predates this ADR and ADR-0011 Rule 10 named it; we do not rename.

7. **Events.** Each importer emits an `ImportCompleted` event (ADR-0014) on finishing a source fetch. Payload: `source` (github / notion / inbox / ...), `entity_id`, `status` (success / partial / error). Subscribers (indexer, dashboard) react uniformly regardless of source.

8. **Shared dedup.** The hash index is shared across all importers (ADR-0011, data-lifecycle §3). A GitHub README imported via `github_importer` and the same README dropped into `vault/inbox/` are detected as duplicates by SHA-256. No importer maintains its own dedup store.

9. **Open family.** Community importers follow ADR-0004 namespacing: `com_<author>_<source>_importer`. The core never changes to add an importer. Registry + manifest-first discovery (ADR-0004 §2/§4) applies.

10. **Permissions boundary.** Each importer's plugin.json declares permissions matching `inbox_ingest`'s boundary (cli-specification §6):

    | Permission | Globs | Rationale |
    |------------|-------|-----------|
    | `read` | source-specific (e.g. `github:*` MCP, local `vault/inbox/**` for inbox) | Read from the source, not the vault graph |
    | `write` | `vault/inbox/**` | Staged pointers — the single handoff point |
    | `deny` | `vault/career/**`, `output/**` | Importers never touch the knowledge graph or derived output |

### Initial importer family

| Source | Skill name | MCP tools | Status |
|--------|-----------|-----------|--------|
| Inbox (file drop) | `inbox_ingest` | none (filesystem) | Specified — ADR-0011 Rule 10, cli-spec §6 |
| GitHub | `github_importer` | `github:get_commits`, `github:get_repo`, `github:get_pr` | Future — Phase 4+ |
| Notion | `notion_importer` | `notion:get_page`, `notion:list_database` | Future — Phase 4+ |
| Google Drive | `drive_importer` | `drive:list`, `drive:get_file` | Future — Phase 4+ |
| Google Scholar | `scholar_importer` | scrape / MCP adapter | Future — Phase 4+ |
| LinkedIn | `linkedin_importer` | browser/scrape adapter | Future — Phase 4+ |

## Consequences

- **Positive:** `resume import <source>` is a natural CLI extension. Each source is an independent installable plugin (ADR-0004) — users install only the importers they need.
- **Positive:** ADR-0011 contract is preserved. `inbox_ingest` name, manifest, and behavior are untouched. No migration cost.
- **Positive:** Single handoff point (`vault/inbox/` staged pointers) keeps `career_collector` single-responsibility. Adding a source does not require changes to downstream Skills.
- **Positive:** Shared dedup across sources prevents duplicate knowledge entries regardless of entry path.
- **Positive:** `ImportCompleted` events (ADR-0014) let the indexer, dashboard, and any future subscriber react uniformly — source-agnostic.
- **Negative:** Multiple importer plugins means more manifests to maintain and more MCP adapter configurations to document. Mitigated by `templates/skill/` scaffold (ADR-0005) and the importer naming convention (rule 6).
- **Negative:** `inbox_ingest` name is inconsistent with `<source>_importer` convention. Accepted as historical debt — renaming would break ADR-0011 and cli-spec §6.
- **Neutral:** The family is open-ended; the initial table (above) is indicative, not exhaustive. Community importers fill the gap.
- **Neutral:** Each importer's MCP adapter must be installed and configured separately. An unconfigured adapter disables the importer (ADR-0008 optional) — no runtime error, just a clear "adapter not available" status.

## Alternatives considered

- **Rename `inbox_ingest` to a generic `importer`.** Rejected: breaks the ADR-0011 Rule 10 contract and the cli-specification §6 manifest block. Migration cost is unjustified when siblings achieve the same goal.
- **One mega-importer with source-specific plugins inside.** Rejected: violates ADR-0004 independent-installable principle. A monolithic importer concentrates risk and prevents users from installing only the sources they need.
- **Importers write directly to `vault/career/**`.** Rejected: violates the single handoff point (rule 3) and `career_collector`'s single responsibility (ADR-0011 Rule 10). Would create N write paths into the knowledge graph — untestable and un-auditable.
- **No family concept; extend `inbox_ingest` to handle all sources.** Rejected: conflates file-drop lifecycle with API/scrape adapters. Violates ADR-0004 (cannot independently install `github_importer` without `inbox_ingest`). `inbox_ingest` would become a god-skill.
- **Each importer maintains its own dedup index.** Rejected: duplicates across sources would go undetected. A GitHub README and the same file dropped into inbox would produce two knowledge entries. The shared hash index (rule 8) is the correct design.
