---
fragment: tech-lead-review
inputs: [resume content]
outputs: [tech lead evaluation]
applies: ADR-0007
---

# Tech Lead Lens Review

Evaluate a resume as a senior engineer would on a peer interview panel: does the candidate
demonstrate depth, accuracy, and credible projects?

**Depth:**
- Does the resume describe the hard parts of the system (trade-offs, bottlenecks, debugging
  war stories) or only surface features?
- Are architecture decisions visible? ("Chose X over Y because Z" -- where does the resume
  show this?)
- If the candidate lists "backend engineer," is there evidence of actual backend work (APIs,
  DB schema, load handling) or only vague claims?

**Accuracy:**
- Are technical claims plausible given the described project? A claimed "real-time ML pipeline"
  should describe the streaming framework, model type, and latency -- if those are missing,
  the claim rings hollow.
- Stack list matches project description? If the stack says "TensorFlow" but the project
  description never mentions ML, there is a credibility gap.
- Technology choices are defensible? Not every candidate needs to have chosen the stack, but if
  the resume implies they did, the details should hold up.

**Project credibility:**
- Are projects described in enough detail that an interviewer could ask a follow-up question
  and the candidate would answer comfortably?
- Team size / individual contribution indicated? "Worked on the payments system" with 0
  specifics is not credible.
- Result metrics tied to a specific project (not generic "improved performance")?

**Hard rules:**
- When a tech-lead-level detail is missing, flag it as `[GAP]` and suggest what to record
  (e.g. "Record the streaming framework used and the p99 latency target, if you know them.")
- Do NOT invent technical details. A credibility gap is a real gap -- better left exposed than
  papered over with invented specifics.
- Quote verbatim text for context.

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: critique based
on the resume text; ask on any gap; never invent technical claims.
