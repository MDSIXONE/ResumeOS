# ADR-0007: Anti-Hallucination Contract — Ask, Never Invent

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers
- **Related:** ADR-0001, ADR-0006

## Context

The brief makes anti-hallucination a hard requirement:

> Never fabricate: Projects, Metrics, Awards, Responsibilities, Experience, Skills, Technologies,
> Numbers. Always ask when uncertain.

LLM resume tools hallucinate by default: to "fill" a resume they invent metrics, inflate
responsibilities, and add technologies the candidate never used. This is the single fastest way to
destroy user trust and to get a candidate fired in an interview for claiming something false. No
amount of templating fixes a model that invents facts.

We need an **enforceable** contract, not a polite request.

## Decision

Every ResumeOS Skill obeys this contract, enforced by structure and by configuration:

### 1. The contract

A Skill may only state a fact that **exists in the vault** and is **validated against its schema**.
For anything missing or uncertain, the Skill **asks the user**. It never infers, rounds, embellishes,
or invents.

### 2. Forbidden fabrications (explicit list)

Projects, metrics (numbers, percentages, durations), awards, responsibilities, experience,
skills, technologies, dates, titles, team sizes, datasets, algorithms — all must trace to a vault
field. `resume_tailoring` Phase 3 may **reword** a confirmed fact (clarity/impact) but may not
**add** a fact.

### 3. Provenance

Every entity carries `frontmatter.sources[]` (set by `career_collector`, never removed). Every
bullet in a generated resume carries a citation to `entity_id:field`. A derived resume with an
uncitable bullet is a **build failure**, not a warning.

### 4. Confidence

`career_builder` tags each fact with `confidence: confirmed | inferred | missing`. Only `confirmed`
facts flow into derived documents. `inferred` facts trigger a follow-up question; `missing` facts
trigger a gap prompt.

### 5. Rewording vs invention (the tailoring boundary)

`resume_tailoring` may:
- reorder, condense, and rephrase a confirmed bullet,
- map a confirmed skill to a JD's synonym (e.g. "PyTorch" ↔ "深度学习框架"),
- drop a bullet that is irrelevant to the JD.

It may **not**:
- add a metric that is not in the vault,
- claim a responsibility not recorded,
- list a technology not present in the entity's `stack`.

### 6. Enforcement

- `resumeos.config.yaml: defaults.anti_hallucination: true` — when true, the contract is active.
- `plugin.json` permissions forbid writing to `output/` without a validated `assembly.json` whose
  bullets all carry citations.
- CI includes a `provenance-check` that fails if a derived resume references a non-existent entity.

## Consequences

- **Positive:** trust. A ResumeOS resume is defensible in an interview — every claim traces to the
  vault.
- **Positive:** the vault becomes more valuable over time as the user fills gaps the Skill surfaces.
- **Negative:** the user must answer follow-up questions; derived resumes are conservative until the
  vault is rich. This is correct behavior, not a bug.
- **Negative:** "never invent" means a thin vault yields a thin resume. Mitigated by `career_builder`
  gap detection that actively prompts the user to record more.

## Alternatives considered

- **Best-effort generation with disclaimers.** Rejected: candidates still get burned by invented
  facts; disclaimers do not survive copy-paste into an ATS.
- **Post-hoc hallucination detector.** Rejected: catching hallucinations after generation is too
  late and unreliable; prevention via provenance is cheaper and certain.
- **Allow invention, let the user delete.** Rejected: shifts the dangerous work to the user and
  assumes they will catch every fabrication.
