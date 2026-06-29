# ResumeOS — CLI Specification

> **Scope:** Minimal, intuitive command surface that drives the skills declared in
> `skills/registry.yaml`. The CLI is a thin orchestrator; it holds no business logic.
> This document is authoritative for command names, flags, behavior, and exit codes.

See the parent track index: [`docs/ux/README.md`](./README.md).

---

## 1. Design principles

1. **Minimal surface.** One verb per intent. No hidden modes.
2. **Intuitive verbs.** Commands match the user's mental model: `import`, `process`, `update`,
   `build`, `tailor`, `review`, `interview`, `dashboard`, `inbox`, `jobs`.
3. **No complicated syntax.** Flags are optional and carry sensible defaults derived from
   `resumeos.config.yaml`.
4. **CLI drives Skills.** Every command dispatches one or more skills declared in
   `skills/registry.yaml`. The CLI does not reimplement skill logic.
5. **Idempotent.** Running a command twice produces the same result as running it once, except
   where the user must resolve an ambiguous duplicate (exit code 4).

The user's only invariants remain those in `docs/ux/README.md`: Knowledge Base is the SSOT,
`output/` is derived and regenerable, and the only required user gesture is "save into Inbox."

---

## 2. Command reference

### 2.1 Overview

| Command | Purpose | Skill(s) invoked | Reads | Writes |
|---------|---------|-------------------|-------|--------|
| `resume import [path]` | Ingest external material into `vault/inbox/` | `inbox_ingest`, `career_collector` | external file/dir/URL/repo, `vault/.library/cache/`, config | `vault/inbox/**`, `vault/assets/**`, `vault/.processing/**`, `vault/.library/cache/**`, `logs/imports/` |
| `resume process` | End-to-end pipeline for everything in `vault/inbox/` | `inbox_ingest` → `career_collector` → `career_builder` → `career_update` | `vault/inbox/**`, `vault/.library/cache/`, config | `vault/inbox/**` (root emptied), `vault/assets/**`, `vault/.processing/**`, `vault/career/**`, `logs/imports/` |
| `resume update` | Refresh derived/stale flags; incremental knowledge maintenance | `career_update` | `vault/career/**`, `vault/inbox/**`, config | `vault/career/**` (incremental fields) |
| `resume build` | Build a generic resume from the vault (no job target) | `resume_builder` | `vault/career/**`, config, templates | `output/` |
| `resume tailor <jd\|company>` | Run the checkpoint tailoring pipeline | `resume_tailoring`, then `cover_letter`, `interview` | `vault/career/**`, JD file or company name, config, vault library | `output/<job>/`, `vault/.library/cache/` |
| `resume review [path]` | Review a generated resume for provenance/hallucination | `resume_review` | target resume, `vault/career/**` | review report (stdout or file) |
| `resume interview <jd\|company>` | Generate interview prep | `interview` | `vault/career/**`, JD file or company name | `output/<job>/interview*` |
| `resume dashboard` | Open/print the career dashboard | (Dataview-backed note, no skill dispatch) | `vault/career/**`, `logs/imports/`, `vault/inbox/_errors/` | none (read-only render) |
| `resume inbox [--errors]` | Open `vault/inbox/` in the file explorer, or list errors | (filesystem only, no skill dispatch) | `vault/inbox/` | none (opens shell or prints list) |
| `resume jobs` | List/track job applications | `job_tracker` | `vault/career/jobs/**` (per config: `vault.entities.job`) | `vault/career/jobs/**` (when adding/updating) |

---

### 2.2 `resume import [path]`

Ingest external material (file, directory, URL, or GitHub repo URL) into `vault/inbox/`.
Invokes `inbox_ingest` (file lifecycle) then hands staged pointers to `career_collector`.

**Syntax:**

```text
resume import [path]
```

`path` may be a local file, a directory, an `http(s)://` URL, or a GitHub repo URL
(`https://github.com/<owner>/<repo>`). If omitted, the CLI imports everything currently
waiting in `vault/inbox/`.

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--category <name>` | string | auto-detected | Force category (`awards`, `projects`, `research`, `certificates`, `images`, `videos`, `documents`). |
| `--year <YYYY>` | integer | inferred from file | Force filing year. |
| `--no-dedup` | boolean | false | Skip duplicate detection (dangerous; prefer normal dedup prompt). |

**Examples:**

```text
resume import ./offer-letter.pdf
resume import https://github.com/octocat/my-project
resume import ~/Downloads/cert.png --category certificates
```

**Behavior:**

- `inbox_ingest` hashes, deduplicates against `vault/.library/cache/`, classifies by extension
  and content, OCRs/extracts as needed, moves the original into
  `vault/assets/<category>/<year>/<slug>-<short-hash>.<ext>`, and appends an entry in
  `logs/imports/`.
- On duplicate, prompts the user: `skip`, `replace`, `merge`, `new-version`. Exit 4 if the
  user declines.
- Emits a staged source pointer into `vault/inbox/` (a small `.md` note listing the asset
  path and extracted facts).
- `career_collector` consumes the staged pointer and builds an inbox note with provenance
  (`sources[]`) and `confidence: inferred` where applicable.
- If any file fails classification or extraction, it is moved to `vault/inbox/_errors/` with
  a stub note. Overall run exits 10 (partial success) if some files succeeded and others did
  not.

---

### 2.3 `resume process`

Process everything currently sitting in `vault/inbox/` end-to-end. This is the single
"do the work" command.

**Syntax:**

```text
resume process
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--stop-on-error` | boolean | false | Abort on the first failing file instead of continuing to the rest. |
| `--no-confirm` | boolean | false | Skip user confirmation prompts where safe. Never overrides anti-hallucination gaps (those always ask). |

**Examples:**

```text
resume process
resume process --no-confirm
```

**Behavior:**

Runs, in order:

1. `inbox_ingest` — hash → dedup → classify → extract → move to `vault/assets/<category>/<year>/` → append `logs/imports/`.
2. `career_collector` — staged pointers → inbox notes with `sources[]` + `confidence`.
3. `career_builder` — inbox notes → structured entities in `vault/career/**` per entity schema.
4. `career_update` — `onVaultChange` hook: refresh derived fields and stale flags in
   `vault/career/**`.

The root of `vault/inbox/` is empty on success. `_errors/` may retain failed-import stubs.
`vault/.processing/` is empty between runs (ADR-0011: transient).

Exit 0 on full success, 10 if any file errored but others succeeded, 4 if a duplicate requires
user intervention and the user chose to abort.

---

### 2.4 `resume update`

Refresh derived and stale flags. Use after manual edits to `vault/career/**` in Obsidian, or
periodically to keep the knowledge graph internally consistent.

**Syntax:**

```text
resume update
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--entity <id>` | string | all | Refresh a single entity (by `entity_id`). |
| `--full` | boolean | false | Re-derive all computed fields instead of only changed ones. |

**Examples:**

```text
resume update
resume update --entity proj_openllm-infra
```

**Behavior:**

- `career_update` scans `vault/career/**` for changes since the last known checkpoint,
  propagates derived fields, and marks downstream entities stale where upstream dependencies
  changed.
- Idempotent. Re-running produces no effect if nothing has changed.

---

### 2.5 `resume build`

Build a generic master resume from the vault. No job target — this is a baseline document,
not a tailored one.

**Syntax:**

```text
resume build
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--lang <zh\|en>` | string | `defaults.language` from config | Output language. |
| `--style <industry\|academic\|research>` | string | `defaults.resume_style` | Resume style. |
| `--length <one_page\|two_page>` | string | `defaults.resume_length` | Target length. |
| `--format <md\|docx\|latex\|jsonresume>` | string | `md` | Output format. Multiple formats: repeat the flag. |
| `--output <path>` | string | `output/master-resume` | Override output directory/file. |

**Examples:**

```text
resume build
resume build --lang en --format docx --format latex
```

**Behavior:**

- `resume_builder` reads `vault/career/**`, composes a master resume per flags, writes to
  `output/` (git-ignored).
- Never writes into the vault.
- All bullets cite `entity_id:field` so later `resume review` can verify provenance.

---

### 2.6 `resume tailor <jd|company>`

Run the checkpoint tailoring pipeline for a job description file or a company name. Surfaces
the configured checkpoints (`research`, `gap_analysis`, `assembly`) for review only when the
pipeline needs a decision; otherwise runs end-to-end.

**Syntax:**

```text
resume tailor <jd-path|company-name>
```

The argument is either a path to a JD file (`.md`, `.pdf`, `.docx`, or a URL) or a plain
company name (looked up via `browser` MCP when enabled, otherwise from the user's library).

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--skip-gate <name>` | string | none | Skip a specific checkpoint gate (`research`, `gap_analysis`, `assembly`). Use with care. |
| `--lang <zh\|en>` | string | `defaults.language` | Output language. |
| `--no-letter` | boolean | false | Skip the cover-letter step. |
| `--no-interview` | boolean | false | Skip the interview-prep step. |
| `--job-id <slug>` | string | derived from company/JD hash | Stable slug for the output directory. |

**Examples:**

```text
resume tailor ./jd-senior-engineer.md
resume tailor "ByteDance"
resume tailor ./jd.pdf --no-interview --job-id bytedance-sre-2026
```

**Behavior:**

1. `resume_tailoring` executes the phased pipeline: research → gap analysis → rank projects →
   assembly → generation. Checkpoint gates from `pipeline.tailoring.checkpoints` surface only
   when the pipeline needs a decision.
2. `cover_letter` generates a personalized cover letter grounded in confirmed vault facts.
3. `interview` generates interview prep (behavior/technical/project) for the same job.

Outputs are written to `output/<job-id>/` with sub-artifacts under
`output/<job-id>/artifacts/` (validated JSON per `pipeline.tailoring.artifacts: true`).
The vault library cache `vault/.library/cache/` is updated if
`pipeline.tailoring.self_improving: true`.

Every generated bullet must cite `entity_id:field`. Uncitable bullets block with exit 3.

---

### 2.7 `resume review [path]`

Review a generated resume for provenance and hallucination. Verifies that every bullet cites
an `entity_id:field` present in the vault.

**Syntax:**

```text
resume review [path]
```

`path` defaults to the most recently generated resume in `output/`.

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--strict` | boolean | false | Treat uncitable bullets as fatal (exit 3) instead of warnings. |
| `--format <text\|json\|md>` | string | `text` | Report format. |
| `--output <path>` | string | stdout | Write report to file instead of stdout. |

**Examples:**

```text
resume review
resume review output/bytedance-sre-2026/resume.md --strict
```

**Behavior:**

- `resume_review` loads the target resume, walks each bullet, looks up the citation in
  `vault/career/**`, and reports missing or stale citations.
- With `--strict`, any uncitable bullet produces exit code 3.

---

### 2.8 `resume interview <jd|company>`

Generate interview prep for a specific role.

**Syntax:**

```text
resume interview <jd-path|company-name>
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--type <behavior\|technical\|project\|all>` | string | `all` | Prep category. |
| `--lang <zh\|en>` | string | `defaults.language` | Output language. |
| `--job-id <slug>` | string | derived from argument | Stable slug for the output directory. |

**Examples:**

```text
resume interview ./jd-senior-engineer.md
resume interview "Alibaba" --type technical
```

**Behavior:**

- `interview` generates behavior/technical/project prep, STAR answers, follow-ups, weakness
  analysis, and (optionally) a mock-interview script.
- Outputs go to `output/<job-id>/interview*`.
- All content must cite vault facts; uncitable items block with exit 3.

---

### 2.9 `resume dashboard`

Open or print the career dashboard. The dashboard is a Dataview-backed note that surfaces
proactive nudges: inbox status (`vault/inbox/` root), stale flags, error list
(`vault/inbox/_errors/`), job-tracker state, and knowledge-base gaps.

**Syntax:**

```text
resume dashboard
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--open` | boolean | true | Open the dashboard note in Obsidian (via `obsidian://` URI). |
| `--print` | boolean | false | Print the dashboard to stdout instead of opening Obsidian. |
| `--section <name>` | string | all | Render only one section (`inbox`, `stale`, `errors`, `jobs`, `nudges`). |

**Examples:**

```text
resume dashboard
resume dashboard --print --section nudges
```

**Behavior:**

- No skill is dispatched. The CLI composes a read-only render from `vault/career/**`,
  `logs/imports/`, `vault/inbox/_errors/`, and `vault/career/jobs/**`.
- Nudges follow the conversation design in
  [`docs/ux/conversation-design.md`](./conversation-design.md): proactive, not interruptive,
  one question at a time when actionable.

---

### 2.10 `resume inbox [--errors]`

Bridge the user's "one folder" mental model to the physical layout. Opens `vault/inbox/` in
the OS file explorer, or lists errors.

**Syntax:**

```text
resume inbox
resume inbox --errors
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--errors` | boolean | false | List error stubs in `vault/inbox/_errors/` instead of opening the folder. |
| `--list` | boolean | false | List current contents of `vault/inbox/` root (no opener). |

**Examples:**

```text
resume inbox
resume inbox --errors
resume inbox --list
```

**Behavior:**

- No skill is dispatched. The CLI shells out to the OS file manager (Windows Explorer / macOS
  Finder / `xdg-open`) pointing at the physical `vault/inbox/` directory.
- `--errors` prints a compact list: stub path, short error reason, original filename. Exit 0
  if no errors, 1 if the error list is non-empty (so it can be chained in scripts).

---

### 2.11 `resume jobs`

List or update tracked job applications.

**Syntax:**

```text
resume jobs
resume jobs add <company> <role>
resume jobs update <job-id> --status <status>
```

**Flags:**

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--status <s>` | string | — | Filter (list) or set (update). Values: `applied`, `screening`, `interview`, `offer`, `rejected`, `withdrawn`. |
| `--format <table\|json>` | string | `table` | List format. |

**Examples:**

```text
resume jobs
resume jobs --status interview
resume jobs add ByteDance "Senior SRE"
resume jobs update bytedance-sre-2026 --status offer
```

**Behavior:**

- `job_tracker` reads and writes `vault/career/jobs/**` (the entity root configured as
  `vault.entities.job`).
- Adding a job creates a frontmatter-validated entity note. Updating preserves the version
  history of status changes (incremental, never rebuild — see UX README §5.8).

---

## 3. Watch mode (V2 roadmap)

Watch mode is explicitly **out of scope for V1**. It is recorded here for completeness and to
prevent scope creep.

- **V1 (now).** Manual invocation: the user runs `resume process` whenever files accumulate
  in `vault/inbox/`.
- **V2 (future).** `resume watch` — a daemon that monitors `vault/inbox/` for filesystem
  events and auto-processes new files, moving completed ones into `vault/assets/`. Off by
  default; explicitly opted in via config or flag.

Proposed V2 flags (not implemented):

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--interval <seconds>` | integer | 5 | Poll interval when filesystem events are unavailable. |
| `--once` | boolean | false | Process currently-waiting files and exit (one-shot). |
| `--no-daemon` | boolean | false | Run in the foreground instead of detaching. |

Watch mode requires a long-running process. It is not in V1. The full lifecycle the watcher
would automate is documented in
[`docs/ux/inbox-workflow.md`](./inbox-workflow.md).

---

## 4. Global flags

These flags apply to every command. They may be placed before or after the verb.

| Flag | Type | Overrides | Default | Description |
|------|------|-----------|---------|-------------|
| `--vault <path>` | path | `vault.path` | repo-relative `vault` | Override the physical vault location. |
| `--lang <zh\|en>` | enum | `defaults.language` | `zh` | Override the default output language. |
| `--yes` | boolean | — | false | Skip confirmation prompts where safe. **Never** suppresses anti-hallucination gap prompts — those always ask (UX README §5.3). |
| `--dry-run` | boolean | — | false | Preview actions without writing. Skills receive a read-only hint and must not mutate the vault. |
| `--verbose` | boolean | — | false | Print detailed progress (skill-by-skill trace, file-by-file status). |
| `--quiet` | boolean | — | false | Suppress all non-error output. Implied by CI environments. |
| `--config <path>` | path | — | `./resumeos.config.yaml` | Use an alternate configuration file. |

Precedence: flag > environment variable (`RESUMEOS_LANG`, `RESUMEOS_VAULT`) > `resumeos.config.yaml` > built-in default.

---

## 5. Exit codes

| Code | Meaning | When |
|------|---------|------|
| `0` | Success | All steps completed cleanly. |
| `1` | General error | Unhandled exception, missing skill, invalid configuration. |
| `2` | Validation error | Frontmatter or schema violation discovered during processing. |
| `3` | Anti-hallucination block | A generated bullet could not be cited against `entity_id:field` in the vault. The user must resolve the gap. |
| `4` | Duplicate — user decision required | A duplicate file was detected and the user declined to pick `skip`/`replace`/`merge`/`new-version`. |
| `10` | Partial success | Multiple inputs: some succeeded, some failed. Individual file outcomes are recorded in `logs/imports/`. |

Scripts can branch on exit code. CI pipelines should treat codes 2, 3, and 4 as failures;
code 10 as a warning-to-failure (configurable); and code 0 as pass.

---

## 6. Developer documentation — the `inbox_ingest` skill manifest

The keystone introduces a new Tier-1 Skill, `inbox_ingest` (ADR-0011 §10). It owns the
file-level lifecycle: hash → dedup → classify → extract → move to Assets → log → emit staged
pointers.

> **Implementation status.** This manifest is a **recommendation for Phase 3 implementation**.
> It is specified here so the UX track and the skills track agree on the contract. No code is
> written in this track.

**Registration (to be appended to `skills/registry.yaml`):**

```yaml
  - name: inbox_ingest
    version: 0.1.0
    path: skills/inbox_ingest
    enabled: true
    depends_on: ["schema@1.0.0"]
    description: File-level lifecycle for imported material — hash, dedup, classify, extract, move to Assets, log, emit staged pointers.
```

**Configuration change (to be added to `resumeos.config.yaml`):**

- `skills.enabled_default` gains `inbox_ingest` at the top of the list (it is the entry
  point of the ingest pipeline).
- `vault.folders` gains `processing: .processing`, `errors: inbox/_errors`, and
  `assets: assets` entries so the skill can resolve physical paths from config.

**Plugin manifest (`skills/inbox_ingest/plugin.json`):**

```json
{
  "$schema": "../../schemas/plugin-manifest.schema.json",
  "name": "inbox_ingest",
  "version": "0.1.0",
  "description": "File-level lifecycle for imported material: hash, dedup, classify, extract (OCR/parse), move to vault/assets, append logs/imports, emit staged source pointers into vault/inbox.",
  "type": "skill",
  "license": "MIT",
  "depends_on": ["schema@1.0.0"],
  "hooks": ["onVaultChange"],
  "mcp_tools": [
    "filesystem:read",
    "filesystem:move",
    "github:get_commits",
    "ocr:extract"
  ],
  "permissions": {
    "read": [
      "vault/inbox/**",
      "vault/.library/cache/**"
    ],
    "write": [
      "vault/inbox/**",
      "vault/assets/**",
      "vault/.processing/**",
      "vault/.library/cache/**",
      "logs/**"
    ],
    "deny": [
      "vault/career/**",
      "output/**"
    ]
  }
}
```

**Notes on the manifest:**

- `hooks: ["onVaultChange"]` lets the skill react to manual vault changes when the user
  drops files directly (watch-mode V2 integration point).
- `mcp_tools` lists `ocr:extract` as a future MCP adapter (per ADR-0008: MCP adapters are
  declared at the skill level; the actual OCR server is discovered at runtime from
  `resumeos.config.yaml: mcp.servers`).
- The `deny` list enforces the invariant from the keystone: `inbox_ingest` never writes into
  `vault/career/**` (that is `career_builder`'s job) or `output/**` (that is a downstream
  tailoring concern).

---

## 7. Configuration alignment

The CLI never hardcodes logic. Every command reads `resumeos.config.yaml` for:

- `vault.path`, `vault.entities.*`, `vault.folders.*` — physical path resolution.
- `skills.enabled_default` and `skills.registry` — skill discovery.
- `defaults.language`, `defaults.resume_style`, `defaults.resume_length` — fallback flag
  values.
- `pipeline.tailoring.checkpoints` — which gates `resume tailor` surfaces.
- `schemas.path`, `schemas.strict` — whether frontmatter validation is fatal.
- `mcp.servers.*` — which MCP tools are available at runtime.

The only config the CLI writes is during its own per-run state (e.g. last-run checkpoint
timestamp for `career_update`), which belongs to the skill, not the CLI.

Environment variables (`RESUMEOS_VAULT`, `RESUMEOS_LANG`, `RESUMEOS_QUIET`, `RESUMEOS_YES`)
override config for scripting; CLI flags override environment variables.

---

## 8. Cross-references

- [`docs/ux/inbox-workflow.md`](./inbox-workflow.md) — the ingest lifecycle the CLI drives,
  including the file-lifecycle state machine and daily-workflow sequence diagrams.
- [`docs/ux/data-lifecycle.md`](./data-lifecycle.md) — import-log JSONL schema, dedup
  strategy, asset-management strategy, incremental update semantics.
- [`docs/ux/conversation-design.md`](./conversation-design.md) — conversation principles
  behind `resume dashboard` nudges and the one-question-at-a-time prompt discipline.
- [`docs/guides/plugin-development.md`](../guides/plugin-development.md) — how to author new
  skills (relevant when extending the CLI with new verbs).
- [`docs/decisions/ADR-0011-inbox-asset-lifecycle-directories.md`](../decisions/ADR-0011-inbox-asset-lifecycle-directories.md) —
  physical placement of the eight lifecycle directories that the CLI surfaces.
