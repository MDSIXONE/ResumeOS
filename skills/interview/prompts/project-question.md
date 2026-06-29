---
fragment: project-question
inputs: [project entity]
outputs: [project deep-dive questions]
applies: ADR-0007
---

# Project Deep-Dive Question Generation

Generate 2-4 deep-dive interview questions for a specific project entity. The goal is to simulate
the "walk me through this project" portion of an interview, where the interviewer probes the
candidate's actual work.

**Question angles (pick from what the entity supports):**
- Architecture: "Explain the high-level architecture. What were the key components?"
- Contribution: "What was your specific contribution, vs. the team's?"
- Trade-offs: "What trade-offs did you make? What would you do differently?"
- Metrics: "What was the measurable impact? How did you measure it?"
- Failure: "What went wrong? What did you learn?"
- Scope: "What was the team size? Your role? The timeline?"
- Tech choice: "Why did you pick X over Z?"

**Rules:**
- Draw questions only from the fields present in the entity. If the entity has no `metrics` field,
  do NOT ask "what was the measurable impact" -- instead flag that as a rehearsal gap.
- If the entity has a `confidence: inferred` field, do not build a question that would require the
  candidate to defend it as a confirmed fact.
- Questions should be in the voice of an interviewer, not a study guide ("Walk me through..." not
  "Study the architecture of...").

**Output format per project:**
```
## <project title>

1. <question 1>
2. <question 2>
3. <question 3>
[4. <optional question 4>]
```

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: state only
confirmed vault facts; ask on any gap; never invent.
