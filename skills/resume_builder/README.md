# resume_builder

Generate a **master resume** from the vault. No JD targeting; no phased pipeline. A single-pass generator that produces a comprehensive, reverse-chronological resume as the base document for tailoring or general use.

## When to use

- You have a populated vault and want a complete, JD-agnostic resume.
- You need a base document to feed into `resume_tailoring` for a specific job.
- You want a comprehensive career summary in any of the supported formats.

## How it works

See [SKILL.md](SKILL.md) for the full steps. In short:

1. **Read and validate** all `vault/career/*` entities against their schemas.
2. **Select** all confirmed entities; order reverse-chronologically per section.
3. **Render** sections using the global `resume-section.md` + `anti-hallucination.md` prompts. Every bullet is cited.
4. **Export** to markdown, DOCX, LaTeX, and/or JSON Resume into `output/master/`.

## Inputs

- A populated vault (`vault/career/*` entities).
- Run parameters: `language`, `resume_style`, `resume_length`, `formats`.

## Outputs

Written to `output/master/`:
- `master.md`, `master.docx`, `master.tex`, `master.json`

## Guardrails

- **Anti-hallucination (ADR-0007):** only confirmed vault facts; every bullet cited; ask on gaps.
- **No vault writes (ADR-0010):** this skill writes only to `output/**`.
- **No checkpoints:** the master resume is not a phased pipeline.

## Related

- [Architecture -- data flow](../../docs/architecture/data-flow.md)
- [ADR-0007 -- anti-hallucination](../../docs/decisions/ADR-0007-anti-hallucination-contract.md)
- [ADR-0010 -- content/derived separation](../../docs/decisions/ADR-0010-content-and-derived-separation.md)
- [Skill authoring spec](../../docs/guides/skill-authoring-spec.md)
