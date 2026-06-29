# Career Collector Contract

**Skill:** `career_collector`  
**Version:** 0.1.0  
**Purpose:** Ingest raw career material (PDF/DOCX/GitHub/LinkedIn/images) into `vault/inbox/`

---

## Happy Path

**Input vault state:**
- Empty or partial vault
- User has a PDF of a research paper, a DOCX of a project report, and a GitHub URL

**Skill behavior:**
1. Read the PDF, extract title, authors, abstract, venue, year
2. Read the DOCX, extract project title, role, timeline, responsibilities, outcomes
3. Fetch the GitHub repo via MCP `github:get_commits`, extract commit history, README, contributors
4. Stage three notes in `vault/inbox/`:
   - `inbox/research-paper-2024.md` with `confidence: inferred`, `sources: [{kind: "pdf", ref: "path/to/paper.pdf"}]`
   - `inbox/project-report.md` with `confidence: inferred`, `sources: [{kind: "docx", ref: "path/to/report.docx"}]`
   - `inbox/github-project.md` with `confidence: inferred`, `sources: [{kind: "github", ref: "https://github.com/user/repo"}]`
5. Report to user: "Collected 3 items. Confidence is 'inferred' — run `career_builder` to enrich and confirm."

**Expected vault state:**
- Three new notes in `vault/inbox/` with valid frontmatter (but not yet validated against entity schema — they are staged, not canonical)
- No changes to `vault/career/*` (that is `career_builder`'s job)

---

## Anti-Hallucination Path

**Input vault state:**
- A PDF with corrupted metadata (no title, no date)

**Skill behavior:**
1. Attempt to read the PDF, fail to extract title and date
2. Stage a note in `vault/inbox/` with:
   - `title: null` (or omit if schema allows)
   - `sources: [{kind: "pdf", ref: "path/to/corrupt.pdf"}]`
   - `confidence: missing`
3. Report to user: "Could not extract title or date from the PDF. Staged in inbox with `confidence: missing`. Please provide the missing information or run `career_builder` to ask follow-up questions."

**NOT allowed:**
- Inventing a title like "Untitled Research Paper"
- Assuming the year is 2024
- Setting `confidence: confirmed` when metadata is missing

---

## Notes

- `career_collector` never writes to `vault/career/*` — that is `career_builder`'s job
- All staged notes have `confidence: inferred` or `missing` until enriched
- The skill must use MCP tools declared in its `plugin.json` (e.g., `filesystem:read_file`, `github:get_commits`)
- If MCP is unavailable, the skill should degrade gracefully and ask the user to manually provide the material
