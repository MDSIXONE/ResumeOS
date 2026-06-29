# ResumeOS Vault

This is the single source of truth for your career data. Everything outside this directory
(resumes, cover letters, interview packs, dashboards) is **derived** from files living here
and is regenerable on demand.

Read [ADR-0001](../docs/decisions/ADR-0001-knowledge-base-as-single-source-of-truth.md) for the
strategy; read [ADR-0003](../docs/decisions/ADR-0003-obsidian-vault-as-graph-database.md) for the
graph-database model.

---

## The One Rule

**Never edit derived files.** Update the vault, then regenerate. If a resume contains a typo,
fix the vault note that produced that bullet; never edit `output/`.

This is the rule that keeps the system honest. Derived documents can be regenerated from any
state of the vault; they are never canonical.

---

## Folder map

```
vault/
├── career/
│   ├── projects/        # Technical projects (schema: project.schema.json)
│   ├── research/        # Papers, preprints, thesis chapters (research.schema.json)
│   ├── competitions/    # Competition entries and placements (competition.schema.json)
│   ├── internships/     # Internship experiences (internship.schema.json)
│   ├── opensource/      # Open-source contributions (opensource.schema.json)
│   ├── awards/          # Awards and honours (award.schema.json)
│   ├── education/       # Education entries (education.schema.json)
│   └── skills/          # Your competencies — NOT the AI Skill plugins (skill.schema.json)
├── jobs/                # Job application notes (job.schema.json)
├── inbox/               # Raw imports awaiting career_collector / career_builder
├── canvas/              # Career-graph .canvas files (spatial views)
├── daily/               # Daily review notes
├── periodic/            # Weekly / monthly / yearly review notes
└── .library/            # Tailoring memory (machine-managed; do not hand-edit)
```

Each folder has a README describing what notes belong inside, plus the schema and template to use.

Entity type is inferred from the containing folder and mapped by
[`resumeos.config.yaml`](../resumeos.config.yaml) under `vault.entities`:

```yaml
vault:
  entities:
    project:     career/projects
    research:    career/research
    competition: career/competitions
    internship:  career/internships
    opensource:  career/opensource
    award:       career/awards
    education:   career/education
    skill:       career/skills
    job:         jobs
```

---

## Creating entities from templates

Every entity type has a matching template under `templates/` at repo root:

```
templates/
├── project.md
├── research.md
├── competition.md
├── internship.md
├── opensource.md
├── award.md
├── education.md
├── skill.md
└── job-application.md
```

Each template has YAML frontmatter that validates against the entity's schema in `schemas/`.
To create a new entity:

1. Open Obsidian on this vault.
2. Use QuickAdd (or Templater's "Create note from template") to create a new note from the
   relevant template.
3. Fill in the required frontmatter fields (those listed in the schema's `required` array).
4. Fill in the body with prose. The frontmatter is the data; the body is the narrative.

---

## Confidence

Every entity carries a `confidence` field: `confirmed | inferred | missing`.

- **`confirmed`** — facts you can defend in an interview, backed by a source. Only `confirmed`
  facts flow into derived documents.
- **`inferred`** — facts that came from a source but have not yet been reviewed (typical for
  freshly ingested inbox notes). `career_builder` will ask you to promote these to `confirmed`.
- **`missing`** — facts that are absent but ought to be present. Skills surface these as gaps.

See [ADR-0007](../docs/decisions/ADR-0007-anti-hallucination-contract.md).

---

## Sources

Every entity carries a `sources[]` array (provenance). Each source has a `kind` (e.g. `pdf`,
`github`, `paper`, `manual`) and a `ref` (path, URL, or identifier).

`career_collector` sets these when it ingests raw material. `career_builder` never removes them.
Skills that generate derived documents must trace every bullet back to a specific
`entity_id:field` citation.

A derived resume with an uncitable bullet is a build failure — see the provenance test
(`tests/test_provenance.py`).

---

## What you should NOT put in the vault

- Derived documents (resumes, cover letters, dashboards). These go to `output/`, which is
  git-ignored.
- Obsidian workspace state (`vault/.obsidian/workspace*`) or plugin data. Also git-ignored.
- Machine-managed tailoring memory (`vault/.library/`). This is managed by `resume_tailoring`
  and `career_update`.
- Local secrets (tokens, keys). Use `.env*` (git-ignored).

---

## Further reading

- [Skill authoring spec](../docs/guides/skill-authoring-spec.md)
- [Plugin development guide](../docs/guides/plugin-development.md)
- [Schema extension guide](../docs/guides/schema-extension.md)
- [MCP integration guide](../docs/guides/mcp-integration.md)
- [Obsidian setup guide](../docs/guides/obsidian-setup.md)
- [Testing strategy](../tests/README.md)
- [Contributing](../CONTRIBUTING.md)
- [Roadmap](../ROADMAP.md)
