# Resume Review Contract

**Skill:** `resume_review`  
**Version:** 0.1.0  
**Purpose:** Review a resume (from vault or external) for ATS compatibility, recruiter appeal, hiring manager fit, and technical accuracy

---

## Happy Path

**Input vault state:**
- User provides a resume: `output/master-resume.md` (or an external PDF)
- User says: "Review my resume for ATS compatibility"

**Skill behavior:**
1. Read the resume
2. Perform ATS review:
   - Check for keywords matching common job descriptions
   - Verify formatting (dates, sections, contact info)
   - Identify missing keywords
3. Output: `output/review-ats.md` with:
   - ATS score: 75/100
   - Strengths: "Good use of action verbs, clear section headers"
   - Weaknesses: "Missing keywords: ROS, distributed systems"
   - Suggestions: "Add a project mentioning ROS if you have experience"

**Expected output:**
- Detailed review document
- Actionable suggestions
- All suggestions grounded in vault facts or job description requirements

---

## Anti-Hallucination Path

**Input vault state:**
- Resume claims: "Improved system performance by 40%"
- Vault has no metric confirming this claim

**Skill behavior:**
1. Parse resume and identify the claim
2. Check vault for supporting evidence → no match
3. Report: "Resume claims 'Improved system performance by 40%' but this is not in the vault. Verify this claim or remove it. Unsubstantiated metrics can hurt credibility in interviews."

**NOT allowed:**
- Assuming the claim is true
- Ignoring the discrepancy
- Suggesting ways to "improve" the claim without vault backing

---

## Review Modes

**ATS Review:**
- Focus on keywords, formatting, machine-readability
- Compare against common job descriptions

**Recruiter Review:**
- Focus on visual appeal, clarity, length
- Check for red flags (gaps, typos, inconsistent formatting)

**Hiring Manager Review:**
- Focus on relevance to target role
- Check for strong action verbs, quantified achievements
- Verify alignment with job requirements

**Technical Review:**
- Focus on technical accuracy
- Check that claimed skills are backed by projects
- Identify over-claims or under-claims

---

## Notes

- `resume_review` can review resumes from `output/*` or external sources
- All suggestions must be grounded in vault facts or job requirements
- The skill must flag unsubstantiated claims as potential credibility risks
- Multiple review modes (ATS, recruiter, hiring manager, technical) can be run independently
