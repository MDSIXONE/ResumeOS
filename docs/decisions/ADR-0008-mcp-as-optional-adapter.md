# ADR-0008: MCP as Optional Adapter, Never the Source of Truth

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers
- **Related:** ADR-0001, ADR-0004

## Context

The brief lists future MCP integrations: Filesystem, GitHub, Browser, Google Drive, Notion, Calendar,
Email, LinkedIn. MCP is powerful but introduces a risk: if an MCP server (e.g. a Notion or LinkedIn
adapter) becomes a place where career facts *live*, we recreate the silo problem that ResumeOS was
built to escape (ADR-0001).

## Decision

**MCP servers are optional adapters.** They are data sources and sinks at the *edge* of the system,
never the source of truth. The vault remains canonical.

### Rules

1. **Optional & runtime-discovered.** MCP servers are declared in `resumeos.config.yaml: mcp.servers`
   with `enabled` flags. ResumeOS works fully with **zero** MCP servers (local-first).
2. **Skills declare the MCP tools they may call** in `plugin.json: mcp_tools`. A Skill cannot call an
   undeclared tool.
3. **MCP never writes directly to the vault.** MCP data is ingested by a Skill (typically
   `career_collector`) into `vault/inbox/`, then enriched by `career_builder` into the vault. The
   vault boundary is preserved.
4. **MCP facts are unconfirmed until enriched.** Anything pulled from MCP lands as
   `confidence: inferred` and must be confirmed by the user before it becomes `confirmed`
   (ADR-0007).
5. **Adapters are replaceable.** Swapping a GitHub MCP server for a browser-based scraper must not
   change the vault schema or the Skills — only the adapter.

### Expected adapter roles

| MCP server | Role | Example |
|---|---|---|
| filesystem | local file ingest | PDF/DOCX into `inbox/` |
| github | ingest commit/PR/release history into a project note | `career_collector` |
| browser | company research, JD scraping for `resume_tailoring` Phase 1 | `resume_tailoring` |
| google_drive | ingest Drive docs / images | `career_collector` |
| notion | bidirectional *mirror*, not master | future plugin |
| calendar | interview scheduling for `job_tracker` | `job_tracker` |
| email | application/offer confirmation parsing | `job_tracker` |
| linkedin | profile export ingest | `career_collector` |

## Consequences

- **Positive:** ResumeOS is usable offline and privately with no MCP; power users opt in per adapter.
- **Positive:** the SSOT (vault) is insulated from external service churn or outages.
- **Positive:** adapters are swappable → no vendor lock-in.
- **Negative:** MCP coverage is extra work and lags core features. Mitigated by the plugin model:
  each adapter is an independent Skill/hook (ADR-0004).

## Alternatives considered

- **MCP as SSOT for live data (LinkedIn/Notion master).** Rejected: recreates the silo; loses
  local-first; breaks when the service is down or the user leaves it.
- **Custom per-service integrations baked into core.** Rejected: couples core to external services;
  violates the plugin model (ADR-0004).
