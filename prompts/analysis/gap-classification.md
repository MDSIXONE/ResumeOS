---
fragment: gap-classification
applies: ADR-0006 Phase 2
inputs: [research.json, library.json]
outputs: [gaps.json items]
---

# Gap Classification

Compare the vault library against the JD-derived requirements. Classify each requirement into one
of three gap states:

| State | Meaning | Action |
|---|---|---|
| `covered` | A confirmed vault fact satisfies this requirement. | Select it in Phase 3 assembly. |
| `underdeveloped` | A vault fact partially satisfies, but is weak (vague, no metric, thin role). | Surface to user: "strengthen this in the vault?" — do not pad. |
| `missing` | No vault fact satisfies this requirement. | Emit an `ask-never-invent` follow-up. Never fabricate. |
| `misaligned` | A vault fact exists but its framing does not match the JD's vocabulary. | In Phase 3, reframe using a JD synonym (e.g. "PyTorch" ↔ "深度学习框架") — rewording only, not invention. |

**For each gap, record in `gaps.json`:**
```json
{
  "requirement": "<JD requirement>",
  "state": "covered | underdeveloped | missing | misaligned",
  "candidate": { "entity_id": "...", "field": "...", "confidence": "confirmed|inferred|missing" },
  "action": "select | ask | reframe | omit",
  "severity": "high | medium | low"
}
```

Rank gaps by severity. A `missing` high-severity requirement (e.g. a core required skill) must be
raised to the user before assembly, because omitting it likely means rejection.
