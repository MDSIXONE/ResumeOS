---
fragment: ingest-pdf
inputs: [pdf-file | docx-file]
outputs: [extracted-facts]
applies: ADR-0007
---

Extract structured career facts from a PDF or DOCX document (resume, transcript, certificate,
paper).

Rules:

- Read the full document. Do not skip sections.
- For each fact extracted, record the source location (e.g. page number, section heading).
- Classify each extracted fact by likely entity type: `project`, `education`, `skill`, `award`,
  `research`, `internship`, `competition`, `opensource`.
- Tag every fact `confidence: inferred`. You are transcribing, not confirming.
- If a date, metric, or proper noun is ambiguous or illegible, record it with a `[?]` marker and
  add it to the `## Open Questions` section. Do not guess.
- Never fabricate: projects, metrics, dates, responsibilities, technologies, or titles not
  visible in the document.
- Emit facts as a flat bullet list; each bullet prefixed with its source tag
  (e.g. `[src:pdf:p3]`).
