# job_tracker

Track every job application, interview, offer, and rejection in `vault/jobs/*`. Generate
dashboards as Markdown tables and Dataview queries.

## When to use

- You have applied to a job and want to track it.
- You received an interview invite, offer, rejection, or follow-up request.
- You want a live dashboard of your application pipeline.

## How it works

See [SKILL.md](SKILL.md) for the full pipeline. In short:

1. **Step a — Read Existing Jobs:** load and validate all `vault/jobs/*.md` notes.
2. **Step b — New Application:** create a job note from the application event
   (`status: applied`, initial `timeline[]` event). Schema-validated.
3. **Step c — Status Change:** update `status`, append to `timeline[]`, record feedback.
   Optionally integrate with calendar / email MCPs.
4. **Step d — Dashboard Generation:** render `output/dashboard.md` grouping jobs by status,
   with a Dataview board-view query and a summary table.
5. **Step e — Regeneration Rule:** the dashboard is derived; never edit it directly;
   regenerate after any job-note change.

## Inputs

- New application details (JD, URL, pasted text).
- Status change events (screen → interview → offer / reject / accept / withdraw).
- Optional: email imports (via `email:read` MCP) and calendar events (via `calendar:create`
  MCP).

## Outputs

- Job notes in `vault/jobs/<id>.md`, each validated against `job.schema.json`.
- `output/dashboard.md` — a Markdown dashboard with a Dataview query and summary table.

## Guardrails

- **Anti-hallucination (ADR-0007):** every job note validated against `job.schema.json`;
  `timeline[]` events trace to confirmed dates; ask on uncertainty; never invent.
- **Derived dashboard (ADR-0001):** never edit `output/dashboard.md` directly; regenerate
  from vault notes.
- **Least-privilege:** can write only to `vault/jobs/**` and `output/**`; cannot touch
  `vault/career/**`.

## Related

- [ADR-0001 — knowledge base is SSOT](../../docs/decisions/ADR-0001-knowledge-base-as-single-source-of-truth.md)
- [ADR-0007 — anti-hallucination](../../docs/decisions/ADR-0007-anti-hallucination-contract.md)
- [Skill authoring spec](../../docs/guides/skill-authoring-spec.md)
