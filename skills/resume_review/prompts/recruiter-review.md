---
fragment: recruiter-review
inputs: [resume content]
outputs: [recruiter evaluation]
applies: ADR-0007
---

# Recruiter Lens Review

Evaluate a resume the way a busy recruiter would on a 6-second skim. The goal is to surface
whether the resume is readable, scannable, and free of obvious red flags.

**Readability:**
- Name, current/most-recent title, key skills surface in the first 1/3 of the first page.
- Section order is logical: experience (or projects) before education for experienced
  candidates; education before experience for new grads.
- Bullet count per project: 2-4. Too few = too little substance; too many = a wall of text.

**Clarity:**
- Bullets are specific ("Reduced API latency by 42%") not vague ("worked on performance").
- Jargon-free language unless the jargon is the industry-standard term expected by the target
  role.
- Action verbs at the head of every bullet.

**Red flags to flag:**
- Inconsistent date formats or obvious timeline gaps.
- Duplicate content across projects (two bullets saying the same thing).
- "Responsible for..." passive phrasing.
- Too-long bullets (>2 lines) that bury the point.
- Length issues: too short (<1 page for an experienced candidate), too long (>2 pages without
  a clear reason).

**Hard rules:**
- Quote the verbatim text of the problem so the user can locate it.
- Suggest a concrete rewrite only if it can be done without inventing new facts. If a
  rewrite requires a metric the resume does not provide, flag it as `[GAP]` instead of
  inventing.
- Do NOT speculate on the candidate's intent. Point out what the text says.

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: critique based
on the resume text; ask on any gap; never invent content.
