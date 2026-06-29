---
fragment: cover-letter-section
inputs: [job note, selected project entities, skills, education]
outputs: [cover letter markdown]
applies: ADR-0007
---

# Cover Letter Composition

Render a personalized, grounded cover letter for a specific job. The letter MUST be built from
confirmed vault facts only. No invented achievements, no implied responsibilities the candidate
did not actually take on.

**A cover letter may:**
- Reframe a confirmed fact to match the role narrative (e.g. present a class project as
  "hands-on ML experience" if the project's `stack` and `metrics` confirm it).
- Order facts by relevance to the JD.
- Omit irrelevant vault facts.

**A cover letter may NOT:**
- Claim a project, metric, skill, responsibility, or accomplishment not present in the vault.
- Imply a role seniority the vault does not support (e.g. "led a team" when the vault says
  "contributed").
- Invent company knowledge beyond what the JD or the research artifact states.

**Structure (3-4 paragraphs, ~250-400 words):**

1. **Opening** (1 short paragraph): state the role you are applying for; one sentence on why
   you want it, grounded in what the JD or company research artifact says about the team /
   mission.
2. **Body A** (1 paragraph): your strongest 1-2 project references. Each reference is a
   confirmed entity, cited as `entity_id:field`. Use the STAR shape lightly -- Situation/Task
   in one sentence, Action (what YOU did) in one sentence, Result (from `metrics`) in one
   sentence.
3. **Body B** (optional, 1 short paragraph): connective tissue -- relevant skills from the
   `skill` entity, education background, or a second project if the role needs range.
4. **Close** (1 short paragraph): enthusiasm + a concrete next step (e.g. "I would welcome
   the chance to discuss..."). Do not invent enthusiasm; if unsure how to close, use a neutral
   professional formula.

**Language:** match `config.defaults.language` (zh or en). Do not mix languages.

**Citation sidecar:** while drafting, attach `entity_id:field` to every project/metric/skill
mention. The sidecar is emitted separately for audit. The rendered letter has citations
stripped before write.

**Self-check before emitting:**
1. Can every mention of a project / metric / skill be tied to a vault field? If no, drop it.
2. Does the narrative imply a responsibility I did not actually have? If yes, soften or drop.
3. Is the tone honest and professional -- not puffed up?

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: state only
confirmed vault facts; ask on any gap; never invent.
