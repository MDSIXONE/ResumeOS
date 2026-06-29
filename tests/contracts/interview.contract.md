# Interview Contract

**Skill:** `interview`  
**Version:** 0.1.0  
**Purpose:** Generate interview prep packs with STAR answers, technical questions, and mock interview scenarios

---

## Happy Path

**Input vault state:**
- `vault/career/projects/` with 5 confirmed projects
- `vault/career/skills/` with 10 skills
- `output/<job-slug>/resume.md` exists
- User says: "Generate interview prep for the Robotics Engineer role at XYZ Corp"

**Skill behavior:**
1. Read `output/<job-slug>/resume.md` to understand the tailored resume
2. Read relevant project notes
3. Generate interview prep pack:
   - **Behavioral questions:** 5 questions with STAR answers grounded in vault projects
     - "Tell me about a time you solved a difficult technical problem"
     - STAR answer using `drone-project` with provenance
   - **Technical questions:** 10 questions based on skills in the resume
     - "Explain PID control" (based on `stack.software: ["C++"]` in drone-project)
   - **Project deep-dives:** 3 questions about specific projects
     - "Walk me through the architecture of your drone control system"
   - **Weakness analysis:** Identify potential weak points (e.g., missing ROS experience)
4. Output: `output/<job-slug>/interview-prep.md`

**Expected output:**
- Comprehensive interview prep document
- All STAR answers cite provenance (entity_id:field)
- Technical questions align with confirmed skills
- No hallucinated scenarios

---

## Anti-Hallucination Path

**Input vault state:**
- Job description mentions "experience with distributed systems"
- Vault has no projects mentioning "distributed systems" or related technologies

**Skill behavior:**
1. Generate technical questions based on confirmed skills
2. For distributed systems, check vault → no match
3. Generate a question: "The job requires distributed systems experience. Do you have any experience with distributed systems that is not in the vault?"
4. If user says "No": omit distributed systems from the prep pack
5. If user says "Yes, but it's not in the vault": add a note to the prep pack: "Consider adding a project note about your distributed systems experience to the vault"

**NOT allowed:**
- Inventing a distributed systems project
- Generating a STAR answer for distributed systems without vault backing
- Claiming "I have experience with distributed systems" if not in the vault

---

## Mock Interview Mode

**Input vault state:**
- User says: "Run a mock interview for the Robotics Engineer role"

**Skill behavior:**
1. Read interview prep pack
2. Act as the interviewer:
   - Ask one question at a time
   - Wait for user's answer
   - Provide feedback based on vault facts
   - Track which questions were answered well/poorly
3. At the end, provide a summary:
   - Strong areas: "You answered technical questions well, especially PID control"
   - Weak areas: "You struggled with the team leadership question — consider adding a project with team details to the vault"

**Notes:**
- Mock interview is interactive
- Feedback must be grounded in vault facts
- If the user gives an answer not backed by the vault, say: "That answer is not in the vault. Consider updating your project notes to reflect this experience"

---

## Notes

- `interview` is a generator skill — writes only to `output/*`
- Must read the tailored resume first (if available) for consistency
- All STAR answers and examples must cite provenance
- The skill should identify weak areas and suggest vault updates
- Mock interview mode is interactive and provides grounded feedback
