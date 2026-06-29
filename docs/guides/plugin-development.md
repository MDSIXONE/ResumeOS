# Plugin Development Guide

This guide explains the ResumeOS plugin model — hooks, manifest fields, permissions, namespace
isolation, dependencies, and registration. It implements ADR-0004 (plugin system design) and
ADR-0005 (standard Skill internal structure).

> **Prerequisite:** read the [Skill authoring spec](skill-authoring-spec.md) first. This guide
> focuses on the *extension points* that sit beneath that spec.

---

## 1. The hook system

ResumeOS exposes a small set of hooks so a Skill can run code at defined moments. Hooks are
declared in `plugin.json` under the `hooks` array and namespaced by Skill name at runtime.

### Lifecycle hooks (vault events)

| Hook | Triggered when | Typical use |
|---|---|---|
| `vault.import` | A new file lands in `vault/` (typically `inbox/`) | Custom ingest adapters (PDF, LinkedIn, proprietary formats) |
| `vault.export` | A derived document is being emitted to `output/` | Custom output formats (HTML, LaTeX theme, JSON Resume extension) |
| `vault.transform` | Content is about to be rendered into a derived doc | Pre-render rewrites (locale-specific, ATS-specific) |
| `vault.validate` | An entity is being validated | Extra validation rules beyond JSON Schema |
| `vault.render` | A derived document is being rendered | Custom themes / renderers |
| `onVaultChange` | A vault file is created, modified, or deleted | React to changes — used by `career_update` |

### Tool hooks (agent-runtime events)

| Hook | Triggered when | Typical use |
|---|---|---|
| `PreToolUse` | Before an agent tool runs | Validate inputs, enforce constraints |
| `PostToolUse` | After an agent tool runs | Record provenance, update indices |

### Registering hooks

A Skill declares which hooks it subscribes to in `plugin.json`:

```json
{
  "name": "career_update",
  "version": "0.1.0",
  "hooks": ["onVaultChange"],
  "..."
}
```

The root `plugin.json` (bundle) can also wire `onVaultChange`, `PreToolUse`, and `PostToolUse` at
the bundle level:

```json
{
  "name": "resumeos",
  "type": "plugin-bundle",
  "hooks": {
    "PreToolUse": [],
    "PostToolUse": [],
    "onVaultChange": ["skills/career_update"]
  }
}
```

---

## 2. Manifest fields (`plugin.json`)

Every Skill ships a manifest validated by
[`schemas/plugin-manifest.schema.json`](../../schemas/plugin-manifest.schema.json). Required keys:
`name`, `version`, `description`. Common optional keys:

```json
{
  "name": "resume_tailoring",
  "version": "0.1.0",
  "description": "Tailor a resume to a specific job description via a phased checkpoint pipeline.",
  "type": "skill",
  "license": "MIT",
  "homepage": "https://example.com/resume_tailoring",
  "depends_on": ["resume_builder@1.0.0", "schema@1.0.0"],
  "hooks": ["onVaultChange"],
  "mcp_tools": ["browser:fetch"],
  "permissions": {
    "read":  ["vault/career/**", "vault/jobs/**"],
    "write": ["output/**", "vault/.library/**"]
  },
  "config": "<optional path to skill-specific config>",
  "prompts": "<optional override of prompts/ root>"
}
```

### Semantic versioning

`version` follows semver (`MAJOR.MINOR.PATCH`). The loader rejects a Skill whose `version` does not
parse. Breaking changes bump the major version and ship a migration note.

### `type`

Either `skill` (the default for a single Skill) or `plugin-bundle` (root bundle only).

---

## 3. Permissions model

`permissions` declares what a Skill may read and write, as path globs relative to repo root.

| Field | Meaning |
|---|---|
| `read` | Paths the Skill may read. Must include at least the entity folders it consumes. |
| `write` | Paths the Skill may write. **Generator skills may only write `output/**`; enrichment skills** (career_collector, career_builder, career_update, job_tracker) **may write vault paths**. |
| `deny` | Explicit exclusions. Always include `vault/.obsidian/**` to protect Obsidian state. |

### Least-privilege rule

A Skill must request the narrowest permissions it needs. The loader logs a warning if a Skill
declares write access to paths it never touches in its `SKILL.md` body.

### Forbidden patterns

- A generator Skill (resume_builder, resume_tailoring, cover_letter, interview, resume_review)
  writing to `vault/`.
- Any Skill writing derived documents back into the vault.
- Any Skill reading `output/**` as an input source.

---

## 4. Namespace isolation

At runtime, every Skill is namespaced `resumeos:<skill-name>`. Hooks, tools, and capabilities
exported by a Skill live under that namespace.

Example: `resume_tailoring:tailor` is distinct from a community `cover-letter:tailor` even if both
expose a `tailor` capability. This prevents collisions across the ecosystem.

The namespace also controls where a Skill's state may be written. A Skill that declares itself as
`com_example_linkedin_sync` writes only to its own namespace paths and never to core paths.

---

## 5. Dependencies (`depends_on`)

`depends_on` lists other Skills or schema versions that must be available for this Skill to load.

```json
{
  "depends_on": ["resume_builder@1.0.0", "schema@1.0.0"]
}
```

- **Skill dependency:** `"resume_builder@1.0.0"` means this Skill requires the `resume_builder`
  Skill at version `1.0.0` or compatible (semver).
- **Schema dependency:** `"schema@1.0.0"` means this Skill targets vault schema version `1.0.0`.

The loader resolves the dependency graph and fails if any dependency is missing or incompatible.

---

## 6. MCP tools

`mcp_tools` lists the MCP tools a Skill may call:

```json
{
  "mcp_tools": ["browser:fetch", "github:get_commits"]
}
```

Format: `<server>:<tool>`. A Skill may only call tools it explicitly declares in `mcp_tools`.
The MCP servers themselves are configured in `resumeos.config.yaml: mcp.servers`. See the
[MCP integration guide](mcp-integration.md) for the full contract.

---

## 7. Registering in `skills/registry.yaml`

Every Skill must appear in [`skills/registry.yaml`](../../skills/registry.yaml):

```yaml
- name: <skill-name>
  version: 0.1.0
  path: skills/<skill-name>
  enabled: true
  depends_on: ["..."]
  description: <one-liner>
```

The registry drives the bundle: when a user installs the root `plugin.json`, the loader reads the
registry to discover which Skills to load.

---

## 8. Minimal example plugin

```
skills/hello_world/
├── SKILL.md
├── plugin.json
├── README.md
└── prompts/
    └── greet.md
```

### `plugin.json`

```json
{
  "name": "hello_world",
  "version": "0.1.0",
  "description": "A minimal example Skill that greets the user.",
  "type": "skill",
  "depends_on": [],
  "hooks": [],
  "mcp_tools": [],
  "permissions": {
    "read":  [],
    "write": [],
    "deny":  []
  }
}
```

### `SKILL.md`

```markdown
---
name: hello_world
version: 0.1.0
description: A minimal example Skill that greets the user.
schema_version: 1.0.0
inputs: []
outputs: []
anti_hallucination: false
---

## Steps

1. Compose: prompts/greet.md
2. Work: greet the user warmly.
3. Output: print the greeting to the console.
```

### Register

```yaml
# skills/registry.yaml
- name: hello_world
  version: 0.1.0
  path: skills/hello_world
  enabled: false
  depends_on: []
  description: A minimal example Skill that greets the user.
```

---

## 9. Quality bar

Before submitting a Skill PR:

- [ ] `plugin.json` validates against `plugin-manifest.schema.json`.
- [ ] The Skill has a `tests/<skill>.contract.md`.
- [ ] Permissions are least-privilege.
- [ ] No prompt prose is inlined in the `SKILL.md` body.
- [ ] The Skill is registered in `skills/registry.yaml`.
- [ ] `python scripts/validate-vault.py --vault examples/vault` passes.
