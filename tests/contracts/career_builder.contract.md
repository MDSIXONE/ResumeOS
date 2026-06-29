# Career Builder Contract

**Skill:** `career_builder`  
**Version:** 0.1.0  
**Purpose:** Enrich `vault/inbox/*` into `vault/career/*`, detect gaps, ask follow-ups, generate STAR stories

---

## Happy Path

**Input vault state:**
- `vault/inbox/project-report.md` with `title: "Drone Control System"`, `role: "Lead Developer"`, `confidence: inferred`
- User answers follow-up: "Team size was 5, we used Python and C++, completed in 6 months"

**Skill behavior:**
1. Read `inbox/project-report.md`
2. Compare required fields against `schemas/project.schema.json`:
   - Missing: `timeline.end`, `team_size`, `stack`
3. Ask user: "What was the team size? What technologies did you use? When did the project end?"
4. User answers
5. Create `vault/career/projects/drone-control-system.md`:
   - `title: "Drone Control System"`
   - `entity_type: "project"`
   - `status: "completed"`
   - `timeline: {start: "2023-01-15", end: "2023-07-15"}`
   - `role: "Lead Developer"`
   - `team_size: 5`
   - `stack: {software: ["Python", "C++"]}`
   - `confidence: "confirmed"`
   - `sources: [{kind: "docx", ref: "inbox/project-report.md"}]`
6. Delete or archive `inbox/project-report.md` (optional, depends on implementation)
7. Report: "Created `vault/career/projects/drone-control-system.md`. Confidence is now 'confirmed'."

**Expected vault state:**
- `vault/career/projects/drone-control-system.md` exists with valid frontmatter
- All required fields from `project.schema.json` are present
- `confidence: "confirmed"`
- `sources` array is non-empty

---

## Anti-Hallucination Path

**Input vault state:**
- `vault/inbox/research-paper.md` with `title: "Machine Learning Study"`, no authors, no venue, no year
- User says: "I don't remember the details"

**Skill behavior:**
1. Read `inbox/research-paper.md`
2. Compare against `schemas/research.schema.json`:
   - Missing: `authors`, `venue`, `year`, `status`, `abstract`, `my_contribution`
3. Ask user: "Who were the authors? What venue was this published at? What year? What was your contribution?"
4. User says: "I don't remember"
5. Skill response: "Cannot enrich this note without confirming the facts. Staging as `confidence: missing` in `inbox/research-paper.md`. You can update it later when you have the information."
6. Do NOT create a note in `vault/career/research/`
7. Do NOT invent authors like "Zhang San, Li Si"
8. Do NOT assume `year: 2023`

**NOT allowed:**
- Creating a `vault/career/research/` note with guessed fields
- Setting `confidence: confirmed` or `inferred` when facts are unknown
- Filling `year` with a default value

---

## STAR Generation

**Input vault state:**
- `vault/career/projects/drone-control-system.md` with detailed responsibilities and outcomes

**Skill behavior (when user asks for STAR stories):**
1. Read the project note
2. Generate a STAR story:
   - **Situation:** "During my internship at XYZ Corp, our team needed to build a drone control system."
   - **Task:** "I was the lead developer responsible for the flight control algorithms."
   - **Action:** "I implemented PID control in C++ and optimized the path planning algorithm, reducing latency by 40%."
   - **Result:** "The system was deployed on 3 commercial drones and improved flight stability by 25%."
3. All facts must trace back to the project note
4. If a detail is missing (e.g., no specific metric for "improved stability"), ask the user: "Do you have a specific metric for the stability improvement?"

---

## Gap Detection

**Input vault state:**
- Vault has 5 projects, 2 awards, 1 education entry, but no skill notes

**Skill behavior:**
1. Analyze vault structure
2. Report: "You have projects but no skill notes. Consider creating skill notes for technologies you used (e.g., Python, C++, PID control). Run: create skill note for 'Python' in vault/career/skills/."
3. Do NOT auto-create skill notes — the user must confirm

---

## Notes

- `career_builder` is the only skill that writes to `vault/career/*` (besides `career_update`)
- It must never guess or invent facts
- It must ask follow-up questions for missing required fields
- It can generate STAR stories, but only from confirmed facts
- Gap detection is a suggestion mechanism, not an auto-creation mechanism
