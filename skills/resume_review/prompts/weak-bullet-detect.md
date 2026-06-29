---
fragment: weak-bullet-detect
inputs: [resume bullets]
outputs: [weak bullets list with fix suggestions]
applies: ADR-0007
---

# Weak Bullet Detection

Scan every bullet in the resume and flag those that are weak by one or more dimensions.

**Weakness dimensions:**

1. **Missing metric.** The bullet describes work without a concrete number (count, percentage,
   duration, revenue impact, latency improvement, user count, etc.).
   - Flag: "No metric present."
   - Fix suggestion: "Add a specific number if available -- e.g., 'reduced p95 latency by X ms'
     -- but only if the number is real."

2. **Weak action verb.** The bullet starts with "Responsible for," "Worked on," "Helped with,"
   "Involved in," "Assisted in." These bury agency.
   - Flag: "Passive/weak verb."
   - Fix suggestion: rewrite with a direct action verb. "Designed," "Built," "Reduced,"
     "Led," "Shipped," "Optimized," "Migrated" -- but ONLY if the verb honestly reflects the
     candidate's role.

3. **Redundancy.** Two bullets say the same thing, possibly with different wording.
   - Flag: "Duplicate claim with <other bullet location>."
   - Fix suggestion: keep the stronger bullet; if both can be salvaged, differentiate them by
     scope.

4. **Length.** Bullets longer than 2 lines bury the point.
   - Flag: "Overly long bullet."
   - Fix suggestion: condense. Lead with the metric; drop the preamble.

**Output format per weak bullet:**
```
- **Location:** <section name, project title, bullet # or snippet>
- **Issue:** <weakness type>
- **Current text:** "<verbatim>"
- **Suggestion:** <concrete reword, or [GAP] if a metric is needed>
```

**Hard rules:**
- A fix suggestion MAY reword a confirmed fact. It may NEVER invent a metric or claim.
- If a weak bullet needs a metric, the suggestion is: "Add metric here if you have one -- do
  not invent."
- Do NOT flag a bullet as weak if it is already strong. False positives erode trust.

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: critique and
suggest based on the resume text only; ask on any gap; never invent.
