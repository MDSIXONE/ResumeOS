# ADR-0001: Knowledge Base is the Single Source of Truth

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers
- **Implements:** the project's core philosophy

## Context

Every resume tool we studied splits the user's career data across form fields, a database, and the
generated document. The data dies in the tool. Reactive Resume stores it in PostgreSQL; OpenResume
in Redux/localStorage; JSON Resume in a JSON file; commercial builders in a SaaS silo. In every case
the *generated resume* and the *career knowledge* are different things stored in different places,
and the user is forced to keep them in sync by hand.

The ResumeOS brief states the inverse as a first principle:

> The knowledge base is the single source of truth. Resume, Cover Letter, Interview Preparation,
> Portfolio and Personal Website are all generated from the knowledge base. Never edit generated
> files directly. Always update the knowledge base. Everything else is derived.

## Decision

**The Obsidian vault is the single source of truth (SSOT).** All career knowledge lives as Markdown
entities with YAML frontmatter inside `vault/`. Every derived artifact — resume, cover letter,
interview pack, portfolio, personal website, job dashboard — is a **pure function** of the vault
(plus run parameters: job description, language, style). Derived artifacts live in `output/`, are
regenerable, and **must never be edited**.

### Concrete rules

1. **Vault = canonical.** `vault/career/*` and `vault/jobs/*` hold all facts. `output/*` holds none.
2. **Derived = disposable.** `output/` is git-ignored. Deleting it and re-running Skills reproduces
   it (given the same vault + prompt versions).
3. **One-way flow.** Data flows vault → output, never output → vault. Enforced by `plugin.json`
   `permissions` (Skills may not read `output/` as input).
4. **Never edit derived files.** To change a resume, change the vault, regenerate. The system
   refuses to treat an `output/` edit as canonical.
5. **Provenance.** Every entity records where its facts came from (`frontmatter.sources[]`), so the
   SSOT is auditable, not just authoritative.

## Consequences

- **Positive:** one place to maintain → no drift; derived docs are always consistent with the vault;
  the user owns their data in plain Markdown; switching tools means exporting the vault, not
  migrating a database.
- **Positive:** makes anti-hallucination enforceable — a Skill can only cite facts that exist in the
  vault (ADR-0007).
- **Negative:** the vault requires discipline (templates, schema validation). A sloppy vault
  produces sloppy derived docs — garbage in, garbage out. Mitigated by `career_builder` gap
  detection and CI frontmatter validation.
- **Negative:** regeneration cost — a big vault + many derived docs means re-running Skills. Accepted
  as the price of consistency.

## Alternatives considered

- **Database as SSOT (Reactive Resume pattern).** Rejected: requires a server, kills local-first
  privacy, and the user does not own a readable artifact.
- **Generated resume as SSOT (most builders).** Rejected: the resume is one of many derived views;
  making it canonical forces every other view to reverse-engineer it.
- **Hybrid (vault + DB mirror).** Rejected as a default: two stores invite drift. A DB *cache* over
  the vault is allowed later (ADR-0003) but the vault remains canonical.
