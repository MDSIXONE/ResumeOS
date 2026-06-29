# resume_review

Review ANY resume -- vault-derived or external -- from four perspectives, and produce a
prioritized improvement report.

## When to use

- You have a vault-derived resume and want to catch any hallucination that slipped through
  generation (provenance cross-check).
- You have an external resume (pasted text) and want a multi-perspective review before
  submitting it.
- You want actionable rewording suggestions for weak bullets.

## How it works

See [SKILL.md](SKILL.md) for the full steps. In short:

1. **Ingest** the resume (file path or pasted text).
2. **4 review lenses** in sequence: ATS check, recruiter review, hiring manager review, tech lead
   review.
3. **Weak bullet detection** -- bullets missing metrics, weak verbs, redundancy.
4. **Provenance cross-check** (vault-cross-check mode only) -- every claim must trace to a
   vault entity.
5. **Prioritized improvement report** -- critical / important / nice-to-have, with concrete
   rewording suggestions that do NOT invent facts.
6. **Write** the report to `output/review/<slug>.md`.

## Inputs

- A resume (file path under `output/` or pasted Markdown / plain text).
- For vault-derived resumes: the vault (optional but recommended for provenance).

## Outputs

Written to `output/review/`:
- `<slug>.md` -- full review report covering all 4 lenses + weak bullets + provenance (if
  applicable) + prioritized improvements.

## Guardrails

- **Anti-hallucination (ADR-0007):** every improvement suggestion rewords or restructures; none
  invent facts.
- **No vault writes (ADR-0010):** this skill writes only to `output/**`.
- **No checkpoints:** emitted as a single report, not a phased pipeline.

## Related

- [resume_tailoring](../resume_tailoring/) -- the tailoring pipeline whose outputs this skill is
  often used to review.
- [ADR-0007 -- anti-hallucination](../../docs/decisions/ADR-0007-anti-hallucination-contract.md)
- [ADR-0010 -- content/derived separation](../../docs/decisions/ADR-0010-content-and-derived-separation.md)
- [Skill authoring spec](../../docs/guides/skill-authoring-spec.md)
