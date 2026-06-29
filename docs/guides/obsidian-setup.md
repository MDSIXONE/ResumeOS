# Obsidian Setup Guide

This guide explains how to open the ResumeOS vault in Obsidian and configure it for effective use.
It implements [ADR-0003](../decisions/ADR-0003-obsidian-vault-as-graph-database.md) (Obsidian vault
as a graph database).

---

## 1. Open the vault

1. Install [Obsidian](https://obsidian.md) (desktop or mobile).
2. Open Obsidian and select **Open folder as vault**.
3. Navigate to the `vault/` folder inside the ResumeOS repo and select it.

Obsidian treats `vault/` as the root. Everything inside it (career notes, jobs, inbox, canvas,
daily/periodic notes) is part of the graph.

---

## 2. Recommended community plugins

ResumeOS relies on several Obsidian community plugins for navigation, templating, and views.
Install them from **Settings → Community plugins → Browse**.

| Plugin | Why |
|---|---|
| **Dataview** | Query the vault like a database — job pipelines, career timelines, skill gaps. |
| **Templater** | Create entity notes from `templates/` with dynamic frontmatter. |
| **QuickAdd** | Fast entity creation via hotkeys / command palette (wraps Templater). |
| **Canvas** | Spatial career graph — connect projects, skills, roles visually. |
| **Excalidraw** | Free-form drawings embedded in notes (architecture diagrams, mind maps). |
| **Periodic Notes** | Daily, weekly, monthly review notes (see section 6 below). |

After installing:

- Enable **Templater** and point it at `templates/`:
  - Settings → Templater → Template folder location → `templates`.
  - Enable "Trigger Templater on new file creation".
- Enable **Dataview** and confirm it indexes the vault (check the Dataview summary in settings).
- Enable **QuickAdd** and create macros for common entity creation (project, job, skill, award).

---

## 3. Templater configuration

The repo's templates live in `templates/` at the repo root (outside the vault). To use them in
Obsidian:

1. Open **Settings → Templater**.
2. Set **Template folder location** to `../templates` (relative to `vault/`).
3. Enable **Trigger Templater on new file creation**.
4. (Optional) Set a hotkey for "Create new note from template".

The templates use Templater syntax (`<% ... %>`), not Jinja or Handlebars. The
`resumeos.config.yaml: templates.syntax: templater` field confirms this.

---

## 4. `skills/` vs `vault/career/skills/`

Two folders sound similar but are completely different:

| Folder | What it holds | Who uses it |
|---|---|---|
| `skills/` (repo root) | AI Skill plugins — independent, installable Claude Code / OpenCode Skills. | The agent runtime (Claude Code / OpenCode). |
| `vault/career/skills/` (inside the vault) | Markdown notes about *your* competencies (e.g. Python, PyTorch, embedded C). | You, Obsidian, and Skills that read the vault. |

Never mix them. `skills/` is code; `vault/career/skills/` is data.

---

## 5. Working with the vault

### Creating entities

Use Templater + QuickAdd to create entity notes from templates. Each note:

- Starts with YAML frontmatter (validated by `schemas/*.schema.json`).
- Has a body with prose sections (overview, details, reflections).
- Lives in the folder corresponding to its entity type (see `resumeos.config.yaml: vault.entities`).

### Linking entities

Use `[[wikilinks]]` in note bodies to create edges in the graph. For example, a project note might
link to the skills it used:

```markdown
This project used [[python]], [[pytorch]], and [[embedded-c]].
```

Dataview can query these links to build skill-usage dashboards.

### Tracking jobs

Use `templates/job-application.md` to create job application notes in `vault/jobs/`. The
`job_tracker` Skill reads these to build pipeline dashboards.

### The inbox

Drop raw material (PDFs, screenshots, links, notes) into `vault/inbox/`. Run `career_collector`
to stage them, then `career_builder` to enrich them into proper entities.

---

## 6. Daily and periodic notes

Use **Periodic Notes** to create daily, weekly, and monthly review notes.

- **Daily notes** (`vault/daily/`): capture what you worked on, what you learned, what to do
  tomorrow.
- **Weekly notes** (`vault/periodic/weekly/`): review the week, update project statuses, plan next
  week.
- **Monthly notes** (`vault/periodic/monthly/`): review the month, detect skill gaps, update the
  career graph.

`career_update` watches the vault and reacts to changes. If you update a project note, it marks
derived documents as stale and prompts you to regenerate.

Configure Periodic Notes:

- Settings → Periodic Notes → Daily notes → Format: `YYYY-MM-DD`, Folder: `daily`.
- Weekly notes → Format: `YYYY-[W]ww`, Folder: `periodic/weekly`.
- Monthly notes → Format: `YYYY-MM`, Folder: `periodic/monthly`.

---

## 7. Graph view tips

Obsidian's **Graph View** (Ctrl+G / Cmd+G) visualizes the vault as a graph. Tips:

- **Filter by folder:** use `path:career/projects` to see only project nodes.
- **Filter by tag:** use `tag:#robotics` to see only robotics-related nodes.
- **Local graph:** right-click a note → "Open local graph" to see its immediate neighbors.
- **Canvas:** open a `.canvas` file in `vault/canvas/` to see a spatial view of your career.

The graph grows with your career. Use it to detect clusters (e.g. "I have many projects in
robotics but few in ML"), gaps (e.g. "I have no notes on public speaking"), and connections
(e.g. "this skill appears in three projects").

---

## 8. Canvas files

Canvas files (`.canvas`) live in `vault/canvas/`. They are JSON files that Obsidian renders as
spatial graphs. Create a canvas for:

- Career timeline (projects → roles → skills).
- Job application pipeline (discovered → applied → interviewing → offer).
- Skill map (clusters of related competencies).

Canvas files are plain JSON; they can be generated by Skills (e.g. `career_builder` can emit a
canvas from the vault graph).

---

## 9. Excalidraw

Excalidraw notes (`.excalidraw.md`) embed free-form drawings in the vault. Use them for:

- Architecture diagrams (project → hardware → software → algorithms).
- Mind maps (skill clusters, career directions).
- Flowcharts (job application process, tailoring pipeline).

Excalidraw files are Markdown with embedded SVG; they are version-controlled and render in
Obsidian.

---

## 10. What NOT to do

- Do not edit `vault/.obsidian/workspace*` or `vault/.obsidian/cache` (git-ignored).
- Do not write derived documents (resumes, cover letters) into the vault — use `output/`.
- Do not hand-edit `vault/.library/` (machine-managed tailoring memory).
- Do not move `skills/` into the vault — they are code, not data.

---

## 11. Further reading

- [Skill authoring spec](skill-authoring-spec.md) — how to write a Skill plugin.
- [Plugin development guide](plugin-development.md) — the hook system, permissions, namespaces.
- [Vault guide](../../vault/README.md) — what the vault is, folder map, the one rule.
- [Schema extension guide](schema-extension.md) — how to add a new entity schema.
