# ADR-0005: Standard Skill Internal Structure

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers
- **Related:** ADR-0004, ADR-0009

## Context

With 9 built-in Skills and a plugin ecosystem planned, a **fixed internal structure per Skill** is
required so that: the loader can discover and validate any Skill; contributors can drop a new Skill
in without reading the core; prompts stay separated from orchestration (ADR-0009); and permissions
are declared, not implicit.

## Decision

Every Skill folder follows this exact layout:

```
skills/<skill-name>/
├── SKILL.md            # Agent Skill standard: frontmatter + orchestration steps
├── plugin.json         # Manifest (validated against schemas/plugin-manifest.schema.json)
├── README.md           # User-facing documentation for this skill
└── prompts/            # Skill-local prompt fragments (.md); may also compose global prompts/
    ├── *.md
```

### SKILL.md frontmatter (required keys)

```yaml
---
name: <skill-name>            # matches folder name; namespaced as resumeos:<skill-name>
version: 0.1.0                # semver
description: <one line>
schema_version: 1.0.0         # vault schema version this skill targets (ADR-0002)
inputs: [<entity types this skill reads>]
outputs: [<entity types or derived kinds this skill writes>]
mcp_tools: [<optional MCP tools this skill may call>]
checkpoints: [research, gap_analysis, assembly]   # if a phased pipeline (ADR-0006)
anti_hallucination: true      # ADR-0007 contract
---
```

### plugin.json (required keys)

```json
{
  "name": "<skill-name>",
  "version": "0.1.0",
  "description": "<one line>",
  "depends_on": ["<other-skill>", "<schema-version>"],
  "hooks": ["<hook names this skill registers>"],
  "mcp_tools": ["<mcp tools>"],
  "permissions": {
    "read":  ["vault/career/**"],
    "write": ["output/**"],
    "deny":  ["vault/.obsidian/**"]
  }
}
```

### Orchestration body of SKILL.md

The prose body describes **steps**, each of which:
1. declares its inputs (entity types / artifacts) and validates them against schemas,
2. performs its work, composing prompt fragments from `prompts/` (local) and the global `prompts/`,
3. declares its outputs and where they are written (vault path or `output/` path),
4. observes the anti-hallucination contract (ADR-0007): ask, never invent,
5. emits a phase artifact if it is part of a pipeline (ADR-0006).

## Consequences

- **Positive:** a contributor reads one Skill, understands all; the loader validates every Skill
  uniformly; permission boundaries are explicit and auditable.
- **Positive:** prompts separated from orchestration → prompts evolve without touching logic, and
  prompts are reusable across Skills (ADR-0009).
- **Negative:** mild boilerplate per Skill. Mitigated by `templates/skill/` (a Skill scaffold) and
  the authoring guide `docs/guides/skill-authoring-spec.md`.

## Alternatives considered

- **Free-form Skill folders.** Rejected: unpredictable for the loader; no uniform permissions.
- **Prompts inline in SKILL.md.** Rejected: blocks reuse and prompt versioning (ADR-0009).
- **One manifest for all skills (root only).** Rejected: kills independent installability
  (ADR-0004).
