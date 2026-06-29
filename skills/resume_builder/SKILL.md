---
name: resume_builder
version: 0.1.0
description: Generate a master resume from the vault with no JD targeting; supports zh/en, academic/industry/research styles, one/two-page lengths, and markdown/docx/latex/jsonresume formats.
schema_version: 1.0.0
inputs: [project, education, skill, award, research, competition, internship, opensource]
outputs: [derived-resume]
mcp_tools: []
anti_hallucination: true
---

# resume_builder

Generate a **master resume** (not targeted at any specific job) from the vault. The master resume is a comprehensive, reverse-chronological record of the candidate's career, suitable as the base document for tailoring or for general-purpose use.

Every fact emitted traces to the vault (ADR-0007). The master resume is not a phased pipeline -- it is a single-pass generator.

---

## Inputs

1. A populated vault: entities in `vault/career/*` (validated against `schemas/`).
   - `project`, `research`, `competition`, `internship`, `opensource`, `award`, `education`, `skill`.
2. Run parameters (from `resumeos.config.yaml` or per-run override):
   - `language` (zh | en)
   - `resume_style` (industry | academic | research)
   - `resume_length` (one_page | two_page)
   - `formats` (markdown | docx | latex | jsonresume)

## Outputs (written to `output/master/`)

- `master.md`, `master.docx`, `master.tex`, `master.json` — the master resume in each requested format.

---

## Steps

### Step 1 — Read and validate all vault entities

- Read every entity under `vault/career/*`.
- Validate each against its schema. Skip invalid entities; report them to the user.
- Build an internal index of all confirmed facts: id, type, dates, title, stack, metrics, contribution, confidence level.

### Step 2 — Select content (reverse-chronological, no JD targeting)

- Select all `confirmed` entities. No relevance ranking is needed — the master resume includes the full breadth of available material.
- Order by date (reverse-chronological) within each section.
- If `resume_length` is `one_page` and content overflows, drop lowest-recency items first.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 3 — Render sections

- **Compose:** `prompts/generation/resume-section.md` + `prompts/core/anti-hallucination.md`.
- Render each section (Projects, Experience, Education, Skills, Awards, etc.) from the confirmed entity index.
- Every bullet cites its source: `entity_id:field`.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 4 — Export formats

- Render `master.md` from the section output.
- Export to requested formats:
  - DOCX, LaTeX: standard template-based conversion.
  - JSON Resume: compose `skills/resume_builder/prompts/jsonresume-convert.md` to map the rendered sections into the JSON Resume schema (round-trip per ADR-0002).
- Write all files to `output/master/`.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

---

## Anti-hallucination enforcement

- Every bullet in the master resume must carry a `entity_id:field` citation in the working document (citations are stripped from the rendered resume but kept in the assembly record for audit).
- `confidence: inferred` or `missing` facts never enter the output. They are noted as gaps the user may fill in the vault.
- Rewording is allowed (clarity, action verbs). Invention is not. No metric, responsibility, or technology may appear unless confirmed in the source entity.

## Prompt composition reference

| Step | Prompts |
|------|---------|
| Section rendering | `prompts/generation/resume-section.md` + `prompts/core/anti-hallucination.md` |
| JSON Resume export | `skills/resume_builder/prompts/jsonresume-convert.md` |

---

## Guardrails

- **No checkpoints.** The master resume is a single-pass generator, not a phased pipeline.
- **Vault immutability.** This skill writes only to `output/**`. It never writes to `vault/`.
- **No JD input.** The master resume is JD-agnostic. Use `resume_tailoring` to target a job.

## Failure modes

- An entity fails schema validation in Step 1: skip it, report it; do not abort.
- Zero confirmed entities for a section: omit the section entirely (do not render an empty placeholder).
- An uncited bullet in Step 3: drop it and flag it as a gap.
