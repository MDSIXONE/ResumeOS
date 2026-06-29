---
fragment: hiring-manager-review
inputs: [resume content]
outputs: [hiring manager evaluation]
applies: ADR-0007
---

# Hiring Manager Lens Review

Evaluate a resume as a hiring manager would: does this candidate have demonstrable IMPACT, does
the resume convey SCOPE, and are the claims CREDIBLE?

**Impact:**
- Are bullets outcome-driven (lead with metric / result) instead of duty-driven ("responsible
  for")?
- Is there at least one measurable result per major project?
- Impact statements should be the candidate's own impact, not their team's. "I drove X which
  resulted in Y" is good. "Team delivered X" does not convey personal impact.

**Scope:**
- Does the resume convey scale where available: team size, user base, budget, data size,
  performance characteristics?
- For senior candidates, does the resume show progression in responsibility (individual
  contributor -> lead -> architect)?
- Missing scope is not necessarily a weakness -- flag where the user could add detail if they
  have it.

**Credibility:**
- Claims proportional to role? "Senior engineer" listing only small side projects is a red
  flag. "Intern" listing "led a team of 20" is a red flag.
- "Unicorn" bullets listing every skill ever as one superproject are suspect.
- Overuse of buzzwords without supporting substance.

**Hard rules:**
- When a hiring-manager-level claim is missing (e.g. no team size, no scale figure), flag it as
  a `[GAP]` rather than suggesting a number.
- Do NOT invent impact metrics. If a bullet says "improved system performance" without a number,
  the improvement is: "Add a specific number if you have one, e.g. 'reduced p95 latency from X
  to Y' -- confirm the number before adding it."
- Quote the verbatim text of the concern.

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: critique based
on what the resume says; ask on any gap; never invent facts.
