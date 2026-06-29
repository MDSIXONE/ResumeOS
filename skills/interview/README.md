# interview

Generate a comprehensive **interview preparation pack** grounded entirely in vault-confirmed facts.

## When to use

- You have an upcoming interview and want to rehearse questions grounded in your actual project history.
- You want to identify weak spots in your vault that an interviewer could probe.
- You want a mock Q&A script you can practice from.

## How it works

See [SKILL.md](SKILL.md) for the full steps. In short:

1. **Read** vault entities (and optional JD).
2. **Behavior questions** -- drawn from your real projects, not invented scenarios.
3. **Technical questions** -- probed from your confirmed `stack` fields.
4. **Project-deep-dive questions** -- 2-4 per project entity.
5. **STAR answers** -- built from confirmed fields; missing metrics flagged, not invented.
6. **Weakness analysis** -- thin vault areas to prepare for honestly.
7. **Mock interview script** -- a rehearsed Q&A for practice.
8. **Write** `interview-prep.md` to `output/<job-slug-or-general>/`.

## Inputs

- Vault: `project`, `education`, `skill` entities (required).
- `job` entity / JD (optional -- when provided, targets the pack).
- Run parameters: `language` (zh | en).

## Outputs

Written to `output/<job-slug>/` (or `output/general/`):
- `interview-prep.md`

## Guardrails

- **Anti-hallucination (ADR-0007):** only confirmed vault facts; every STAR answer cited; ask on gaps.
- **No vault writes:** this skill writes only to `output/**`.
- **No checkpoints:** emitted as a single document, not a phased pipeline.

## Related

- [career_builder](../career_builder/) -- the enrichment skill that fills vault gaps surfaced here.
- [ADR-0007 -- anti-hallucination](../../docs/decisions/ADR-0007-anti-hallucination-contract.md)
- [Skill authoring spec](../../docs/guides/skill-authoring-spec.md)
