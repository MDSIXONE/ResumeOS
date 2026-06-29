---
fragment: technical-question
inputs: [vault project entities, skill entities]
outputs: [technical questions list]
applies: ADR-0007
---

# Technical Question Generation

Generate 8-15 technical interview questions from the candidate's confirmed entity `stack` fields.

**Source of questions:** the `stack` field of every `project`, `research`, `internship`, and
`opensource` entity. This is the set of technologies the candidate has ACTUALLY used. Questions
must probe these, not imagined ones.

**Depth vs. breadth:**
- **Primary stack items** (appear in 2+ projects, or are explicitly marked as strong skills in a
  `skill` entity): ask depth questions -- internals, architecture trade-offs, debugging war stories,
  performance tuning.
- **Secondary stack items** (appear in 1 project, or are listed as basic skills): ask breadth
  questions -- what it is, why it was chosen, how it fits the larger architecture.

**Question types to consider:**
- "Explain how X works under the hood in project Y."
- "Why did you choose X over Z in project Y?"
- "What was the hardest bug you debugged with X?"
- "Walk me through the data flow in your X-based system."
- "What would you change about your X implementation today?"

**Hard rules:**
- Do NOT generate a question about a technology not present in any vault `stack` field. If the
  candidate has never used Kubernetes, asking them about Kubernetes is not prep -- it is fiction.
- If the JD is provided and mentions a technology the vault does not contain, surface this as a
  gap (the candidate should prepare a transfer narrative or a "haven't used it but..." answer),
  rather than fabricating a question.
- Group questions by stack item for the candidate's study plan.

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: state only
confirmed vault facts; ask on any gap; never invent.
