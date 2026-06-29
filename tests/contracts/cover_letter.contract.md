# Cover Letter Contract

**Skill:** `cover_letter`  
**Version:** 0.1.0  
**Purpose:** Generate personalized cover letters grounded in confirmed vault facts

---

## Happy Path

**Input vault state:**
- `vault/career/projects/` with 5 confirmed projects relevant to the job
- `vault/career/skills/` with matching skills
- `output/<job-slug>/resume.md` exists (from `resume_tailoring`)
- Job description: "Robotics Engineer at XYZ Corp"

**Skill behavior:**
1. Read `output/<job-slug>/resume.md` to understand the tailored resume
2. Read relevant project notes from `vault/career/projects/`
3. Generate cover letter:
   - **Opening:** Express interest in the role and company
   - **Body:** Highlight 2-3 most relevant projects, emphasizing matching skills
   - **Closing:** Call to action (interview request)
4. All facts must trace back to vault entities
5. Output: `output/<job-slug>/cover-letter.md`

**Expected output:**
- Cover letter in Markdown format
- All claims cite provenance (e.g., "In my drone control project [entity_id:drone-project], I...")
- No hallucinated facts
- Personalized to the specific job (not a generic template)

---

## Anti-Hallucination Path

**Input vault state:**
- Job requires "team leadership experience"
- Vault has no projects with `role: "Team Lead"` or `team_size > 1`

**Skill behavior:**
1. Attempt to generate cover letter
2. For team leadership paragraph, check vault for relevant projects
3. Find no confirmed examples
4. Omit the team leadership paragraph
5. Report: "Could not find confirmed team leadership experience in the vault. Omitted from cover letter. Add a project with team leadership details to enable this section."

**NOT allowed:**
- Inventing a team leadership story
- Claiming "I led a team of 5 engineers" if not in the vault
- Using vague language like "I have leadership experience" without a specific vault-backed example

---

## Notes

- `cover_letter` is a generator skill — writes only to `output/*`
- Must read the tailored resume first (if available) to ensure consistency
- All claims must cite provenance
- The skill should personalize the letter to the specific job, not use a generic template
- If the vault is too sparse, report: "Vault has insufficient data for a personalized cover letter"
