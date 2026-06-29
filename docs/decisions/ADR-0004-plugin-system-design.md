# ADR-0004: Plugin System Design — Skills as independently installable plugins

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers
- **Related:** ADR-0001, ADR-0005

## Context

The brief requires ResumeOS to be an **ecosystem**, not a single project: every Skill must be
independently installable, removable, and replaceable, and future developers must add new Skills
without modifying the core.

We compared three extension systems:

- **Claude Code** — `.claude-plugin/plugin.json` manifest + `SKILL.md`; namespace isolation
  `plugin:skill`; load order Enterprise > Personal > Project > Bundled. Manifest-first → excellent
  discoverability and tooling. The only model with built-in conflict resolution via namespacing.
- **OpenCode** — code-first, no manifest, JS/TS hook system with 10+ lifecycle hooks. Simpler, but
  no built-in conflict resolution.
- **Obsidian plugins** — `manifest.json`, vault-scoped sandbox, lifecycle `onload/onunload`.
  Community distribution model.

The strong pattern across all three: **manifest-first discovery + hook-based extension points +
namespace isolation.** The weak pattern in many OSS projects: plugin system as afterthought, where
breaking changes destroy ecosystem trust.

## Decision

ResumeOS is a **plugin-based platform**. The core is a registry + a hook bus + shared schemas; every
feature is a Skill plugin.

### 1. Two-tier extensibility

- **Tier 1 — Agent Skills (AI):** the primary extension unit. Each Skill is an Agent-Skill-standard
  `SKILL.md` (Claude Code / OpenCode compatible) plus a `plugin.json` manifest plus local prompts.
  These are the 9 built-in Skills and the expected form for community Skills.
- **Tier 2 — Hooks (code):** an OpenCode-inspired hook bus for programmatic extension points:
  - `vault.import` — custom ingest adapters (LinkedIn, Indeed, PDF parsers)
  - `vault.export` — custom export formats (HTML, DOCX, LaTeX, JSON Resume)
  - `vault.transform` — pre-render content transformations
  - `vault.validate` — custom validation rules beyond JSON Schema
  - `vault.render` — custom renderers / themes
  - `onVaultChange` — react to vault file events (used by `career_update`)

### 2. Manifest-first

Every plugin ships a `plugin.json` (validated by `schemas/plugin-manifest.schema.json`) declaring:
`name`, `version`, `description`, `dependencies` (other Skills or schemas), `hooks`, `mcp_tools`,
`permissions` (read/write/deny globs), and `skills` (for a bundle, the list of included skills).

### 3. Namespace isolation

Hooks and Skill-provided capabilities are namespaced `plugin-name:capability` to prevent collisions
across the ecosystem (the Claude Code pattern). E.g. `resume_tailoring:tailor` is unambiguous even
if a community `cover_letter` plugin also exposes a `tailor` capability.

### 4. Registry

`skills/registry.yaml` is the authoritative list of known Skills with version pins, dependencies,
and enabled flags. The agent-runtime loader reads it to resolve and load Skills. Adding a Skill =
adding an entry + a folder; the core never changes.

### 5. Stability promise

- The plugin API is semver'd. Breaking changes bump the major version and ship a migration guide.
- Deprecation warnings appear two minor versions before removal.
- Core schemas are also semver'd (ADR-0002); a Skill declares the schema version it targets.

## Consequences

- **Positive:** new Skills extend without touching core → ecosystem growth is unconstrained by the
  maintainers' bandwidth.
- **Positive:** users install only what they need (e.g. a researcher installs `career_collector` +
  `resume_builder` + `interview`; a job-seeker adds `resume_tailoring` + `job_tracker`).
- **Positive:** manifest-first enables future tooling (a plugin marketplace, dependency resolution,
  permission auditing).
- **Negative:** more upfront design surface than a monolith. Justified by the ecosystem goal.
- **Negative:** API stability discipline is now a permanent obligation. Accepted.

## Alternatives considered

- **Monolithic skills directory, no manifests.** Rejected: no discoverability, no dependency
  resolution, no permission boundaries — exactly the "afterthought plugin system" anti-pattern.
- **Code-only plugins (OpenCode style), no manifest.** Rejected: simpler but no conflict resolution
  and poor tooling. We adopt OpenCode's hooks but keep manifests.
- **Single mega-Skill.** Rejected: violates the "independently installable/removable" requirement
  and concentrates risk.
