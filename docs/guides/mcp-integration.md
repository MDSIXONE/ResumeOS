# MCP Integration Guide

This guide explains how ResumeOS integrates with external services via the Model Context Protocol
(MCP). It implements [ADR-0008](../decisions/ADR-0008-mcp-as-optional-adapter.md) (MCP servers are
optional adapters, never the source of truth).

---

## 1. The rule

**MCP never writes directly to the vault.** All MCP data flows through a Skill (typically
`career_collector` or `career_builder`) before reaching the vault. The vault boundary is preserved
(ADR-0001).

MCP facts are unconfirmed until enriched. Anything pulled from MCP lands with
`confidence: inferred` and must be confirmed by the user before it becomes `confirmed` (ADR-0007).

---

## 2. Declaring MCP tools in `plugin.json`

A Skill declares which MCP tools it may call in its `plugin.json`:

```json
{
  "name": "resume_tailoring",
  "mcp_tools": ["browser:fetch"],
  "..."
}
```

Format: `<server>:<tool>`. The server name must match a key in `resumeos.config.yaml: mcp.servers`.
The tool name must match a tool exposed by that server.

A Skill may only call tools it explicitly declares. The loader rejects undeclared tool calls.

---

## 3. Configuring MCP servers in `resumeos.config.yaml`

MCP servers are declared under `resumeos.config.yaml: mcp.servers` with `enabled` flags:

```yaml
mcp:
  servers:
    filesystem:
      enabled: true
      scope: vault
      config:
        # filesystem-specific config (e.g. allowed paths)
    github:
      enabled: false
      config:
        token_env: GITHUB_TOKEN
    browser:
      enabled: false
      config:
        # browser-specific config
    google_drive:
      enabled: false
      config:
        credentials_file: secrets/gdrive.json
    notion:
      enabled: false
      config:
        token_env: NOTION_TOKEN
```

- `enabled: true` means the server is available at runtime.
- `enabled: false` means the server is not loaded (ResumeOS works fully with zero MCP servers).
- `config` holds server-specific configuration (tokens, paths, etc.).

Secrets (tokens, credentials) should be stored in environment variables or a `secrets/` folder
(git-ignored).

---

## 4. Expected adapter roles

| MCP server | Role | Example usage |
|---|---|---|
| `filesystem` | Local file ingest | PDF/DOCX → `vault/inbox/` |
| `github` | Ingest commit/PR/release history | `career_collector` enriches a project note with GitHub data |
| `browser` | Company research, JD scraping | `resume_tailoring` Phase 1 research |
| `google_drive` | Ingest Drive docs / images | `career_collector` stages Drive files |
| `notion` | Bidirectional mirror (not master) | Future: sync Notion pages to `vault/` |
| `calendar` | Interview scheduling | `job_tracker` creates calendar events |
| `email` | Application/offer confirmation parsing | `job_tracker` updates job status |
| `linkedin` | Profile export ingest | `career_collector` stages LinkedIn data |

Each adapter is replaceable. Swapping a GitHub MCP server for a browser-based scraper must not
change the vault schema or the Skills — only the adapter.

---

## 5. YAML snippet example

A minimal `resumeos.config.yaml` with two MCP servers enabled:

```yaml
mcp:
  servers:
    filesystem:
      enabled: true
      scope: vault
    browser:
      enabled: true
```

A Skill that uses those servers:

```json
{
  "name": "resume_tailoring",
  "mcp_tools": ["filesystem:read_file", "browser:fetch"],
  "permissions": {
    "read": ["vault/career/**"],
    "write": ["output/**"]
  }
}
```

The Skill can now read local files and fetch web pages, but it cannot write to the vault (only to
`output/`). If it needs to ingest data into the vault, it must call `career_collector` or
`career_builder`.

---

## 6. The ingest flow

```
External service → MCP server → Skill (career_collector) → vault/inbox/
                                                              ↓
                                                     career_builder
                                                              ↓
                                                     vault/career/<entities>/
                                                     (confidence: confirmed)
```

The Skill stages the MCP data in `inbox/` with `confidence: inferred`. The user (or
`career_builder`) reviews and confirms the data, moving it to `vault/career/<entities>/` with
`confidence: confirmed`.

---

## 7. What never happens

- An MCP server writing directly to `vault/career/` or `vault/jobs/`.
- A Skill reading MCP data and using it in a derived document without confirming it first.
- A Skill calling an undeclared MCP tool.
- MCP becoming the source of truth (the vault is always canonical — ADR-0001).

---

## 8. Testing MCP integrations

MCP adapters should be tested separately from Skills. The Skill's behavior contract
(`tests/<skill>.contract.md`) should describe what happens when:

- The MCP server is available and returns valid data.
- The MCP server is unavailable (Skill should degrade gracefully).
- The MCP server returns malformed data (Skill should reject it and ask the user).

The validator (`scripts/validate-vault.py`) does not test MCP integrations; it only validates the
vault after MCP data has been ingested and enriched.

---

## 9. Future adapters

The `ROADMAP.md` lists planned adapters (LinkedIn, Notion, Drive, Calendar, Email). Each adapter
is an independent Skill or hook (ADR-0004). To contribute a new adapter:

1. Write the adapter as an MCP server (follow the MCP spec).
2. Add it to `resumeos.config.yaml: mcp.servers` with `enabled: false`.
3. Write a Skill (or extend an existing one) that declares the adapter in `mcp_tools`.
4. Add a behavior contract describing the ingest flow.
5. Document the adapter in this guide.
