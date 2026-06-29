---
fragment: ats-keyword-extract
applies: ADR-0006 Phase 1
inputs: [job description]
outputs: [research.json: ats_keywords]
---

# ATS Keyword Extraction

Extract the keywords an Applicant Tracking System is likely to score for this role.

**Process:**
1. Read the JD. Identify: required hard skills, required tools/frameworks, required domain
   knowledge, required qualifications, preferred (nice-to-have) skills, leadership/soft-skill
   signals.
2. Normalize each to a canonical token (lowercase, no version unless version is semantically
   required, e.g. "ROS 2" vs "ROS").
3. Mark each as `required` or `preferred`.
4. Note JD synonyms the company uses (e.g. "建模" ↔ "modeling", "落地" ↔ "deployment") — these map
   vault vocabulary to the company's vocabulary for later reframing.

**Output (into `research.json: ats_keywords`):**
```json
[
  { "keyword": "pytorch", "required": true, "synonyms": ["深度学习框架"] },
  { "keyword": "ros2",    "required": true, "synonyms": ["ros 2"] }
]
```

**Do not** invent keywords the JD does not contain or imply. ATS keyword inflation is a form of
hallucination and harms matching.
