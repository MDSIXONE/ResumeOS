---
name: job_tracker
version: 0.1.0
description: Track job applications, interviews, offers, and rejections in vault/jobs; maintain timelines and generate dashboards.
schema_version: 1.0.0
inputs: [job]
outputs: [job, dashboard]
mcp_tools: [calendar:create, email:read]
anti_hallucination: true
---

# job_tracker

Track every job application in `vault/jobs/*` (validated against `job.schema.json`). Maintain
`timeline[]`, `status`, `contacts[]`, and `feedback` per application. Generate dashboards as
Markdown tables and Dataview queries.

**Obey ADR-0007 at every step: state only confirmed vault facts; ask on any gap; never invent.**

---

## Inputs

- Application events supplied by the user at runtime:
  - A new application (JD, URL, or pasted description).
  - A status change (screening → interviewing → offer / rejected / withdrawn / accepted).
  - Interview scheduling, feedback, or contact information.
  - Email imports parsed via `email:read` (optional MCP).
- `vault/jobs/*` — existing job notes.
- `schemas/job.schema.json` — entity schema for validation.

## Outputs

- Job notes in `vault/jobs/<id>.md`, each validated against `job.schema.json`.
- `output/dashboard.md` — the application dashboard (Markdown table + Dataview query).

---

## Pipeline

### Step a — Read Existing Jobs

- **Inputs:** all `vault/jobs/*.md`.
- **Work:** parse each note; validate frontmatter against `job.schema.json`. Skip and report
  invalid entries.
- **Outputs:** a validated list of existing job notes, used as working state.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step b — New Application

- **Compose:** `prompts/application-update.md` + `prompts/core/anti-hallucination.md`.
- **Inputs:** a new application event from the user.
- **Work:** build a job note:
  - Frontmatter: `entity_type: job`, `title`, `company`, `status: applied`, `applied_at`
    (today's date, ISO 8601), `timeline[]` with the first `applied` event.
  - `sources[]` — provenance (URL, pasted text, or `email:read` reference).
  - `location`, `remote`, `url`, `tags[]` — filled only from user-provided values.
  - Validate against `job.schema.json` before writing.
  - Required missing fields → emit a follow-up question. Do not invent.
- **Outputs:** `vault/jobs/<company-slug>_<role-slug>.md`.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step c — Status Change / Timeline Append

- **Compose:** `prompts/application-update.md` + `prompts/core/anti-hallucination.md`.
- **Inputs:** a status change event for an existing job.
- **Work:**
  - Update `status` to the new enum value (`discovered`, `preparing`, `applied`, `screening`,
    `interviewing`, `offer`, `rejected`, `accepted`, `withdrawn`).
  - Append a `timeline[]` event with `date` (ISO 8601) and the matching `event` enum value.
  - If `feedback` is provided, append it.
  - If MCP `calendar:create` is enabled and the user schedules an interview, create the
    calendar event and record the result in the `timeline[]` note.
  - If MCP `email:read` is enabled and the user imports an offer/reject email, parse it for
    facts and append to `timeline[]`; do not invent anything not explicitly in the email.
  - Validate the updated note against `job.schema.json` before writing.
- **Outputs:** updated `vault/jobs/<id>.md`.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step d — Dashboard Generation

- **Compose:** `prompts/dashboard.md` + `prompts/core/anti-hallucination.md`.
- **Inputs:** all `vault/jobs/*.md` (validated).
- **Work:**
  - Build a Markdown dashboard grouping jobs by `status`.
  - Include a Dataview query block that renders as a board view in Obsidian.
  - Add a summary table: total applications, per-status counts, upcoming interviews, and
    oldest active applications.
  - Every row links back to the job note. No facts are duplicated outside the note.
- **Outputs:** `output/dashboard.md`.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step e — Regeneration Rule

- The dashboard is a derived document (ADR-0001). If the user edits `output/dashboard.md`
  directly, discard the edit and regenerate from the job notes.
- If a job note changes, the dashboard is out of date. Re-run Step d to regenerate.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

---

## Prompt Fragments

| Step | Prompt |
|------|--------|
| Application update | `prompts/application-update.md` |
| Dashboard generation | `prompts/dashboard.md` |

Always compose local fragments with `prompts/core/anti-hallucination.md`.

---

## Anti-hallucination Enforcement

- Job notes are schema-validated against `job.schema.json` before every write.
- `timeline[]` events carry exact `date` + `event` enum values; no invented dates or events.
- Dashboard content is a pure projection of the vault — no facts are invented or persisted in
  the dashboard.
- Email / calendar MCP integrations add facts only when the source data is unambiguous;
  anything uncertain is flagged and asked about.

## Failure Modes

- A `vault/jobs/*.md` note fails schema validation: report it, skip it, do not abort the
  dashboard run.
- A status change event specifies an unknown enum value: ask the user to choose from the
  schema's `status` enum.
- Email parse returns ambiguous data: ask the user to confirm; do not auto-assign.
