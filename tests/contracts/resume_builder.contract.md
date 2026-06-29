# Resume Builder Contract

**Skill:** `resume_builder`  
**Version:** 0.1.0  
**Purpose:** Generate a master resume from `vault/career/*` in multiple formats (Markdown, DOCX, LaTeX, JSON Resume)

---

## Happy Path

**Input vault state:**
- `vault/career/projects/` with 5 confirmed projects
- `vault/career/education/` with 1 education entry
- `vault/career/skills/` with 10 skill notes
- `vault/career/awards/` with 3 awards
- User config: `defaults.resume_style: "industry"`, `defaults.resume_length: "one_page"`

**Skill behavior:**
1. Read all entity notes from `vault/career/*`
2. Filter by `confidence: "confirmed"` (exclude `inferred` or `missing`)
3. Select top projects by relevance and recency (heuristic: projects from last 3 years, sorted by `timeline.end`)
4. Select skills by `level` (expert > advanced > intermediate)
5. Generate resume sections:
   - **Education:** institution, degree, field, timeline, GPA (if present)
   - **Experience:** projects sorted by date, each with role, org, dates, 3-5 bullets
   - **Skills:** grouped by category, with proficiency level
   - **Awards:** title, issuer, date, level
6. Output to `output/master-resume.md`
7. If `docx` format is enabled, also output `output/master-resume.docx`
8. Report: "Generated master resume: output/master-resUME.md. Includes 5 projects, 8 skills, 3 awards."

**Expected output:**
- `output/master-resume.md` with valid structure
- All bullets cite provenance (e.g., `entity_id:field`)
- No hallucinated facts
- Resume fits on one page (for `one_page` config)

---

## Anti-Hallucination Path

**Input vault state:**
- `vault/career/projects/drone-project.md` has no `metrics` field
- User config: `defaults.resume_style: "industry"`

**Skill behavior:**
1. Read the project note
2. Attempt to generate bullets
3. For the first bullet, use `contribution` field: "Led development of a drone control system"
4. For metrics-based bullets, check `metrics` field → empty
5. Do NOT invent metrics like "Improved performance by 30%"
6. Generate only factual bullets:
   - "Led development of a drone control system" (from `contribution`)
   - "Implemented PID control algorithms in C++" (from `stack.software`)
7. Report: "Project 'drone-project' had no confirmed metrics. Generated 2 factual bullets. Add metrics to the project note to enable stronger resume bullets."

**NOT allowed:**
- Inventing metrics if `metrics` is empty
- Claiming "Reduced latency by 40%" if not in the vault
- Setting `confidence: "confirmed"` for a bullet when the source data is missing

---

## Format Conversion

**Input vault state:**
- `output/master-resume.md` exists
- User requests DOCX format

**Skill behavior:**
1. Read `output/master-resume.md`
2. Convert to DOCX using Pandoc (or similar tool)
3. Output `output/master-resume.docx`
4. Preserve all formatting (headings, lists, dates)
5. Report: "Generated output/master-resume.docx"

**Notes:**
- Format conversion does not change content
- If Pandoc is unavailable, report an error and suggest manual conversion

---

## JSON Resume Export

**Input vault state:**
- User requests JSON Resume format

**Skill behavior:**
1. Read all confirmed entities from `vault/career/*`
2. Map to JSON Resume schema:
   - `basics`: name, email, location (from `vault/vault.meta.yaml`)
   - `work`: map projects with `role` and `company` to work entries
   - `education`: map education entries
   - `skills`: map skill notes
   - `awards`: map award entries
3. Output `output/resume.json` in JSON Resume 1.0.0 format
4. Include `$resumeos` namespace for provenance

**Notes:**
- JSON Resume export must be reversible (JSON Resume → ResumeOS)
- `$resumeos` field is ignored by JSON Resume tools but used by ResumeOS for provenance tracking

---

## Notes

- `resume_builder` is a generator skill — it writes only to `output/*`, never to `vault/`
- All bullets must cite provenance (entity_id:field)
- Only `confidence: "confirmed"` entities are included
- The skill must respect `defaults.resume_style` and `defaults.resume_length`
- If the vault is too sparse to fill a one-page resume, report: "Vault has insufficient data for a one-page resume. Consider adding more projects or skills."
