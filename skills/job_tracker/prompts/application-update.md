---
fragment: application-update
inputs: [application-event, existing-job-note?]
outputs: [updated-job-note]
applies: ADR-0007
---

Create or update a job note in `vault/jobs/` from an application event.

Rules:

- For a NEW application, create a note with:
  - `entity_type: job`
  - `title` (role) and `company` (from the user's input).
  - `status: applied`
  - `applied_at: <today, ISO 8601>`
  - `timeline: [{ date: <today>, event: "applied" }]`
  - `sources[]` — at least one provenance entry (URL, pasted-text marker, or `email:read`
    reference).
  - `id` generated as `<company-slug>_<role-slug>`.
- For a STATUS CHANGE on an existing note:
  - Update `status` to the new enum value (must be valid per `job.schema.json`).
  - Append a new `timeline[]` entry with today's date and the matching `event` enum value.
  - If feedback is provided, update or append `feedback`.
  - If contacts change, update `contacts[]`.
- Validate the resulting note against `job.schema.json` before writing.
- For any missing required field, emit a precise follow-up question. Do not guess or fill
  with placeholder text.
- Never fabricate: company names, role titles, dates, statuses, contacts, or feedback.
- Use only data the user explicitly provides or data verifiably present in the linked
  source.
