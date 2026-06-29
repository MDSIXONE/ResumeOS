# Roadmap

This roadmap tracks ResumeOS development phases.

---

## Phase Alpha (in progress)

**Goal:** Stabilize the core data model and built-in Skill set.

| Task | Status | Reference |
|---|---|---|
| Vault schemas v1.0.0 (9 entity types + JSON Schema draft 2020-12) | ✓ Done | ADR-0002 |
| `plugin-manifest.schema.json` + root bundle manifest | ✓ Done | ADR-0004, ADR-0005 |
| 9 built-in Skills (each with `SKILL.md`, `plugin.json`, `prompts/`) | ✓ Done | `skills/registry.yaml` |
| `resumeos.config.yaml` central configuration | ✓ Done | — |
| Example vault (`examples/vault/`) with fixtures | ✓ Done | — |
| Example output (`examples/output/`) with derived artifacts | ✓ Done | ADR-0006 |
| CI: schema validation + pytest on every PR | ✓ Done | `.github/workflows/ci.yml` |
| Plugin development guide + skill authoring spec | ✓ Done | `docs/guides/` |
| Obsidian setup guide for end users | ✓ Done | `docs/guides/obsidian-setup.md` |
| Real vault scaffolding (`vault/` folder-notes + `vault.meta.yaml`) | In progress | ADR-0001, ADR-0003 |

---

## Phase Beta

**Goal:** Add external adapters and rich Obsidian views.

| Task | Status | Reference |
|---|---|---|
| MCP adapter: GitHub ingests (commits, PRs, releases) → project notes | Planned | ADR-0008 |
| MCP adapter: Browser tool for JD scraping / company research | Planned | ADR-0008 |
| MCP adapter: Google Drive (PDFs, docs, images) → `inbox/` | Planned | ADR-0008 |
| Dataview dashboards: job pipeline, career timeline, skill gaps | Planned | ADR-0003 |
| JSON Resume 1.0.0 round-trip: ResumeOS ↔ JSON Resume converter | Planned | ADR-0002 |
| `career_collector`: LinkedIn profile export ingest via MCP | Planned | ADR-0008 |
| `job_tracker`: Calendar adapter for interview scheduling | Planned | ADR-0008 |
| Templater enhancements: QuickAdd flows for common entity creation | Planned | ADR-0003 |
| `resume_builder`: DOCX output (Pandoc-based) | Planned | — |
| `resume_builder`: LaTeX output (XeLaTeX / CTEX) | Planned | — |
| `vault-meta.schema.json` + `vault/vault.meta.yaml` | In progress | `schemas/` |

---

## Phase 1.0

**Goal:** Public release, community contributions, and polish.

| Task | Status | Reference |
|---|---|---|
| Plugin marketplace: registry.yaml → discoverable Skill hub | Planned | ADR-0004 |
| Skill install/uninstall commands (agent-runtime loader) | Planned | ADR-0004 |
| Multi-device sync vault guide (Git + Obsidian Git / Syncthing) | Planned | ADR-0001 |
| Portfolio / website generator (Vault → static site) | Planned | ADR-0010 |
| `resume_review`: ATS scoring against real-world filters | Planned | ADR-0007 |
| `resume_tailoring`: Phase 0 library build with embedding vectors | Planned | ADR-0006 |
| Versioned schema migration tool (`schemas/migrations/` runner) | Planned | ADR-0002 |
| Community Skill contributions (first external PRs welcome) | Planned | ADR-0004 |
| End-user documentation rewrite (quick starts, video demos) | Planned | — |

---

## Future

Ideas and possibilities; no commitment yet.

- LinkedIn bidirectional adapter (mirror, not master — ADR-0008).
- Notion bidirectional mirror adapter.
- Google Drive sync adapter (full vault sync, not just ingest).
- CRDT sync for multi-device concurrent edits (Automerge / Yjs).
- OCR ingest: scanned CVs, certificates, patents → `inbox/`.
- Email adapter: parse application/offer confirmation emails.
- Calendar + email integration for automatic job timeline updates.
- Voice-based vault entry (transcribe interview notes).
- Obsidian community plugin: `resumeos-bridge` for tighter UI integration.
- `career_builder` automatic gap-detection nudges (weekly review).
- `resume_review` peer / mentor review workflow.
- Multi-language vault support (EN/ZH parallel frontmatter).
- Export to Europass CV, academic CV (IEEE/ACM formats).

---

## How this roadmap is updated

- Alpha items: tracked as tasks; move to "Done" only after CI passes and documentation aligns.
- Beta/1.0: feature-complete means docs, tests, and examples all match the feature.
- Future: ideas only. To promote an idea, open a PR with an ADR and a prototype.
