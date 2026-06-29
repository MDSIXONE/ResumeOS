# cover_letter

Generate a **personalized cover letter** for a specific job, grounded only in confirmed vault facts.

## When to use

- You have a specific job description, a populated vault, and want to send a cover letter tailored to that role.
- You have already run `resume_tailoring` for the same job and want to reuse the research artifact for consistency.

## How it works

See [SKILL.md](SKILL.md) for the full steps. In short:

1. **Read** the job note/JD + vault entities + (if present) the `resume_tailoring` `research.json` artifact.
2. **Select** 1-2 projects whose confirmed facts best match the JD.
3. **Compose** the letter using `cover-letter-section.md` + `anti-hallucination.md`. Every project/metric cited.
4. **Write** `cover-letter.md` (and optional `.docx`) to `output/<job-slug>/`.

## Inputs

- A job description (text, URL, or a `vault/jobs/<id>.md` note).
- Vault: `project`, `education`, `skill` entities.

## Outputs

Written to `output/<job-slug>/`:
- `cover-letter.md`
- `cover-letter.docx` (optional)
- `cover-letter.provenance.md` (sidecar with citation audit trail)

## Guardrails

- **Anti-hallucination (ADR-0007):** only confirmed vault facts; every project/metric cited; ask on gaps.
- **Reframing, not inventing (ADR-0010):** a cover letter may present a vault fact from a different angle; it cannot claim a fact that is not in the vault.
- **No vault writes:** this skill writes only to `output/**`.

## Related

- [resume_tailoring](../resume_tailoring/) -- the tailoring pipeline whose research artifact this skill can reuse.
- [ADR-0007 -- anti-hallucination](../../docs/decisions/ADR-0007-anti-hallucination-contract.md)
- [ADR-0010 -- content/derived separation](../../docs/decisions/ADR-0010-content-and-derived-separation.md)
- [Skill authoring spec](../../docs/guides/skill-authoring-spec.md)
