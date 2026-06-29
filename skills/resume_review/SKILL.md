---
name: resume_review
version: 0.1.0
description: Review any resume (vault-derived or external) from ATS, recruiter, hiring manager, and tech lead perspectives with prioritized improvement suggestions.
schema_version: 1.0.0
inputs: [derived-resume, project, education, skill]
outputs: [review-report]
mcp_tools: []
anti_hallucination: true
---

# resume_review

Review ANY resume -- a vault-derived one or an external one pasted by the user. Evaluate from four perspectives (ATS, recruiter, hiring manager, tech lead), detect weak bullets, and for vault-derived resumes, cross-check every claim against the vault (catch any hallucination that slipped through).

Every improvement suggestion MUST be grounded in what the resume actually says. Suggestions may reword or restructure; they may NEVER invent a new fact.

This is a single-pass analyzer, not a phased pipeline. No checkpoints.

---

## Inputs

1. A resume to review -- either:
   - a file path to a previously vault-derived resume (e.g. `output/<job-slug>/resume.md`), OR
   - pasted Markdown / plain text from an external resume.
2. For vault-derived resumes: the candidate's vault (`project`, `education`, `skill` entities),
   used to cross-check provenance.
3. Run parameters:
   - `language` (zh | en)

## Outputs (written to `output/review/<slug>.md`)

- A single review report covering all four lenses, weak bullets, provenance check (if applicable),
  and a prioritized improvement list with concrete rewording suggestions.

---

## Steps

### Step 1 -- Ingest the resume

- Read the resume file or accept pasted text.
- Determine the review mode:
  - **Vault-cross-check mode** if the resume is under `output/` and the vault is populated.
    Provenance checks are enabled.
  - **External-review mode** if the resume is pasted / from outside the vault. Provenance checks
    are disabled; focus on structure, clarity, ATS, and impact.
- Record the source path or "pasted" marker in the report header.

### Step 2 -- ATS lens

- **Compose:** `skills/resume_review/prompts/ats-check.md` + `prompts/core/anti-hallucination.md`.
- Evaluate:
  - Keyword coverage (against the JD if one is provided; otherwise against the role the resume
    appears to target).
  - Parseability: standard section headers, no tables/images that break ATS parsers.
  - Format issues: fonts, columns, contact block placement.
- **Obey ADR-0007:** do not invent missing keywords. If a keyword is missing from the resume but
  present in the expected role, flag it as a gap and suggest where the candidate could
  legitimately add it IF they have that experience.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 3 -- Recruiter lens

- **Compose:** `skills/resume_review/prompts/recruiter-review.md` + `prompts/core/anti-hallucination.md`.
- Evaluate:
  - Readability: can a 6-second skim surface the candidate's name, current role, key skills?
  - Clarity: are bullets specific and jargon-free?
  - Red flags: inconsistent dates, vague role titles, too-generic "responsible for" phrasing,
    length issues.
- Output concrete fix suggestions.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 4 -- Hiring manager lens

- **Compose:** `skills/resume_review/prompts/hiring-manager-review.md` + `prompts/core/anti-hallucination.md`.
- Evaluate:
  - Impact: are bullets outcome-driven (metric-first, not duty-first)?
  - Scope: does the resume convey scale (team size, budget, user base) where available?
  - Credibility: do claims feel proportional? Any "unicorn" bullets that list every skill ever?
- Output concrete fix suggestions.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 5 -- Tech lead lens

- **Compose:** `skills/resume_review/prompts/tech-lead-review.md` + `prompts/core/anti-hallucination.md`.
- Evaluate:
  - Depth: does the candidate describe the hard parts of the system, or only surface features?
  - Accuracy: are technical claims plausible given the described project?
  - Project credibility: are the projects described in enough detail that a peer could assess
    them?
- Output concrete fix suggestions.
- Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 6 -- Weak bullet detection

- **Compose:** `skills/resume_review/prompts/weak-bullet-detect.md` + `prompts/core/anti-hallucination.md`.
- Scan every bullet for:
  - Missing metrics (no number, percentage, or concrete outcome).
  - Weak action verbs ("responsible for," "worked on," "helped with").
  - Redundancy (two bullets that say the same thing).
  - Length (too-long bullets that bury the point).
- List each weak bullet with a rewording suggestion that does NOT invent a fact. If the bullet
  needs a metric to be strong, flag it as a gap and suggest the user either add the metric from
  memory or drop the bullet.

### Step 7 -- Provenance check (vault-cross-check mode only)

- If the resume is vault-derived (`output/<job-slug>/resume.md` or `output/master/master.md`):
  - For every claim in the resume, attempt to trace it to a vault entity (`entity_id:field`).
  - Flag any claim that cannot be traced as **likely hallucination** or **unconfirmed**.
  - For each flagged claim, offer two paths: (a) the user confirms and records the fact in the
    vault, or (b) the fact is removed from the resume.
- If the resume is external or provenance tracking is not enabled, skip this step with a note
  in the report.

### Step 8 -- Produce the prioritized improvement report

- Compile all findings from Steps 2-7 into one Markdown report:
  - **Critical:** issues that will cause the resume to be rejected (ATS unparseable, likely
    hallucinations, empty sections).
  - **Important:** issues that reduce the resume's effectiveness (weak bullets, missing
    keywords the candidate likely has).
  - **Nice-to-have:** polish (formatting, wording, section reordering).
- Each improvement item includes: the current text (verbatim), the suggested rewording (grounded
  or marked `[GAP -- confirm with user]`), and the reason.
- Write the report to `output/review/<slug>.md`.

---

## Anti-hallucination enforcement

- Every improvement suggestion MAY reword or restructure. It may NEVER invent a fact.
- If a suggestion requires a new claim (e.g., "add a metric here"), the suggestion MUST be marked
  `[GAP -- confirm with user]` and must NOT be inserted into the resume text automatically.
- Provenance flags in Step 7 are treated as critical findings; uncitable claims in a
  vault-derived resume are build failures, not warnings.

## Prompt composition reference

| Step | Prompts |
|------|---------|
| ATS | `skills/resume_review/prompts/ats-check.md` + `prompts/core/anti-hallucination.md` |
| Recruiter | `skills/resume_review/prompts/recruiter-review.md` + `prompts/core/anti-hallucination.md` |
| Hiring manager | `skills/resume_review/prompts/hiring-manager-review.md` + `prompts/core/anti-hallucination.md` |
| Tech lead | `skills/resume_review/prompts/tech-lead-review.md` + `prompts/core/anti-hallucination.md` |
| Weak bullets | `skills/resume_review/prompts/weak-bullet-detect.md` + `prompts/core/anti-hallucination.md` |

---

## Guardrails

- **No vault writes.** This skill writes only to `output/**`.
- **Reads vault for cross-check.** `permissions.read` includes `vault/career/**` for provenance
  checks on vault-derived resumes.
- **No checkpoints.** The review report is a single-shot output.
- **Suggestions never invent facts.** All rewording suggestions are grounded in what the resume
  already says, or explicitly marked as gaps.

## Failure modes

- The resume file does not exist and no text is pasted: abort with a clear message asking for the
  source.
- The resume is vault-derived but the vault is empty or inaccessible: fall back to external-review
  mode and note the provenance check was skipped.
- A claim in the resume contradicts the vault: flag as a critical provenance failure.
