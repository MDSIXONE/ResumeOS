# ADR-0000: Use Markdown Architectural Decision Records (MADR)

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers

## Context

ResumeOS is a long-lived open-source project with many interconnected design choices (schema
strategy, plugin model, pipeline shape, anti-hallucination contract). Without a record of *why*
each choice was made, future contributors will reverse-engineer intent from code — slowly and
incorrectly — and will repeat decisions already considered and rejected.

We compared:
- **MADR** (Markdown Architectural Decision Records) — lightweight Markdown templates, one file per
  decision, immutable once Accepted.
- **ear/ADR** (Michael Nygard's original) — terse text format.
- **Structurizr / C4-as-code** — diagrams, not decisions.
- **Notion / wiki decision logs** — external, drifts from the repo.

## Decision

Adopt **MADR** as the decision-record format for ResumeOS. Every major design decision gets one ADR
file under `docs/decisions/ADR-NNNN-<slug>.md`.

### Rules

1. **Numbering:** zero-padded, monotonically increasing (`ADR-0001`, `ADR-0002`, …).
2. **Immutability:** once an ADR is `Accepted`, its content is not edited. Supersession creates a new
   ADR that links back (`Supersedes ADR-NNNN`) and the old ADR's status becomes `Superseded`.
3. **Statuses:** `Proposed` → `Accepted` | `Rejected` | `Deprecated` → (optionally) `Superseded`.
4. **Template:** see `adr-template.md`. Sections: Context, Decision, Consequences, Alternatives.
5. **Linking:** architecture docs and Skill specs link to the ADRs that justify them.
6. **CI:** a check ensures every `docs/decisions/ADR-*.md` matches the template sections.

## Consequences

- **Positive:** decisions are versioned with the code; `git blame` on an ADR shows when/why intent
  changed; new contributors read rationale instead of guessing.
- **Negative:** small ongoing overhead to write an ADR per non-trivial decision.
- **Neutral:** ADRs are prose, not executable — they guide, they do not enforce.

## Alternatives considered

- **Nygard ADRs** — rejected: too terse for an ecosystem that needs consequences + alternatives.
- **C4-only** — rejected: C4 records structure, not the *why*; we use both.
- **Wiki decision log** — rejected: lives outside the repo, drifts, lacks review history.
