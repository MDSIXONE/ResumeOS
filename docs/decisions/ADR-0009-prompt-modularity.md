# ADR-0009: Modular, Composable Prompt Files Separated from Orchestration

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers
- **Related:** ADR-0004, ADR-0005

## Context

The brief lists "Modular Prompt Files" as a first-class stack component and a design principle:
"Separate prompts from logic." In practice, LLM tools that inline prompts inside code or inside a
single monolithic SKILL.md suffer: prompts cannot be reused across skills, cannot be versioned
independently, cannot be A/B tested, and contributors must understand orchestration to tweak
wording.

## Decision

**Prompts live as small, composable Markdown fragments** under a global `prompts/` tree and a
per-skill `skills/<skill>/prompts/` tree. `SKILL.md` files contain **orchestration** (which prompts
to compose, in what order, with what inputs) — not the prompt text itself.

### Structure

```
prompts/                         # global, shared across skills
├── core/
│   ├── anti-hallucination.md    # the contract preamble (ADR-0007), included everywhere
│   ├── provenance.md            # citation rules
│   └── ask-never-invent.md      # the "ask on gap" behavior
├── analysis/
│   ├── gap-classification.md    # missing/underdeveloped/misaligned taxonomy
│   ├── ats-keyword-extract.md
│   └── company-research.md
├── generation/
│   ├── star-story.md
│   ├── bullet-rewrite.md        # reword confirmed facts only
│   └── resume-section.md
├── review/
│   ├── ats-check.md
│   └── weak-bullet-detect.md
└── interview/
    ├── behavior-question.md
    └── mock-interview.md

skills/<skill>/prompts/          # skill-local fragments
```

### Composition rules

1. A `SKILL.md` step says `Compose: prompts/analysis/gap-classification.md + prompts/core/anti-hallucination.md`.
2. Fragments declare their **inputs** (entity types / artifacts) and **outputs** (what the model
   should produce) in a small frontmatter block, so composition is auditable.
3. Global fragments are preferred; skill-local fragments are for behavior unique to one Skill.
4. Prompts are **versioned** with the repo; a Skill pins to a prompt set via `schema_version` and a
   `prompts_version` (so a past derived resume is reproducible from a Git tag).

## Consequences

- **Positive:** wording evolves without touching orchestration; fragments are reused across the 9
  Skills (e.g. `anti-hallucination.md` is included by every generation step).
- **Positive:** prompts are A/B-testable and reviewable in isolation; a prompt change is a small,
  reviewable diff.
- **Positive:** reproducibility — a derived resume is a function of (vault, prompts_version, config).
- **Negative:** more files. Justified by reuse and reviewability.

## Alternatives considered

- **Inline prompts in SKILL.md.** Rejected: no reuse, no independent versioning, large diffs.
- **Single shared prompt library with no per-skill fragments.** Rejected: some behavior is genuinely
  skill-specific; forcing it global creates awkward conditional logic.
- **Prompts as code (TS/Python builders).** Rejected: the brief specifies Markdown prompt files and
  non-code contributors should be able to edit prompts.
