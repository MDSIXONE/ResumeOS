---
name: career_collector
version: 0.1.0
description: Collect raw career material (PDF/DOCX/MD/GitHub/LinkedIn/images/certs/blogs) into vault/inbox/ as provenanced notes.
schema_version: 1.0.0
inputs: []
outputs: [inbox-note]
mcp_tools: [filesystem:read, github:get_commits, github:get_prs, github:get_releases]
anti_hallucination: true
---

# career_collector

Ingest raw career material from external sources and stage it as structured notes in `vault/inbox/`.
Each staged note records `sources[]` provenance and marks extracted facts `confidence: inferred`
until the user confirms or `career_builder` validates them.

**career_collector never writes directly to `vault/career/*`.** That is `career_builder`'s role.

**Obey ADR-0007 at every step: state only confirmed vault facts; ask on any gap; never invent.**

---

## Inputs

- External material supplied by the user at runtime:
  - PDF / DOCX / Markdown files (resume, transcript, certificate, paper).
  - GitHub repository references (owner/repo, or a Gist URL).
  - LinkedIn data export (PDF or JSON).
  - Images of certificates, awards, or demo screenshots.
  - Blog posts, README files, personal website content.

## Outputs

- One or more staged notes written to `vault/inbox/<source-slug>_<timestamp>.md`.
  - Frontmatter includes `sources[]` (provenance), `confidence: inferred`, `kind` (entity guess).
  - Body holds extracted facts as bullet points, each tagged with its source reference.
- A final collection report summarizing what was ingested and flagging low-confidence extractions.

---

## Pipeline

### Step 1 — Source Classification

- **Inputs:** the user-provided material (file path, URL, or pasted text).
- **Work:** identify the source kind (`pdf`, `docx`, `md`, `github`, `linkedin`, `image`,
  `certificate`, `blog`, `readme`). For GitHub sources, resolve to commits / PRs / releases via
  MCP tools.
- **Outputs:** a source-kind label used by subsequent steps.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 2 — Extraction Per Source Kind

- **Compose:** the matching prompt fragment (see below) + `prompts/core/anti-hallucination.md`.
- **Work:** extract structured facts from the raw source:
  - **PDF / DOCX:** run the matching `prompts/ingest-pdf.md` prompt; extract text, identify
    entities (projects, roles, skills, dates), emit as bullet list.
  - **GitHub:** run `prompts/ingest-github.md`; call `github:get_commits`, `github:get_prs`,
    `github:get_releases`; summarize contributions, technologies, outcomes.
  - **LinkedIn:** run `prompts/ingest-linkedin.md`; parse the export; map sections to entity
    candidates (experience, education, skills, awards).
  - **Images / Certificates:** transcribe visible text, classify certificate type, record issuer
    and date if legible; mark any ambiguous text `confidence: inferred`.
  - **Blogs / READMEs:** extract project descriptions, tech stack, dates, outcomes.
- Every extracted fact is tagged `confidence: inferred` at this stage. The collector does NOT
  upgrade confidence.
- **Outputs:** a list of typed, provenanced fact candidates.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 3 — Staging Note Assembly

- **Compose:** `prompts/stage-note.md` + `prompts/core/anti-hallucination.md`.
- **Work:** build a single inbox note per source. The note includes:
  - Frontmatter: `entity_type: inbox`, `kind` (guessed entity type), `sources[]` (required, at
    least one entry with `kind` + `ref`), `confidence: inferred`, `created_at`, `tags[]`.
  - Body: extracted facts as bullet points, each prefixed with a source tag
    (e.g. `[src:pdf:p3]`, `[src:github:commit:abc123]`).
  - An `## Open Questions` section listing anything ambiguous or incomplete.
- **Outputs:** the staged note written to `vault/inbox/<source-slug>_<timestamp>.md`.
- Validate: every staged note MUST have `sources[]` with at least one entry. A note with empty
  `sources[]` is a staging failure; report it and do not write the file.

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

### Step 4 — Collection Report

- **Inputs:** all notes staged in this run.
- **Work:** produce a summary listing:
  - Sources ingested (count and kinds).
  - Notes created (paths).
  - Low-confidence extractions flagged (items the user must verify or enrich).
  - Suggested next step: run `career_builder` to validate, classify, and enrich the staged notes.
- **Outputs:** a Markdown report printed to the user (not persisted to the vault or output/).

Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

---

## Prompt Fragments

| Stage | Prompt |
|-------|--------|
| PDF / DOCX ingestion | `prompts/ingest-pdf.md` |
| GitHub ingestion | `prompts/ingest-github.md` |
| LinkedIn ingestion | `prompts/ingest-linkedin.md` |
| Staged note assembly | `prompts/stage-note.md` |

Always compose the relevant fragment with `prompts/core/anti-hallucination.md`.

---

## Anti-hallucination Enforcement

- Every staged note carries `sources[]` with at least one provenance entry.
- All extracted facts carry `confidence: inferred`; the collector never upgrades to `confirmed`.
- An extraction that cannot be traced to a source token is flagged in the `Open Questions` section,
  not silently included.
- The collector does not write to `vault/career/*` or `vault/jobs/*` (enforced by deny permissions).

## Failure Modes

- Unreadable file (corrupt PDF, binary image with no OCR path): report the failure, do not stage
  a partial note.
- GitHub API returns no results for a given repo: report, ask the user to verify the repository
  reference.
- LinkedIn export format unrecognized: report, ask the user to confirm the export version.
