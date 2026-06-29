---
name: resume_tailoring
version: 0.1.0
description: Tailor a resume to a specific job via a 6-phase, checkpoint-based, anti-hallucination pipeline.
schema_version: 1.0.0
inputs: [project, research, competition, internship, opensource, award, education, skill, job]
outputs: [derived-resume]
mcp_tools: [browser:fetch]
checkpoints: [research, gap_analysis, assembly]
anti_hallucination: true
---

# resume_tailoring

Tailor a resume to a specific job description by running a **sequential, checkpoint-based phased
pipeline** (ADR-0006). Every fact emitted traces to the vault (ADR-0007). The user reviews artifacts
at three checkpoints before any resume is generated.

**Obey ADR-0007 at every step: state only confirmed vault facts; ask on any gap; never invent.**

---

## Inputs

1. A job description (JD) — pasted text, a URL (via `browser:fetch` MCP), or a `vault/jobs/<id>.md`
   note with the JD in its body.
2. Run parameters (from `resumeos.config.yaml` or per-run override):
   - `language` (zh | en)
   - `resume_style` (industry | academic | research)
   - `resume_length` (one_page | two_page)
   - `formats` (markdown | docx | latex | jsonresume)
3. The vault: read entities from `vault/career/*` (validated against `schemas/`).

## Outputs (written to `output/<job-slug>/`)

- `artifacts/library.json`     — Phase 0
- `artifacts/research.json`    — Phase 1 (checkpoint)
- `artifacts/gaps.json`        — Phase 2 (checkpoint)
- `artifacts/assembly.json`    — Phase 3 (checkpoint)
- `resume.md`  `resume.docx`  `resume.tex`  `resume.json` — Phase 4
- `vault/.library/<job-slug>.json` — Phase 5

---

## Pipeline

### Phase 0 — Library Build

- **Read** all `vault/career/*` entities. Validate each against its schema; skip invalid entities
  and report them.
- **Build** `library.json`: an index of entities with their confirmable facts (id, title, type,
  stack, metrics, contribution, confidence).
- No checkpoint. Proceed to Phase 1.

### Phase 1 — Research  ✅ CHECKPOINT: research

- **Compose:** `prompts/analysis/company-research.md` + `prompts/analysis/ats-keyword-extract.md`
  + `prompts/core/anti-hallucination.md`.
- Parse the JD; research the company (use `browser:fetch` only if enabled & approved; else work from
  JD + user input). Extract ATS keywords (required/preferred + synonyms).
- **Emit** `artifacts/research.json` (schema: `schemas/artifacts/research.schema.json`).
- **PAUSE.** Present `research.json` to the user. Do not start Phase 2 until approved. The user may
  edit the artifact; if edited, re-validate against its schema.

### Phase 2 — Gap Analysis  ✅ CHECKPOINT: gap_analysis

- **Compose:** `prompts/analysis/gap-classification.md` + `prompts/core/ask-never-invent.md`.
- Compare `library.json` against `research.json`. Classify each requirement: `covered |
  underdeveloped | missing | misaligned`. Rank by severity.
- For every `missing` high-severity requirement, emit a follow-up question (ask, never invent).
- **Emit** `artifacts/gaps.json` (schema: `schemas/artifacts/gaps.schema.json`).
- **PAUSE.** Present gaps + follow-up questions. The user answers (facts get recorded in the vault
  by `career_builder` or manually) or chooses to omit. Do not start Phase 3 until approved.

### Phase 3 — Assembly  ✅ CHECKPOINT: assembly

- **Compose:** `prompts/generation/bullet-rewrite.md` + `prompts/core/provenance.md`.
- Select and rank projects/experience by relevance to the JD. Reword confirmed bullets only
  (action verbs, metrics preserved not invented, JD-synonym mapping). Attach `provenance` citations
  to every bullet. Assign a `tailoring_score` (0–1) per item.
- **Emit** `artifacts/assembly.json` (schema: `schemas/artifacts/assembly.schema.json`). Every item
  must carry a citation; an uncited item is a build failure.
- **PAUSE.** Present the assembled resume outline (sections + bullets + citations) to the user.
  Do not start Phase 4 until approved.

### Phase 4 — Generation

- **Compose:** `prompts/generation/resume-section.md` + `prompts/core/anti-hallucination.md`.
- Render `resume.md` from `assembly.json`, honoring `language`, `resume_style`, `resume_length`.
  Strip citation markers from the rendered resume but keep them in `assembly.json`.
- Export to the requested `formats`: DOCX, LaTeX, JSON Resume (round-trip via the JSON Resume
  converter — ADR-0002).
- No checkpoint. Proceed to Phase 5.

### Phase 5 — Library Update

- Record what worked and what the user edited at each checkpoint into
  `vault/.library/<job-slug>.json` (self-improving memory for the next run's Phase 0).
- Update `$resumeos.library_hints` on entities whose tailoring score shifted significantly.

---

## Anti-hallucination enforcement (read every run)

- Include `prompts/core/anti-hallucination.md` in Phases 1, 3, and 4.
- Every bullet in `assembly.json` carries `provenance: entity_id:field`. An uncited bullet fails
  the build.
- `confidence: inferred` or `missing` facts never reach Phase 4; they become follow-up questions in
  Phase 2.
- Rewording adds NO metrics/responsibilities/technologies. It only rephrases confirmed facts.

## Re-runnability

Because each phase writes an artifact file, the user may edit any checkpoint artifact and re-run
from that phase forward without redoing earlier phases. Pass `--from-phase <N>` (or its equivalent)
to resume the pipeline.

## Failure modes

- An entity fails schema validation in Phase 0 → skip it, report it; do not abort the pipeline.
- A checkpoint artifact fails its schema after user edit → re-prompt the user to fix it.
- An uncited bullet in Phase 3 → drop it and surface it as a gap; never ship it uncited.
