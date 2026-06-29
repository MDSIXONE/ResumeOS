---
fragment: generate-interview-questions
inputs: [enriched-entity]
outputs: [interview-question-list]
applies: ADR-0007
---

Generate likely interview questions an enriched entity invites.

Rules:

- Questions must trace to confirmed entity fields. Each question includes a `cites`
  reference to the field(s) it probes.
- Cover three angles:
  - Contribution / role-specific: "Walk me through your role in <project>."
  - Technical depth: "How did you implement <algorithm/stack item>?"
  - Outcome / reflection: "What was the measurable result? What would you do differently?"
- Do not fabricate context for questions. If the entity lacks a metric, the question should
  ask about the qualitative outcome, not invent a number.
- Store the question list in the entity's `interview_questions[]` frontmatter field.
- Keep the list focused: 3–8 questions per entity.
