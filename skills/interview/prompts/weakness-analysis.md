---
fragment: weakness-analysis
inputs: [vault entities, optional JD]
outputs: [weakness report]
applies: ADR-0007
---

# Weakness Analysis (thin-vault areas)

Identify areas of the vault that are thin or ambiguous and that an interviewer could probe. For
each weakness, frame what the interviewer might ask and how the candidate should answer honestly.

**Weakness types to scan for:**

1. **Missing result metrics.** Projects with `contribution` but empty `metrics`. The candidate
   can describe the work but cannot claim a quantified impact. Surface: "The vault records
   <entity_id>:contribution but no `metrics`. Prepare to describe the contribution without a
   number, or record a metric in the vault before the interview."

2. **Shallow role descriptions.** Entities where `role` or `contribution` is vague ("contributed
   to the backend"). The interviewer will ask "what specifically did you do?" and the candidate
   needs a concrete answer. Surface: "The vault records <entity_id>:role as generic. Record a
   concrete contribution before relying on this for an interview answer."

3. **Employment / timeline gaps.** If the vault has no entities for a known period the candidate
   was working, the interviewer may ask "what were you doing between X and Y?" The candidate
   should rehearse an honest answer without fabricating project experience.

4. **JD technical gaps (if JD provided).** Technologies the JD requires but the vault does not
   contain. Do NOT fake experience. The honest answer is: "I haven't used X professionally, but
   I have used Y which solves a similar problem." Surface the gap and suggest the transfer
   narrative.

5. **Soft-skill evidence gaps.** The vault may not record team size, collaboration, or conflict
   resolution. If the interview is for a role that values these, the candidate should rehearse
   honest answers grounded in whatever small evidence exists.

**Output format:**
```
## Weakness: <title>
- **Vault signal:** <what is thin / missing in the vault>
- **Interviewer may ask:** <the likely question>
- **Answer honestly:** <what to say>
- **Vault action:** <what to record in the vault to fix this> (if applicable)
```

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: state only
confirmed vault facts; ask on any gap; never invent.
