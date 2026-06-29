---
name: interview
version: 0.1.0
description: Generate a complete interview preparation pack covering behavior, technical, and project-deep-dive questions with STAR answers, weakness analysis, and a mock interview script.
schema_version: 1.0.0
inputs: [project, education, skill, job]
outputs: [derived-interview-prep]
mcp_tools: []
anti_hallucination: true
---

# interview

Generate a comprehensive interview preparation pack for a candidate, grounded entirely in vault-confirmed facts. The pack equips the candidate to rehearse real questions they are likely to face, answered from real project data they actually own.

Every fact emitted traces to the vault (ADR-0007). A gap in the vault is surfaced to the candidate as a rehearsal target, not papered over with a fabricated answer.

This is a single-pass generator, not a phased pipeline. No checkpoints.

---

## Inputs

1. Vault entities: `project`, `education`, `skill` (required). `job` (optional — when provided, targets the pack to a specific role; when omitted, generates a general prep pack).
2. Run parameters:
   - `language` (zh | en)

## Outputs (written to `output/<job-slug-or-general>/`)

- `interview-prep.md` — the full prep pack in a single Markdown file.

---

## Steps

### Step 1 — Read vault entities (and optional JD)

- Read `project`, `education`, `skill` entities from `vault/career/*`. Validate each against its schema; skip invalid entities and report them.
- If a `job` entity / JD is provided, extract the role's stated requirements and technical stack. This is the targeting vector; it does not change the grounded-facts rule.

### Step 2 — Generate behavior questions (grounded in REAL projects)

- **Compose:** `skills/interview/prompts/behavior-question.md` + `prompts/core/anti-hallucination.md`.
- Generate 6-10 behavior questions drawn from the candidate's real project history (e.g., "Tell me about a time you debugged a production issue" -> grounded in `px4-uav:contribution`, not an invented scenario).
- Do NOT fabricate hypothetical scenarios the candidate has never lived.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 3 — Generate technical questions (from entity stack fields)

- **Compose:** `skills/interview/prompts/technical-question.md` + `prompts/core/anti-hallucination.md`.
- Generate 8-15 technical questions from the entity `stack` fields (languages, frameworks, tools actually used in the vault).
- Questions must probe real competence: depth questions for primary stack items, breadth questions for secondary ones.
- Do NOT invent a skill the candidate has not confirmed.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 4 — Generate project-deep-dive questions (per project)

- **Compose:** `skills/interview/prompts/project-question.md` + `prompts/core/anti-hallucination.md`.
- For each project entity with confirmed details, generate 2-4 deep-dive questions: architecture decisions, the candidate's specific contribution, trade-offs, metrics, what went wrong.
- Questions must be grounded in the project entity's actual fields.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 5 — Produce STAR answers (confirmed fields only)

- **Compose:** `prompts/generation/star-story.md` + `prompts/core/anti-hallucination.md`.
- For each behavior and project question, draft a STAR answer.
- STAR structure: Situation, Task, Action (what YOU did, first person), Result (from `metrics` ONLY).
- If a Result metric is missing from the entity, do NOT fabricate one. Instead emit an `ask-never-invent` placeholder: `[GAP: the vault does not record a result for <entity_id>. Confirm a metric before rehearsing this answer.]`
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 6 — Weakness analysis (thin vault areas)

- **Compose:** `skills/interview/prompts/weakness-analysis.md` + `prompts/core/anti-hallucination.md`.
- Identify thin areas in the vault the candidate should prepare for:
  - Projects with no result metric.
  - Roles described only shallowly (e.g., "contributed" with no specifics).
  - Technical gaps vs the JD if a JD was provided.
  - Employment / timeline questions the vault cannot answer.
- For each weakness, frame the question the interviewer might ask + guidance on how to answer honestly (what to say, what to skip, what to ask the user to record in the vault).
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 7 — Mock interview script

- **Compose:** `skills/interview/prompts/mock-interview.md` + `prompts/core/anti-hallucination.md`.
- Produce a rehearsed Q&A script: 8-12 questions mixing behavior, technical, and project-deep-dive, with suggested answers drawn from the STAR outputs in Step 5.
- Annotate each answer with its vault source so the candidate can verify.
- Flag any answer that depends on a vault gap (noted in Step 6) so the user knows what to fill in before rehearsing.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 8 — Write the output

- Assemble Steps 2-7 into `interview-prep.md`.
- Write to `output/<job-slug>/interview-prep.md` (if a JD was provided) or `output/general/interview-prep.md` (otherwise).
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

---

## Anti-hallucination enforcement

- Every STAR answer must be built from confirmed entity fields only. If a STAR element (Situation, Task, Action, or Result) is missing, the missing element becomes a follow-up question, not a fabricated sentence.
- Technical questions probe only confirmed stack items. Do not generate a question about a technology the candidate never used.
- The weakness analysis is explicitly about honesty: it helps the candidate rehearse defensible answers for thin areas, not bluff their way through.

## Prompt composition reference

| Step | Prompts |
|------|---------|
| Behavior questions | `skills/interview/prompts/behavior-question.md` + `prompts/core/anti-hallucination.md` |
| Technical questions | `skills/interview/prompts/technical-question.md` + `prompts/core/anti-hallucination.md` |
| Project questions | `skills/interview/prompts/project-question.md` + `prompts/core/anti-hallucination.md` |
| STAR answers | `prompts/generation/star-story.md` + `prompts/core/anti-hallucination.md` |
| Weakness analysis | `skills/interview/prompts/weakness-analysis.md` + `prompts/core/anti-hallucination.md` |
| Mock interview | `skills/interview/prompts/mock-interview.md` + `prompts/core/anti-hallucination.md` |

---

## Guardrails

- **No vault writes.** This skill writes only to `output/**`.
- **No checkpoints.** The interview prep pack is emitted as a single document for the candidate to review, not a phased checkpoint pipeline.
- **Ask on gaps.** If a STAR element is missing, flag it as a rehearse-after-filling item rather than inventing content.

## Failure modes

- Zero projects in the vault: generate a reduced pack covering only education and skills, with an explicit note that project questions cannot be grounded without project entities.
- A project entity fails schema validation in Step 1: skip it, report it; do not abort.
- No JD provided: generate a general pack. Do not invent a target role.
