---
fragment: mock-interview
inputs: [behavior questions, technical questions, project questions, STAR answers, weakness analysis]
outputs: [rehearsal Q&A script]
applies: ADR-0007
---

# Mock Interview Script

Produce a rehearsed Q&A script of 8-12 questions mixing behavior, technical, and project-deep-dive
questions. The candidate reads and practices this script aloud before the real interview.

**Structure:**
- Alternate question types to simulate a real interview: open with a behavior question, follow
  with a technical, then a project, then another behavior, etc.
- Weight toward the candidate's strongest areas first (builds confidence), then introduce gaps
  (practices the hard answers).

**Per question:**
- State the question in interviewer voice.
- Provide a suggested answer drawn from the STAR outputs. Every fact in the answer must be a
  confirmed vault fact.
- Annotate with citations: `[cite: entity_id:field]` so the candidate can verify.
- If the answer depends on a weakness or gap identified in the weakness analysis, mark it clearly:
  `[GAP: <what is missing>. Record in vault before relying on this answer.]`

**Tone:**
- The script reads like an interview, not a study guide. Questions are natural spoken English
  (or zh), answers are complete sentences the candidate could actually say aloud.
- Keep answers tight: 30-60 seconds of speaking time each.

**Hard rules:**
- No fabricated answers. If a STAR answer is missing an element, the script includes the question
  but the answer is flagged as `[GAP]` with guidance on how to answer honestly in the meantime.
- If a question probes a vault gap, include guidance: "If asked this, pivot to what the vault
  DOES confirm: <suggest a transfer>."

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: state only
confirmed vault facts; ask on any gap; never invent.
