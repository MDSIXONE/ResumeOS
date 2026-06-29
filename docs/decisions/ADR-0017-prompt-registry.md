# ADR-0017: Prompt Registry

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS lead, Runtime track
- **Related:** ADR-0004 §4, ADR-0009

## Context

ADR-0009 established modular, composable prompt fragments with frontmatter (`fragment`, `inputs`, `outputs`, `applies`). The prompt tree has grown: 9 global fragments under `prompts/` and 27 per-skill fragments under `skills/<skill>/prompts/`, with more expected. There is no authoritative index of these fragments.

Two concrete problems emerge:

1. **Path fragility.** ADR-0009 §4 composition rule says `Compose: prompts/analysis/gap-classification.md + prompts/core/anti-hallucination.md`. Moving `anti-hallucination.md` breaks every generation step that references it by path. Skill SKILL.md files and workflow YAMLs embed file paths; a rename cascades into N edits.
2. **No reuse contract.** A community Skill author wants to compose `core.anti-hallucination`. They must know the file path, which is internal layout, not a contract. The same problem existed for Skills before ADR-0004 §4 introduced `skills/registry.yaml` as the authoritative, id-based index.

ADR-0004 §4 (line 59-62): `skills/registry.yaml` is the authoritative list of known Skills with version pins, dependencies, and enabled flags. The agent-runtime loader reads it to resolve and load Skills. ADR-0009's composition model needs the same treatment for prompts.

## Decision

A `prompts/registry.yaml` is the **authoritative index** of all prompt fragments. Skills and workflows reference prompts by **stable id** (e.g. `core.anti-hallucination`), not by file path. The runtime resolves `id` → `path` via the registry. This mirrors `skills/registry.yaml` (ADR-0004 §4) in shape, semantics, and update discipline.

### Concrete rules

1. `prompts/registry.yaml` is the single authoritative list of all prompt fragments, covering both the global tree (`prompts/core/**`, `prompts/analysis/**`, `prompts/generation/**`) and per-skill trees (`skills/<name>/prompts/**`).
2. Each registry entry carries:

   | Field | Type | Purpose |
   |-------|------|---------|
   | `id` | dotted string | Stable reference name (e.g. `core.anti-hallucination`). |
   | `version` | semver | Fragment version; breaking changes bump major. |
   | `enabled` | bool | Loader skips `enabled: false` entries (deprecation, A/B gating). |
   | `path` | string | File path relative to repo root. |
   | `description` | string | One-line summary. |
   | `inputs` | list | Artifacts the fragment consumes (from frontmatter). |
   | `outputs` | list | Artifacts the fragment produces (from frontmatter). |
   | `applies` | list | Skill ids or ADR references that use this fragment. |
   | `depends_on` | list | Other prompt ids this fragment composes (may be empty). |

3. Skills reference prompts by `id` in their `SKILL.md` and in workflow YAML composition steps, NOT by file path. The runtime resolves `id` → `path` via the registry before invoking the LLM.
4. Adding a prompt = adding a file + adding a registry entry (same discipline as ADR-0004 §4 for Skills).
5. Community prompts use the namespace prefix `com_<author>.<name>`, matching the community-entry convention in `skills/registry.yaml` (line 71-75).
6. **Version pins.** A Skill declares which prompt version it targets. Breaking prompt changes (input/output shape changes, semantic contract changes) bump the fragment version. The ADR-0004 §5 stability promise (semver, two-minor-version deprecation window) applies to prompts.
7. The registry is the **contract surface for prompt reuse** across Skills. A community Skill composes `core.anti-hallucination` without knowing its filesystem path — only its id, version, and inputs/outputs contract.
8. `depends_on` declares fragment-to-fragment composition: e.g. `generation.bullet-rewrite` depends on `core.anti-hallucination` + `core.provenance`. The runtime loads transitive dependencies in topological order.

### Id namespace mapping

| Path prefix | Id prefix | Example |
|-------------|-----------|---------|
| `prompts/core/` | `core.` | `core.anti-hallucination` |
| `prompts/analysis/` | `analysis.` | `analysis.gap-classification` |
| `prompts/generation/` | `generation.` | `generation.star-story` |
| `skills/<skill>/prompts/` | `<skill>.` | `resume_tailoring.attempt-invent` (hypothetical) |
| Community | `com_<author>.` | `com_alice.cover-letter-cn` |

## Consequences

- **Positive:** moving a prompt file requires a path edit in one place (the registry), not in every SKILL.md and workflow that referenced it.
- **Positive:** reusable contract surface — community Skills compose core fragments by id, without coupling to internal layout.
- **Positive:** version pins enable reproducibility (ADR-0009 line 55-56: a derived resume is a function of vault + prompts_version + config).
- **Positive:** `depends_on` makes composition explicit and auditable, replacing the implicit ad-hoc `Compose:` concatenation strings.
- **Negative:** one more file to maintain when adding a prompt. Justified: the cost is a 6-line YAML block; the alternative is path-fragility across N consumers.
- **Negative:** the registry and frontmatter can drift. Mitigated by a future lint rule (registry entry must match file frontmatter).
- **Neutral:** per-skill prompts get a registry entry identical to global prompts, even though most are consumed by exactly one Skill. Uniform schema is worth the minor verbosity.

## Alternatives considered

- **Path-only references (no registry).** Rejected: a rename cascades into N broken references across SKILL.md files and workflow YAML. Fragile at current scale (36 prompts); unacceptable at ecosystem scale.
- **JSON registry instead of YAML.** Rejected: `skills/registry.yaml` already uses YAML (line 1-75); two formats for structurally identical registries would be inconsistent.
- **No registry, let frontmatter stand alone.** Rejected: frontmatter lacks `version`, `enabled`, and `depends_on`. No mechanism to pin versions or disable a fragment without deleting it.
- **Registry auto-generated from frontmatter (no manual YAML entry).** Rejected: frontmatter does not carry version pins or `depends_on`, and auto-generation removes the ability to disable or pin a fragment. Manual entry is low cost at 6 lines per prompt and gives the runtime the contract it needs.
