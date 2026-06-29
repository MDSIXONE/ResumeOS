# Contributing to ResumeOS

Thank you for contributing. ResumeOS is a small, opinionated project; the rules below exist to keep
that opinion coherent. Please read them in full before opening a pull request.

---

## Project layout

```
ResumeOS/
├── skills/             # AI Skill plugins (each independently installable)
│   ├── <skill-name>/   # SKILL.md + plugin.json + README.md + prompts/
│   └── registry.yaml   # Authoritative list + version pins
├── vault/              # The Obsidian vault (single source of truth)
├── templates/          # Obsidian Templater templates for every entity type
├── prompts/            # Modular, composable prompt fragments consumed by Skills
├── schemas/            # JSON Schema for every entity, manifest, and artifact
├── docs/
│   ├── architecture/   # C4 + data-flow + plugin model
│   ├── decisions/      # Architecture Decision Records (ADR-0000..0010)
│   └── guides/         # Skill authoring, plugin dev, schema extension, MCP, Obsidian setup
├── examples/           # A complete example vault + derived outputs
├── tests/              # Schema-validation tests + Skill behavior contracts
├── scripts/            # Standalone validator + supporting tooling
├── .github/workflows/  # CI
├── resumeos.config.yaml
├── plugin.json         # Root Claude-Code plugin manifest (the bundle)
└── README.md  CONTRIBUTING.md  ROADMAP.md  LICENSE
```

Two naming distinctions that matter:

- `skills/` holds AI Skill *plugins*.
- `vault/career/skills/` holds notes about *your* competencies.

They are different things; see [the Obsidian setup guide](docs/guides/obsidian-setup.md).

---

## Dev workflow

1. Fork the repo and create a feature branch from `main`.
2. Keep commits atomic: one logical change per commit.
3. Run the validator locally before pushing:
   ```
   pip install -r scripts/requirements.txt
   python scripts/validate-vault.py --vault examples/vault
   pytest
   ```
4. Open a pull request. Fill in the PR checklist below.

---

## How to add a Skill

Follow the [Skill authoring spec](docs/guides/skill-authoring-spec.md). Summary:

1. Create `skills/<skill-name>/` containing exactly: `SKILL.md`, `plugin.json`, `README.md`,
   and a `prompts/` folder.
2. The manifest (`plugin.json`) must validate against
   [`schemas/plugin-manifest.schema.json`](schemas/plugin-manifest.schema.json).
3. Add a behavior contract at `tests/<skill-name>.contract.md` describing happy, anti-hallucination,
   and (if applicable) checkpoint paths.
4. Register the Skill in [`skills/registry.yaml`](skills/registry.yaml).
5. Read the [Plugin development guide](docs/guides/plugin-development.md) for the hook system,
   permissions model, namespace isolation, and `depends_on`.

---

## How to extend a schema

Follow the [Schema extension guide](docs/guides/schema-extension.md). Summary:

1. Use JSON Schema draft 2020-12, `additionalProperties: false`, required `sources[]` and
   `confidence`.
2. Version the `$id` (`/schemas/<major>.<minor>.<patch>/<entity>.schema.json`).
3. Breaking changes bump the major version and ship a migration note under `schemas/migrations/`.
4. Templates must match schema required keys exactly.
5. CI validates every `examples/vault/**/*.md` frontmatter against its schema.

---

## How to write an ADR

Follow the [ADR template](docs/decisions/adr-template.md). Every major design decision gets an ADR.
Statuses: Proposed, Accepted, Rejected, Deprecated, Superseded. Accepted ADRs are immutable;
supersession creates a new ADR that links back.

---

## What NOT to commit

- Derived documents. Edit the vault; regenerate. The `output/` tree is git-ignored.
- Obsidian workspace / cache (`vault/.obsidian/workspace*`, `vault/.obsidian/cache`).
- Local secrets (`.env*`, `secrets/`).
- Machine-managed tailoring memory (`vault/.library/` content).

---

## PR checklist

- [ ] Every new/changed vault entity validates against its schema in `schemas/`.
- [ ] Every new/changed `plugin.json` validates against `plugin-manifest.schema.json`.
- [ ] Every new/changed output artifact validates against `schemas/artifacts/*.schema.json`.
- [ ] Vault frontmatter contains no derived data — everything is canonical.
- [ ] No new prompt prose lives inline in an `SKILL.md` body; prompts are in `prompts/*.md`.
- [ ] New Skills have a `tests/<skill>.contract.md`.
- [ ] `python scripts/validate-vault.py --vault examples/vault` passes locally.
- [ ] `pytest` passes locally (or tests were added for a new feature).
- [ ] ADRs are updated if this PR introduces a new design decision.
- [ ] Documentation (`README.md`, relevant guide) is updated if it references the change.

---

## Code of conduct

Be concise, be kind, and critique the work rather than the worker. We enforce one hard rule —
**anti-hallucination** ([ADR-0007](docs/decisions/ADR-0007-anti-hallucination-contract.md)) —
because it protects the user. Argue about everything else.

ResumeOS is a private, local-first project. Contributors are expected to respect the user's
ownership of their data: no telemetry, no silent cloud round-trips, no feature that moves the
source of truth out of the vault. If you are unsure whether a change respects that, open an issue
first.
