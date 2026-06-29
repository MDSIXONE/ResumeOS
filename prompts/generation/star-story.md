---
fragment: star-story
applies: career_builder, interview
inputs: [project entity]
outputs: [STAR narrative]
---

# STAR Story Generation

Turn a **confirmed** project entity into a STAR narrative for interviews and resumes.

**Structure:**
- **Situation:** the context — company, competition, timeline, team size. All from frontmatter.
- **Task:** the problem/goal — from the entity's `problem`/`goal` (body sections).
- **Action:** what YOU did — from `contribution` + `stack`. First person, action verbs.
- **Result:** the outcome — from `metrics` ONLY. If `metrics` is empty, the Result is "outcome not
  quantified" and you MUST ask the user for a metric rather than inventing one.

**Rules:**
- Use only fields present in the entity. No invented stakes, numbers, or responsibilities.
- If a STAR element is missing from the vault, emit an `ask-never-invent` follow-up, not a guess.
- Keep the story tight: 4–6 sentences, interview-spoken register.
- Tag the output with citations: `entity_id:field` per element.

A STAR story is only as strong as the vault behind it. Thin vault → thin story → the correct
response is to enrich the vault, not to embellish the story.
