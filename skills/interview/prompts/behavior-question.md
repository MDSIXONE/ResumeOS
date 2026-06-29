---
fragment: behavior-question
inputs: [vault projects, education, skills]
outputs: [behavior questions list]
applies: ADR-0007
---

# Behavior Question Generation

Generate 6-10 behavior interview questions grounded in the candidate's REAL project history.

**Source of questions:** the candidate's confirmed project entities. Each question must be
answerable from at least one vault entity. Do not fabricate hypothetical scenarios the candidate
has never lived.

**Question shape:**
- "Tell me about a time when..."
- "Describe a situation where you..."
- "Give an example of..."
- "What would you do differently in..."

**Question categories to cover (pick from what the vault supports):**
- Collaboration / team dynamics
- Conflict resolution
- Failure / debugging / recovery
- Leadership / initiative
- Deadline / pressure
- Learning a new skill or technology
- Impact / measurable results

**Hard rules:**
- Every question must map to at least one confirmed project entity. If the vault has no entity
  that supports a natural behavior question on, say, "team conflict," do NOT invent one.
- If the JD is provided, weight questions toward the soft skills the JD highlights.
- Each question must be answerable using STAR from the vault. If no STAR element is missing,
  the candidate can practice; if one is missing, the question surfaces a rehearsal gap.

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: state only
confirmed vault facts; ask on any gap; never invent.
