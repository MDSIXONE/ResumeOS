# Career Update Contract

**Skill:** `career_update`
**Version:** 0.1.0
**Purpose:** Watch the vault for new/changed files, enrich them, mark derived docs stale, prompt regeneration

---

## Happy Path

**Input vault state:**
- `vault/career/projects/drone-project.md` is updated (user adds a new metric)
- `output/master-resume.md` exists (generated before the update)
- `output/<job-slug>/resume.md` exists (generated before the update)

**Skill behavior:**
1. Detect file change event on `vault/career/projects/drone-project.md`
2. Validate the note against `schemas/project.schema.json`
3. If valid, run `career_builder` enrichment on the changed note (detect new opportunities for STAR stories, keywords)
4. Check `output/` for derived documents that depend on this entity
5. Mark stale documents in `output/.stale.json`
6. Prompt user: "drone-project.md was updated. 2 derived resumes are now stale. Regenerate?"
7. If user confirms, regenerate stale documents

**Expected vault state:**
- `output/.stale.json` updated with stale document list
- If user confirms: stale documents regenerated
- If user declines: nothing regenerated, stale list persists

---

## Anti-Hallucination Path

**Input vault state:**
- New file `vault/career/projects/new-project.md` appears
- Frontmatter fails schema validation (missing required field `sources`)

**Skill behavior:**
1. Detect new file
2. Validate against `project.schema.json` -> FAIL (missing `sources`)
3. Report: "vault/career/projects/new-project.md fails validation: missing required field 'sources'. Please fix the frontmatter before proceeding."
4. Do NOT enrich the file
5. Do NOT mark any derived docs stale (invalid entity cannot flow into output)

---

## New File Path

**Input vault state:**
- New file `vault/career/projects/unknown-project.md` appears in `vault/career/projects/`
- Frontmatter validates against schema
- But no enriched data exists (no STAR stories, no ATS keywords)

**Skill behavior:**
1. Detect new file
2. Validate against schema -> passes
3. Check for enriched fields (e.g., `interview_questions`, `ats_keywords`) -> missing/empty
4. Run `career_builder` on the new entity to identify gaps and suggest enrichment
5. Report: "New project detected. Missing: interview_questions, ats_keywords. Run career_builder to enrich."

---

## Checkpoint Path

Not applicable (career_update is not a phased pipeline skill).
But it does involve a user prompt before regeneration, which functions as a soft checkpoint.

---

## Notes

- `career_update` registers the `onVaultChange` hook
- It can write to `vault/career/*` (enrichment) and `output/.stale.json`
- It calls `career_builder` for gap analysis
- It never auto-regenerates without user consent
- It validates every changed file before acting on it
