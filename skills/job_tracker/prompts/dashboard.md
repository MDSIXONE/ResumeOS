---
fragment: dashboard
inputs: [validated-job-notes]
outputs: [dashboard-markdown]
applies: ADR-0001
---

Render a Markdown dashboard from all validated job notes in `vault/jobs/`.

Rules:

- Group jobs by `status` in this order: `discovered`, `preparing`, `applied`, `screening`,
  `interviewing`, `offer`, `rejected`, `accepted`, `withdrawn`.
- Within each group, sort by most recent `timeline[]` event date, descending.
- Each row includes: title, company, location (if set), applied_at date, status badge tag,
  and a wikilink to the job note.
- Include a Dataview query block that renders a board view grouped by `status`:

  ```dataview
  TABLE company, location, applied_at
  FROM "vault/jobs"
  WHERE status != "withdrawn"
  SORT applied_at DESC
  GROUP BY status
  ```

- Add a summary section at the top:
  - Total applications.
  - Per-status counts.
  - Upcoming interviews (jobs with status = `interviewing`).
  - Oldest active applications (status != `rejected`, `accepted`, `withdrawn`).
- All dashboard facts trace back to job note fields. Do not invent any row, count, or
  status.
- Output to `output/dashboard.md`. Never edit this file directly — regenerate from the
  vault notes.
