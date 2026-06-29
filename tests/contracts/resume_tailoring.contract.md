# Resume Tailoring Contract

**Skill:** `resume_tailoring`  
**Version:** 0.1.0  
**Purpose:** Tailor a master resume to a specific job description via a 6-phase checkpoint pipeline

---

## Happy Path

**Input vault state:**
- `output/master-resume.md` exists with 5 projects, 10 skills, 3 awards
- User provides a job description: "Senior Robotics Engineer at XYZ Corp. Requirements: Python, C++, ROS, computer vision, 3+ years experience"

**Skill behavior (6-phase pipeline):**

### Phase 0: Library Build
1. Index all confirmed entities from `vault/career/*`
2. Build a vector index of skills and projects (for semantic matching)
3. Output: internal index (not written to disk)

### Phase 1: Research (checkpoint)
1. Parse job description
2. Extract requirements:
   - Skills: Python, C++, ROS, computer vision
   - Experience: 3+ years
   - Domain: robotics
3. Research company (via MCP `browser:fetch` if available): XYZ Corp, their products, culture
4. Output: `output/<job-slug>/artifacts/research.json` with:
   - `required_skills: ["Python", "C++", "ROS", "computer vision"]`
   - `experience_years: 3`
   - `domain: "robotics"`
   - `company_info: {...}`
5. **Checkpoint:** pause and present `research.json` to user: "Does this accurately capture the job requirements?"

**Expected user action:** Review and approve or edit `research.json`

### Phase 2: Gap Analysis (checkpoint)
1. Compare `research.json` requirements against vault entities
2. Identify:
   - **Matching skills:** Python (expert), C++ (advanced), computer vision (intermediate)
   - **Missing skills:** ROS (not in vault)
   - **Weak skills:** computer vision (intermediate, but job requires expert-level)
3. Output: `output/<job-slug>/artifacts/gaps.json` with:
   - `matching: [...]`
   - `missing: ["ROS"]`
   - `weak: [{"skill": "computer vision", "current_level": "intermediate", "required_level": "expert"}]`
4. **Checkpoint:** pause and present `gaps.json`: "You are missing ROS. Do you have experience with ROS that is not in the vault?"

**Expected user action:** Confirm gaps or add missing information to vault

### Phase 3: Assembly (checkpoint)
1. Select top 3-4 projects most relevant to the job
2. Reword bullets to emphasize matching skills (without inventing facts)
3. Assign tailoring scores (0.0-1.0) to each project based on relevance
4. Output: `output/<job-slug>/artifacts/assembly.json` with:
   - `sections: [{title: "Experience", items: [{entity_id: "drone-project", bullets: [...], tailoring_score: 0.85}]}]`
5. **Checkpoint:** pause and present `assembly.json`: "Selected 4 projects. Are these the right ones? Are the bullets accurate?"

**Expected user action:** Review and approve assembly

### Phase 4: Generation
1. Read `assembly.json`
2. Generate tailored resume:
   - Include only selected projects
   - Reword bullets to emphasize Python, C++, computer vision
   - Exclude ROS (not in vault)
   - Adjust skills section to highlight matching skills
3. Output: `output/<job-slug>/resume.md`
4. Also output `resume.docx` if format is enabled

**Expected output:**
- Tailored resume that emphasizes matching skills
- No hallucinated facts (e.g., no claim of ROS experience)
- All bullets cite provenance

### Phase 5: Library Update
1. Record tailoring decisions in `vault/.library/<job-slug>.json`:
   - Which projects were selected
   - Which skills were emphasized
   - Tailoring scores
2. This enables future tailoring runs to learn from past decisions

**Expected vault state:**
- `vault/.library/<job-slug>.json` created
- Machine-managed, not user-editable

---

## Anti-Hallucination Path

**Input vault state:**
- Job description requires "ROS experience"
- Vault has NO projects or skills mentioning ROS
- User says: "I have some ROS experience but didn't add it to the vault"

**Skill behavior (Phase 2):**
1. Identify ROS as a missing skill
2. Report: "You are missing ROS. Do you have experience with ROS?"
3. User: "Yes, I used ROS in a personal project"
4. Skill response: "Please add a project note to `vault/career/projects/` describing your ROS experience. Once confirmed, I can include it in the tailored resume."
5. Do NOT proceed with Phase 3 until the user adds the project to the vault

**NOT allowed:**
- Inventing a ROS project
- Adding "ROS" to the skills section with `confidence: inferred`
- Proceeding to Phase 4 without the fact being in the vault

---

## Checkpoint Path

**Input vault state:**
- Phase 2 checkpoint: `gaps.json` shows user is missing "ROS"

**Skill behavior:**
1. **Pause** after Phase 2
2. Present `gaps.json` to user: "You are missing ROS. Do you have experience with ROS?"
3. Wait for user response
4. If user says "No": proceed to Phase 3 without ROS
5. If user says "Yes, but it's not in the vault": block and ask user to add it to vault first
6. Do NOT auto-advance to Phase 3 without user approval

**NOT allowed:**
- Auto-advancing past checkpoints
- Skipping the gap analysis review
- Proceeding without user confirmation at each checkpoint

---

## Notes

- `resume_tailoring` is a phased pipeline skill (ADR-0006)
- It must pause at checkpoints: research, gap_analysis, assembly
- It must never invent facts — if a required skill is missing, it must ask the user to add it to the vault
- It rewords bullets but never adds new facts
- All bullets in the final resume must cite provenance (entity_id:field)
- The library update (Phase 5) enables self-improvement over time
- The skill may use MCP `browser:fetch` for company research (Phase 1), but this is optional
