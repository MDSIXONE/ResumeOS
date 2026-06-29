---
fragment: ingest-linkedin
inputs: [linkedin-export]
outputs: [extracted-facts]
applies: ADR-0007
---

Extract structured career facts from a LinkedIn data export (PDF or JSON format).

Rules:

- Map LinkedIn sections to ResumeOS entity candidates:
  - Experience → `project` or `internship`
  - Education → `education`
  - Skills → `skill`
  - Honors & Awards → `award`
  - Publications → `research`
  - Courses / Certifications → `education` or `certificate`
  - Projects → `project`
- Tag every fact `confidence: inferred`. LinkedIn self-reported data is not yet confirmed.
- For each fact, record the source section as the provenance tag
  (e.g. `[src:linkedin:experience:<company>]`).
- If a field is blank, end-dated, or ambiguous, note it in `## Open Questions`. Do not fill
  gaps.
- Do not infer endorsements, recommendations, or connection counts beyond what the export
  explicitly contains.
- Emit facts as a flat bullet list with source tags.
