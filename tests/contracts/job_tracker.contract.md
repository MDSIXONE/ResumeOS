# Job Tracker Contract

**Skill:** `job_tracker`  
**Version:** 0.1.0  
**Purpose:** Track job applications, interviews, offers, and generate pipeline dashboards

---

## Happy Path

**Input vault state:**
- User says: "Track this job: Senior Robotics Engineer at XYZ Corp, applied on 2024-01-15"

**Skill behavior:**
1. Create `vault/jobs/xyz-corp-robotics-engineer.md`:
   - `entity_type: "job"`
   - `title: "Senior Robotics Engineer"`
   - `company: "XYZ Corp"`
   - `status: "applied"`
   - `applied_at: "2024-01-15"`
   - `sources: [{kind: "manual", ref: "user input"}]`
2. Optionally use MCP `browser:fetch` to scrape the job description and enrich the note
3. Report: "Created job tracking note: vault/jobs/xyz-corp-robotics-engineer.md"

**Expected vault state:**
- New job note with valid frontmatter
- `confidence: "confirmed"` (user-provided)

---

## Status Updates

**Input vault state:**
- `vault/jobs/xyz-corp-robotics-engineer.md` exists with `status: "applied"`
- User says: "Got an interview on 2024-01-20"

**Skill behavior:**
1. Update the job note:
   - `status: "interviewing"`
   - `timeline: [{date: "2024-01-20", event: "phone screen"}]`
2. If MCP `calendar` is enabled, offer to create a calendar event
3. Report: "Updated job status to 'interviewing'. Added timeline event."

---

## Dashboard Generation

**Input vault state:**
- 10 job notes in `vault/jobs/`

**Skill behavior (when user asks for dashboard):**
1. Read all job notes
2. Generate dashboard:
   - Total applications: 10
   - By status: applied (3), interviewing (4), offer (2), rejected (1)
   - Timeline: applications per month
3. Output: `output/job-dashboard.md` or Dataview query

**Expected output:**
- Summary statistics
- Pipeline visualization
- Actionable insights (e.g., "You have 2 offers — time to decide")

---

## Anti-Hallucination Path

**Input vault state:**
- User says: "Update job status" but does not specify which job

**Skill behavior:**
1. Ask: "Which job would you like to update? Options: xyz-corp, abc-inc, ...]
2. Wait for clarification
3. Do NOT guess which job

**NOT allowed:**
- Updating a random job
- Assuming the most recent job

---

## Notes

- `job_tracker` can write to `vault/jobs/` (it is an enrichment skill)
- It may use MCP `browser:fetch` for job description scraping
- It may use MCP `calendar` for interview scheduling
- Dashboard generation can output Markdown or Dataview queries
- The skill must ask for clarification when input is ambiguous
