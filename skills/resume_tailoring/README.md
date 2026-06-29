# resume_tailoring

Tailor a resume to a specific job description using a **6-phase, checkpoint-based pipeline**.

## When to use

- You have a specific job description and a populated vault.
- You want the best possible resume for *that* job, grounded only in confirmed facts.

## How it works

See [SKILL.md](SKILL.md) for the full pipeline. In short:

1. **Phase 0 — Library Build:** index the vault.
2. **Phase 1 — Research** (checkpoint): parse JD, research company, extract ATS keywords.
3. **Phase 2 — Gap Analysis** (checkpoint): classify requirements; ask on gaps, never invent.
4. **Phase 3 — Assembly** (checkpoint): rank projects, reword confirmed bullets, cite everything.
5. **Phase 4 — Generation:** render Markdown → DOCX / LaTeX / JSON Resume.
6. **Phase 5 — Library Update:** save learnings for the next run.

## Inputs

- A job description (text, URL, or a `vault/jobs/<id>.md` note).
- Run parameters: `language`, `resume_style`, `resume_length`, `formats`.

## Outputs

Written to `output/<job-slug>/`:
- `artifacts/{library,research,gaps,assembly}.json` (phase artifacts, auditable)
- `resume.md`, `resume.docx`, `resume.tex`, `resume.json`
- `vault/.library/<job-slug>.json` (self-improving memory)

## Guardrails

- **Anti-hallucination (ADR-0007):** only confirmed vault facts; every bullet cited; ask on gaps.
- **Checkpoints (ADR-0006):** you review research, gaps, and assembly before generation.
- **Re-runnable:** edit a checkpoint artifact and resume from that phase.

## Related

- [Architecture — data flow](../../docs/architecture/data-flow.md)
- [ADR-0006 — checkpoint pipeline](../../docs/decisions/ADR-0006-checkpoint-phased-pipeline.md)
- [ADR-0007 — anti-hallucination](../../docs/decisions/ADR-0007-anti-hallucination-contract.md)
- [Skill authoring spec](../../docs/guides/skill-authoring-spec.md)
