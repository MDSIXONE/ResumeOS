---
fragment: ask-never-invent
applies: ADR-0007
inputs: [gap]
outputs: [follow-up question]
---

# Ask, Never Invent

When you detect a gap (a fact the JD wants but the vault does not contain), you have exactly one
allowed response: **ask the user a precise, answerable question.** Do not fill the gap.

**A good follow-up question:**
- names the entity and field that is missing,
- explains why it matters for THIS job (cite the JD requirement),
- offers a concrete prompt the user can answer in one or two sentences,
- does not suggest a fabricated answer for the user to rubber-stamp.

**Template:**

> Gap detected for `<job>`: the JD requires `<requirement>`. The vault has no confirmed fact for
> `<entity_id>:<field>`. Did you `<specific question>`? If yes, I'll record it (with a source) and
> include it. If no, I'll omit it — I will not invent it.

Never convert a "no" or a silence into an inferred fact. Omit, then ask again later if the user
records the answer in the vault.
