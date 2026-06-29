# ADR-0011: Inbox, Asset, and Lifecycle Directory Placement

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS lead, UX track
- **Supersedes:** none
- **Superseded by:** none

## Context

The Phase 2 UX specification introduces an Inbox-first interaction model with a full file
lifecycle:

```text
Inbox → Processing → Knowledge Extraction → User Confirmation →
Knowledge Base Update → Asset Storage → Import Log → Inbox Cleaned
```

The user-facing specification names eight logical directories:

```text
Inbox/  Processing/  Error/  Assets/  Career/  Outputs/  Cache/  Logs/
```

These must be placed physically **without redesigning the Phase 1 architecture**. The
constraints from already-Accepted ADRs are firm:

- **ADR-0001** — `vault/` is the single source of truth (markdown knowledge); `output/` is
  derived, git-ignored, and never hand-edited. One-way flow vault → output.
- **ADR-0003** — the Obsidian vault is a graph database; entity folders live under
  `vault/career/**`. Users should rarely leave Obsidian.
- **ADR-0010** — content (`vault/`) and derived (`output/`) trees are physically separated.
  `output/` is git-ignored. `examples/` is the only committed "derived-looking" tree.

Two forces are in tension:

1. **Obsidian presence.** The user's one folder (`Inbox/`) and their assets must be visible
   inside the Obsidian vault so the user "rarely leaves Obsidian" (ADR-0003). Anything outside
   `vault/` is invisible to Obsidian.
2. **Git hygiene.** Binary assets (PDF, DOCX, images, video) and transient processing data
   must not bloat the git repo. ADR-0001/0010 already git-ignore `output/`.

A third force: the Phase 1 config (`resumeos.config.yaml`) already declares
`vault.folders.inbox: inbox` and `vault.entities.*` under `career/`, and `career_collector`
already writes to `vault/inbox/**`. The new directories must extend, not contradict, these.

## Decision

The eight logical lifecycle directories map to physical paths as follows. Logical names are
the user-facing vocabulary; physical paths are what exists on disk.

| Logical dir | Physical path | Git | Obsidian-visible | Owner skill |
|-------------|---------------|-----|------------------|-------------|
| `Inbox/` | `vault/inbox/` | md committed; binaries git-ignored | yes | `inbox_ingest` (new), `career_collector` |
| `Processing/` | `vault/.processing/` | git-ignored | no (dotfolder) | `inbox_ingest` |
| `Error/` | `vault/inbox/_errors/` | committed (small error stubs) | yes (underscore-sorted last) | `inbox_ingest` |
| `Assets/` | `vault/assets/` | git-ignored (binaries) | yes (Obsidian attachments) | `inbox_ingest` |
| `Career/` | `vault/career/` | committed | yes | `career_builder`, `career_update` |
| `Outputs/` | `output/` | git-ignored | no (outside vault) | `resume_builder`, `resume_tailoring`, `cover_letter`, `interview` |
| `Cache/` | `vault/.library/cache/` | git-ignored | no | `inbox_ingest`, `resume_tailoring` (library) |
| `Logs/` | `logs/` (repo root) | committed (audit trail) | via Dataview dashboard note | `inbox_ingest` |

### Concrete rules

1. **Inbox is the only folder the user manages.** `vault/inbox/` is the drop zone. Raw
   binaries dropped there are git-ignored (matched by extension); staged `.md` notes produced
   by ingestion are committed. After successful processing the root of `vault/inbox/` is empty;
   only `_errors/` may retain failed-import stubs.

2. **Processing is hidden and transient.** `vault/.processing/` is a dotfolder so Obsidian
   ignores it. It holds in-flight work (extracted text, OCR output, intermediate JSON). It is
   git-ignored. A successful run leaves it empty; a crashed run leaves partial state that the
   next `resume process` command cleans up before restarting.

3. **Errors stay visible but sorted away.** Failed imports move to `vault/inbox/_errors/`
   with an error-stub note explaining why and how to retry. The underscore prefix sorts it
   below real inbox items in Obsidian. The CLI `resume inbox --errors` and a dashboard widget
   surface them. Errors are not "successful processing," so keeping them does not violate
   "Inbox becomes empty after success."

4. **Assets live in the vault as Obsidian attachments, git-ignored.** `vault/assets/<category>/<year>/`
   stores original files permanently, organized by detected category and year. Binary
   extensions are git-ignored so the repo stays lean; the markdown knowledge that *references*
   them is the committed SSOT. Category subfolders: `awards/`, `projects/`, `research/`,
   `certificates/`, `images/`, `videos/`, `documents/`.

5. **Career is unchanged.** `vault/career/**` remains the SSOT knowledge graph per ADR-0001/0003.
   Entity subfolders are those already declared in `resumeos.config.yaml: vault.entities`.

6. **Outputs is unchanged.** `output/` remains the derived, git-ignored tree per ADR-0001/0010.
   Resumes, cover letters, interview packs, dashboards go here.

7. **Cache is hidden and transient.** `vault/.library/cache/` extends the existing
   `vault/.library/` (tailoring library from ADR-0006) with ingestion cache (OCR cache, parsed
   text cache, hash index). Git-ignored.

8. **Logs are a top-level committed audit trail.** `logs/imports/` stores one JSONL file per
   import run plus a rolled `logs/imports.jsonl` index. Logs are committed because they are
   historical audit data, not regenerable. A Dataview dashboard note
   (`vault/career/_import-log.md`) renders recent imports inside Obsidian so the user can audit
   without leaving the vault.

9. **Original files are never deleted.** The ingestion pipeline *moves* (not copies) originals
   from `vault/inbox/` to `vault/assets/<category>/<year>/`. The SSOT markdown references the
   asset path; the binary is the immutable evidence of provenance.

10. **A new plugin `inbox_ingest` owns the file lifecycle.** To keep `career_collector`
    focused on note-building (its existing role), a new Tier-1 Skill `inbox_ingest` handles
    file-level lifecycle: hash → dedup → classify → OCR/extract → move to Assets → write import
    log → emit a staged source pointer. `career_collector` then builds inbox notes from the
    staged pointers. This respects ADR-0004 (new skills extend without modifying core) and
    ADR-0005 (skill structure). `inbox_ingest` is registered in `skills/registry.yaml` and
    added to `resumeos.config.yaml: skills.enabled_default`. See the UX spec's developer
    documentation for its manifest.

## Consequences

- **Positive:** The user gets a single drop folder (`vault/inbox/`) that is Obsidian-visible,
  while git stays lean (binaries + transient data ignored). Existing ADRs are respected — this
  is an extension, not a redesign. Audit logs are committed and queryable. The new
  `inbox_ingest` skill keeps `career_collector` single-responsibility.
- **Negative:** Two ingestion skills (`inbox_ingest` + `career_collector`) instead of one —
  more moving parts. `vault/assets/` binaries are not in git, so a fresh clone lacks originals
  (acceptable for a personal career OS; assets are backed up out-of-band). `logs/` grows
  indefinitely and needs rotation.
- **Neutral:** The logical-to-physical mapping is a small cognitive load for contributors; the
  table above is the canonical reference. Obsidian attachment settings must point at
  `vault/assets/` (documented in `docs/guides/obsidian-setup.md`).

## Alternatives considered

- **Inbox at repo root (`inbox/` top-level).** Rejected: outside the Obsidian vault, the user
  could not see or drag into it from Obsidian, violating ADR-0003's "rarely leave Obsidian."
- **Assets outside the vault (`assets/` top-level).** Rejected: Obsidian could not render
  certificate/award images inline in notes, breaking the visual knowledge graph. Keeping them
  in `vault/assets/` (git-ignored) preserves Obsidian UX without bloating git.
- **Errors as a top-level `error/` dir.** Rejected: errors are inbox items the user must act
  on; hiding them outside the vault would make them invisible in Obsidian. `vault/inbox/_errors/`
  keeps them in the user's field of view while sorting them last.
- **Logs inside `vault/.library/logs/`.** Rejected: dotfolders are hidden in Obsidian and the
  logs are audit data worth committing visibly. Top-level `logs/` + a Dataview dashboard note
  gives both auditability and Obsidian presence.
- **Expand `career_collector` to own the file lifecycle.** Rejected: it would merge
  file-level lifecycle with note-level extraction, violating the single-responsibility plugin
  model (ADR-0004) and making `career_collector` harder to replace independently. A new
  `inbox_ingest` skill is cleaner and more ecosystem-friendly.
