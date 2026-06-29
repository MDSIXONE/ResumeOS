# ADR-0002: Schema Strategy — JSON Schema superset of JSON Resume, strict frontmatter

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers
- **Related:** ADR-0001, ADR-0003

## Context

We studied four schema approaches:

- **JSON Resume** — a static `schema.json` hand-edited since 2014 (v1.0.0, stagnant). All fields
  optional, so themes cannot rely on any shape and must defend everywhere. Uses deprecated
  `definitions` instead of `$defs`.
- **Reactive Resume** — Zod schemas as source of truth, code-generating DB types and API validation.
  Excellent maintainability, but tied to a TypeScript/React/PostgreSQL stack.
- **OpenResume** — implicit TypeScript types, no real schema, unmaintained.
- **Universal Resume** — Effect.ts schemas → generated JSON Schema. Proves auto-generation works.

ResumeOS is **Obsidian + Markdown + YAML frontmatter**, not a TypeScript app. The schema must
validate frontmatter that lives inside `.md` files, be human-readable, and work with non-JS tooling
(CI, Obsidian plugins, future MCP servers). But we must not repeat JSON Resume's "everything
optional" mistake, and we must stay portable to the JSON Resume ecosystem.

## Decision

1. **Format: JSON Schema (draft 2020-12)** for every entity type, stored under `schemas/`. One file
   per entity: `project.schema.json`, `job.schema.json`, `education.schema.json`, `skill.schema.json`,
   `award.schema.json`, `research.schema.json`, `competition.schema.json`, `internship.schema.json`,
   `opensource.schema.json`, plus `plugin-manifest.schema.json` and `vault-meta.schema.json`.
2. **Superset of JSON Resume.** The resume entity maps to JSON Resume 1.0.0 and round-trips through a
   converter. ResumeOS adds required fields and extension points without breaking compatibility:
   - Required: `name` (basics), `email` (basics), at least one work/position entry.
   - Extension: a `$resumeos` map for ResumeOS-specific metadata (entity ids, tags, provenance,
     confidence, library hints). JSON Resume tools ignore it; ResumeOS tools use it.
3. **Strict frontmatter.** Each entity note's YAML frontmatter MUST validate against its schema.
   `additionalProperties: false` by default (configurable to `true` for gradual adoption). Unknown
   keys are rejected, preventing schema drift.
4. **Versioning.** Every schema carries `$schema` (the JSON Schema dialect) and `$id` with a
   semver path (`/schemas/1.0.0/project.schema.json`). Breaking changes bump the major version and
   ship a migration note under `schemas/migrations/`.
5. **Dates are ISO 8601.** `YYYY-MM-DD` enforced via `format: date`.
6. **No hand-waving optional-everything.** Required fields are required. This is the explicit
   rejection of JSON Resume's fragility.

## Consequences

- **Positive:** frontmatter is machine-validated by CI and by Skills before use → no "garbage entity"
  silently corrupts a derived resume. Themes/renders can rely on shape. Portable to JSON Resume via
  the converter.
- **Positive:** schemas are tool-agnostic — a Python validator, an Obsidian plugin, or an MCP server
  can all consume them.
- **Negative:** stricter than JSON Resume, so some legacy JSON Resume files need a migration pass
  (the converter emits warnings, not errors, for missing required fields).
- **Negative:** maintaining JSON Schema by hand has some overhead. Mitigation: schemas are small,
  one-per-entity, and covered by round-trip tests.

## Alternatives considered

- **Zod/Effect as SSOT, generate JSON Schema.** Rejected as the *primary* form: ResumeOS is not a
  TS app, and the vault must be validatable by non-JS tooling. A future `@resumeos/schema` package
  may wrap these JSON Schemas in Zod for TS consumers — but JSON Schema is canonical.
- **Pure JSON Resume.** Rejected: all-optional fields make rendering defensive and fragile; no
  extension mechanism for provenance/confidence.
- **Free-form frontmatter (no schema).** Rejected: violates ADR-0001 — an unvalidatable SSOT is not
  trustworthy.
