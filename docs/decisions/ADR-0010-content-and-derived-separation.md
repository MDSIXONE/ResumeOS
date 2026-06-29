# ADR-0010: Content and Derived Output Live in Different Trees

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers
- **Related:** ADR-0001

## Context

ADR-0001 establishes the vault as SSOT and `output/` as derived. The risk is operational: if derived
documents live *inside* the vault (e.g. `vault/career/projects/X/resume.md`), users will edit them
directly, the vault and the derived doc drift, and the "never edit derived files" rule becomes
unenforceable because the boundary is invisible.

## Decision

**Two physically separate trees**, enforced by layout and by `plugin.json` permissions:

| Tree | Path | Canonical? | Git-tracked? | Editable by user? |
|---|---|---|---|---|
| **Content** (vault) | `vault/` | yes (SSOT) | yes | yes — this is the point |
| **Derived** (output) | `output/` | no — regenerable | no (git-ignored) | no — regenerate instead |
| **Examples** | `examples/` | no — fixtures | yes | no — they are reference fixtures |

### Rules

1. **`output/` is git-ignored.** It is a build artifact, not a source. Reproducible from vault +
   prompts + config.
2. **`examples/` is the only place "derived-looking" content is committed.** It ships a complete
   example vault + example derived outputs as *fixtures* for tests, docs, and onboarding — clearly
   labeled as examples, not the user's real data.
3. **`plugin.json` permissions** forbid Skills from writing derived docs into `vault/` and forbid
   reading `output/` as input.
4. **`career_update` marks stale derived docs** in `output/.stale.json` when their source entities
   change, then prompts the user to regenerate. It never auto-overwrites without consent.

## Consequences

- **Positive:** the boundary is visible and physical — a user cannot accidentally edit a derived
  resume thinking it is canonical.
- **Positive:** `output/` can be blown away and rebuilt with no loss; Git history stays clean.
- **Positive:** `examples/` gives contributors reproducible fixtures without polluting `output/`.
- **Negative:** users must learn the vault/output distinction. Mitigated by the vault README and
  Obsidian setup guide.

## Alternatives considered

- **Derived docs inside the vault, marked `derived: true`.** Rejected: invisible boundary; users
  edit anyway; drift is inevitable.
- **Single tree with a `.derived/` subfolder.** Rejected: still inside the vault; same drift risk.
- **No `examples/` tree; only `output/`.** Rejected: no committed fixtures for tests/docs/onboarding.
