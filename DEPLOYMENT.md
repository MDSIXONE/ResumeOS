# Deployment Guide

Step-by-step setup for ResumeOS — from clone to running demos.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.9 or later | Check with `python --version` |
| pip | any recent version | Comes with Python |
| Git | any recent version | For cloning the repository |
| Obsidian | (optional) latest | For viewing and editing the vault |
| Claude Code / OpenCode | (optional) latest | For running Skills as AI agents |

---

## Quick install

Three commands to get from zero to running:

```bash
git clone https://github.com/MDSIXONE/ResumeOS.git
cd ResumeOS
pip install -r scripts/requirements.txt
```

Verify the installation:

```bash
pytest --tb=short -q
```

Expected output: **407 passed**.

---

## Run the demos

All five demos are self-contained. They use local fixtures and the `DummyLLMProvider` — no API keys, no network access, no LLM provider setup needed.

### Sprint 1 — Runtime smoke test

```bash
python scripts/demo_sprint1.py
```

Tests the core runtime: Event Bus pub/sub, Knowledge Index search, and conversation Memory. Confirms the foundation works.

### Sprint 2.5 — Importer

```bash
python scripts/demo_sprint25.py
```

Parses a README file into an Artifact using the 5-layer importer pipeline (Detector, Extractor, Normalizer). Zero AI calls — pure file parsing.

### Sprint 3 — Inbox orchestrator

```bash
python scripts/demo_sprint3.py
```

Batch-imports 3 files through the inbox. Produces Artifacts, emits Events, generates Import Receipts, archives originals, and supports deterministic Replay.

### Sprint 4 — Career builder

```bash
python scripts/demo_sprint4.py
```

Runs the full Builder pipeline: Artifact to Knowledge via Planner, Retriever, LLM (DummyLLM), Validator, and Merger. Demonstrates Provenance tracking and Conflict detection.

### Sprint 5 — Resume assembly

```bash
python scripts/demo_sprint5.py
```

End-to-end: reads a Job Description, selects and ranks Knowledge entries, builds a ResumeIR, and renders output in three formats — Markdown, JSON Resume, and HTML.

---

## Open in Obsidian (optional)

The knowledge base lives in `vault/` and is a standard Obsidian vault.

1. Open Obsidian.
2. Click **Open folder as vault**.
3. Select the `vault/` directory inside your ResumeOS clone.
4. Install the recommended community plugins:
   - **Dataview** — query and dashboard views across your career notes
   - **Templater** — use the templates in `templates/` to create new entities
   - **QuickAdd** — fast entity creation flows
   - **Canvas** — career-graph visualization
   - **Excalidraw** — visual career mapping
   - **Periodic Notes** — daily and periodic reviews

See [`docs/guides/obsidian-setup.md`](docs/guides/obsidian-setup.md) for detailed configuration.

---

## Install Skills in Claude Code / OpenCode (optional)

The Skills in `skills/` are designed for AI coding agents. To use them:

1. Open your project in Claude Code or OpenCode.
2. Point the agent at the `skills/` directory, or symlink individual skill folders into your agent's skill directory (e.g., `.claude/skills/`).
3. The root `plugin.json` registers the full bundle. Individual skills each have their own `plugin.json` for standalone installation.

See [`docs/guides/plugin-development.md`](docs/guides/plugin-development.md) for the hook system, permissions model, and namespace isolation.

---

## Run the test suite

```bash
pytest
```

Expected result: **407 tests passed, 0 failed.**

The test suite covers:

| Category | Location | What it tests |
|---|---|---|
| Unit tests | `tests/unit/` | Every runtime module in isolation |
| Integration tests | `tests/integration/` | End-to-end pipeline behavior |
| Golden-file tests | `tests/golden/` | Regression against known-good outputs |
| Schema validation | `tests/test_schema_validation.py` | All vault frontmatter against JSON Schemas |
| Provenance | `tests/test_provenance.py` | KnowledgeObject provenance tracking |
| Contracts | `tests/contracts/` | Skill behavior contracts |

---

## Troubleshooting

### Python version too old

ResumeOS requires Python 3.9 or later. If you see syntax errors (especially with `dict` type hints or `match` statements), check your version:

```bash
python --version
```

On some systems, `python3` is the correct command. The demos and tests use `python` by default.

### Missing dependencies

If you see `ModuleNotFoundError`, install the dependencies:

```bash
pip install -r scripts/requirements.txt
```

Key dependencies: `pytest`, `jsonschema`, `PyYAML`, `pypdf`, `python-docx`, `Pillow`.

### CRLF warnings on Windows

Git may warn about line endings when cloning:

```
warning: LF will be replaced by CRLF
```

This is harmless. To suppress it:

```bash
git config --global core.autocrlf true
```

### Tests fail on first run

If a few tests fail immediately after clone, try:

```bash
pip install --upgrade pip
pip install -r scripts/requirements.txt --force-reinstall
pytest --tb=short -q
```

If failures persist, check that you are on the `main` branch and up to date.

---

## Next steps

| Goal | Where to look |
|---|---|
| Understand the architecture | [`docs/architecture/README.md`](docs/architecture/README.md) |
| Read the design decisions | [`docs/decisions/`](docs/decisions/) (ADR-0000 through ADR-0020) |
| Build your own Skill | [`docs/guides/skill-authoring-spec.md`](docs/guides/skill-authoring-spec.md) |
| Extend entity schemas | [`docs/guides/schema-extension.md`](docs/guides/schema-extension.md) |
| Connect external tools | [`docs/guides/mcp-integration.md`](docs/guides/mcp-integration.md) |
| Contribute to the project | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| See what is planned | [`ROADMAP.md`](ROADMAP.md) |
