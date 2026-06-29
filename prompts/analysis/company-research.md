---
fragment: company-research
applies: ADR-0006 Phase 1, ADR-0008 (optional browser MCP)
inputs: [company name, job description]
outputs: [research.json: company]
---

# Company Research

Build a compact, factual profile of the hiring company to inform tone, emphasis, and framing.

**Gather (only from provided material or explicitly approved MCP/browser sources; cite every
fact):**
- Mission / product / market.
- Engineering culture signals (tech blog, open-source activity, stack mentions in JD).
- Leadership principles / values (if published, e.g. Amazon's LPs).
- Hiring style (e.g. "heavy system design", "take-home heavy", "culture-fit first").
- Size, stage, and any public scale signals.

**Output (into `research.json: company`):**
```json
{
  "name": "...",
  "mission": "...",
  "culture_signals": ["..."],
  "leadership_principles": ["..."],
  "hiring_style": "...",
  "stack_signals": ["..."],
  "sources": [{"kind":"browser","ref":"<url>"}]
}
```

**Anti-hallucination:** if a field cannot be sourced, leave it `null` and flag it. Do not invent a
culture or values statement. When the `browser` MCP server is unavailable, work only from the JD
text and the user's input.
