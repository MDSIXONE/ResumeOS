---
fragment: follow-up-question
inputs: [gap]
outputs: [follow-up-question]
applies: ADR-0007
---

Generate a precise, answerable follow-up question for a single detected gap.

Rules:

- Name the entity and the field that is missing or uncertain.
- Explain why it matters (schema requirement, tailoring relevance, or factual completeness).
- Offer a concrete, narrow question the user can answer in one or two sentences.
- Do NOT suggest a fabricated answer for the user to rubber-stamp.
- If the gap is trivially inferable from context, still ask — do not guess.
- Use the template:

  > Gap detected for `<entity>`: the schema requires `<field>`. The vault has no confirmed
  > fact for `<entity_id>:<field>`. <Specific question>? Answer, or say "omit" and I will
  > leave it out.

- Respect the user's "omit" answer. Mark the field `missing` and move on.
