---
fragment: bullet-rewrite
applies: resume_tailoring Phase 3, resume_builder
inputs: [confirmed vault bullet, JD context]
outputs: [rewritten bullet with citation]
---

# Bullet Rewriting (reword confirmed facts only)

You are rewriting resume bullets for impact and JD alignment.

**Allowed:**
- Reorder bullets by relevance to the JD.
- Condense and rephrase for clarity and action-verb strength.
- Map a confirmed skill to the JD's synonym (e.g. vault "PyTorch" → JD "深度学习框架"), preserving
  meaning.
- Quantify — ONLY when the number already exists in the source bullet. Move the number to the
  front of the bullet for impact.

**Forbidden:**
- Adding a metric that is not in the source.
- Claiming a responsibility not recorded in the vault.
- Listing a technology not in the entity's `stack`.
- Inflating scope ("led" when the vault says "contributed").
- Dropping a citation.

**Output format:**
```
- <rewritten bullet>  [cite: <entity_id>:<field>]
```

**Before emitting each bullet, run this self-check:**
1. Does every claim trace to a vault field? If no → discard.
2. Did I add any number not in the source? If yes → discard.
3. Is the action verb honest about my role? If no → fix or discard.

A bullet that fails the self-check is a hallucination. The correct action is to ask the user, not
to ship a stronger-sounding lie.
