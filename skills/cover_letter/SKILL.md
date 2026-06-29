---
name: cover_letter
version: 0.1.0
description: Generate a personalized cover letter for a specific job, grounded only in confirmed vault facts, with optional reuse of resume_tailoring research artifacts.
schema_version: 1.0.0
inputs: [project, education, skill, job]
outputs: [derived-cover-letter]
mcp_tools: [browser:fetch]
anti_hallucination: true
---

# cover_letter

Generate a **personalized cover letter** for a specific job, grounded ONLY in confirmed vault facts. A cover letter may reframe confirmed facts to match the role narrative, but it must NOT claim any unrecorded accomplishment.

Every fact emitted traces to the vault (ADR-0007). This is a single-pass generator, not a phased pipeline.

---

## Inputs

1. A job description (JD) -- pasted text, a URL (via `browser:fetch` if enabled), or a `vault/jobs/<id>.md` note.
2. The vault: `project`, `education`, `skill`, and the relevant `job` entity/note.
3. (Optional) The `resume_tailoring` research artifact for the same job at `output/<job-slug>/artifacts/research.json`. If present, reuse it -- do not re-research.

## Outputs (written to `output/<job-slug>/`)

- `cover-letter.md`
- `cover-letter.docx` (if DOCX output is requested)

---

## Steps

### Step 1 -- Read job note, vault entities, and (if present) research artifact

- Read the `job` entity / note.
- Read `project`, `education`, `skill` entities from `vault/career/*`.
- If `output/<job-slug>/artifacts/research.json` already exists from a prior `resume_tailoring` run for the same job, reuse it. Otherwise, optionally invoke `browser:fetch` to research the company/JD (only if the user has enabled MCP browser access).
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 2 -- Select 1-2 best-matching projects

- Based on the JD's required skills and responsibilities, pick 1 or 2 `project` (or `internship` / `research`) entities whose confirmed facts most closely align.
- Do NOT invent a project that matches the JD. Pick from what exists. If no project matches well, state this explicitly and draft around the skills / education entities available.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 3 -- Compose the cover letter

- **Compose:** `skills/cover_letter/prompts/cover-letter-section.md` + `prompts/core/anti-hallucination.md`.
- Write a 3-4 paragraph cover letter:
  - **Opening:** the role, why the candidate is writing.
  - **Body:** 1-2 specific project references, each citing its source (`entity_id:field`). Reframe to match the role narrative.
  - **Close:** enthusiasm and a concrete next-step gesture.
- Render in the target `language` (zh or en).
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 4 -- Write the output

- Write `cover-letter.md` to `output/<job-slug>/`.
- Optionally export `cover-letter.docx`.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

---

## Anti-hallucination enforcement

- A cover letter may **reframe** a confirmed fact for the role narrative. It may NOT **claim** a fact that is not in the vault.
- Every specific project / metric / skill mentioned in the letter must carry an internal citation (`entity_id:field`) in the working document. Citations are stripped from the rendered letter but kept in a sidecar `cover-letter.provenance.md` for audit.
- `confidence: inferred` or `missing` facts never enter the letter. They are surfaced to the user as "I would like to include X but it is not recorded -- can you confirm?"

## Prompt composition reference

| Step | Prompts |
|------|---------|
| Letter composition | `skills/cover_letter/prompts/cover-letter-section.md` + `prompts/core/anti-hallucination.md` |

---

## Guardrails

- **No vault writes.** This skill writes only to `output/**`.
- **Reuse prior research.** If `resume_tailoring` has already produced `research.json` for the same job, do not re-scrape the company.
- **Reframing, not inventing.** A cover letter can present the same vault fact from a different angle; it cannot add a fact.

## Failure modes

- No `job` entity or JD provided: abort with a clear message asking the user to supply one.
- No project matches the JD: still generate a letter grounded in `skill` + `education` entities; flag the mismatch as a gap the user may want to prepare for in an interview.
- The optional `browser:fetch` research step fails: proceed using JD text only. Do not fabricate company details.
