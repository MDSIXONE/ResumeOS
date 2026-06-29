# AI Agent Guide — ResumeOS

> This document is written FOR AI agents (Claude, GPT, Cursor, Copilot, etc).
> If you are an AI that just cloned or opened this repository, read this first.
> Your job: help the human user understand and run ResumeOS.

---

## Who you are talking to

The human who asked you to clone this repo is likely a developer, researcher, or
student who wants a long-term career knowledge system — not a one-off resume
generator. They may not have read the full README. Your job is to get them from
zero to "oh, I get it, this is cool" in under 10 minutes.

Speak in their language. If they talk to you in Chinese, respond in Chinese. If
English, respond in English. Do not dump the whole README at them — walk them
through it step by step.

---

## What ResumeOS is (30-second explanation for the human)

Tell the human this in your own words:

> ResumeOS is not a resume builder. It is a Career Knowledge Operating System.
> You maintain ONE knowledge base (an Obsidian vault of Markdown files) that
> captures your entire career — every project, skill, award, research, job
> application. Everything else — resume, cover letter, interview prep, portfolio
> — is a PROJECTION derived from that knowledge base. Build once, project
> anywhere.
>
> The Python runtime is LLM-agnostic (zero LLM imports, CI-enforced). It has 407
> passing tests and 5 runnable demos. The AI Skills orchestrate the runtime from
> Claude Code or OpenCode.

Do not explain the architecture in detail yet. Let the demos do the talking.

---

## Step 1: Verify the environment

Before running anything, check the human's environment:

```bash
python --version    # needs 3.9+
pip --version
git --version
```

If Python is too old, tell them to upgrade. If `python` doesn't work, try
`python3`. On Windows, both should work if Python is on PATH.

---

## Step 2: Install dependencies

```bash
pip install -r scripts/requirements.txt
```

This installs: `pytest`, `jsonschema`, `PyYAML`, `pypdf`, `python-docx`,
`Pillow`. All are lightweight, no GPU, no large downloads.

If the human sees permission errors, suggest `pip install --user -r
scripts/requirements.txt` or using a virtual environment.

---

## Step 3: Run the test suite (confidence check)

```bash
python -m pytest tests -q
```

Expected: **407 passed**. This proves the repo is healthy and the runtime works
on their machine. If any tests fail, see the Troubleshooting section below.

Tell the human: "407 tests passed — the entire runtime is working on your
machine. Now let me show you what it actually does."

---

## Step 4: Run the demos in order (the "aha" moment)

This is the most important step. Run the demos one by one and explain what each
one demonstrates. Do not skip ahead — each demo builds on the previous concept.

### Demo 1: Runtime smoke test

```bash
python scripts/demo_sprint1.py
```

**What to tell the human:**

> This is the foundation. It shows the Event Bus (how components communicate),
> the Knowledge Index (how the system searches your vault), and the Memory
> (how it remembers your conversation). These are the three pillars everything
> else is built on.

Expected output: `[PASS] Sprint 1 Runtime is alive.`

### Demo 2: Importer (zero-AI file parsing)

```bash
python scripts/demo_sprint25.py
```

**What to tell the human:**

> This shows how ResumeOS reads files. It takes a README file and extracts
> structured data — tech stack, project name — WITHOUT any AI. Pure file
> parsing: regex, PDF text extraction, DOCX XML, image EXIF, git log. This is
> important: the parser is deterministic. It never hallucinates.

Expected output: a ProjectArtifact with `tech_stack: [Python, ROS, ROS2, CMake]`
and a SHA256 hash.

### Demo 3: Inbox orchestrator (batch import)

```bash
python scripts/demo_sprint3.py
```

**What to tell the human:**

> This shows the Inbox workflow. You drop 3 files into the inbox — a README, a
> PDF, and an image. The system batch-imports them: each file becomes an
> Artifact, an event is published, a receipt is generated, the original is
> archived, and the inbox is empty again. This is the "you just save your work"
> experience.

Expected output: 3 receipts, 3 archived files, 3 events, replay works.

### Demo 4: Career builder (Artifact to Knowledge)

```bash
python scripts/demo_sprint4.py
```

**What to tell the human:**

> This is where AI comes in — but in a controlled way. The Builder takes an
> Artifact, sends it through a pipeline (plan, retrieve, LLM, validate, merge),
> and produces a Knowledge Object with full provenance. Every piece of knowledge
> records WHO generated it, WHICH LLM, WHICH prompt, FROM which artifact, and
> WHEN. If the LLM suggests something that conflicts with existing knowledge,
> the conflict is flagged — the system never silently overwrites.

Expected output: `career/projects/sample-project.md` with provenance frontmatter.

### Demo 5: Resume assembly (the payoff)

```bash
python scripts/demo_sprint5.py
```

**What to tell the human:**

> This is the final step. You give it a job description. It reads your knowledge
> base, selects relevant entries, ranks them by relevance to that specific JD,
> builds a ResumeIR (intermediate representation), and renders it to three
> formats — Markdown, JSON Resume, and HTML. Same knowledge base, different JD
> = different resume. And it can explain WHY each item is in the resume.

Expected output:
- Scenario 1 (ROS JD): top project = PX4 UAV, score 0.194
- Scenario 2 (CV JD, same KB): top project = YOLO Detection, score 0.159
- Knowledge base unchanged after assembly
- 3 output files per scenario: .md, .json, .html

**This is the moment where the human understands the value proposition.** The
same knowledge base produces different resumes for different jobs, and nothing
is fabricated — everything traces back to the vault.

---

## Step 5: Open the vault in Obsidian (optional but recommended)

If the human has Obsidian installed:

1. Open Obsidian
2. Click "Open folder as vault"
3. Select the `vault/` directory in the repo
4. Install recommended community plugins: Dataview, Templater, QuickAdd, Canvas

**What to tell the human:**

> Your knowledge base lives in `vault/career/`. Each subfolder is an entity type:
> projects, research, education, skills, awards, competitions, internships,
> opensource. Each file is a Markdown note with YAML frontmatter validated
> against a JSON Schema. You can edit these directly in Obsidian — backlinks,
> tags, and Canvas all work. This is your career database, and it's just
> Markdown files on your disk. You own it.

---

## Step 6: Install Skills in Claude Code / OpenCode (optional)

If the human uses Claude Code or OpenCode:

1. Point the agent at the `skills/` directory
2. Or symlink individual skill folders into `.claude/skills/`
3. The root `plugin.json` registers the full bundle

**What to tell the human:**

> The 9 Skills are AI agent plugins. `career_collector` ingests raw material,
> `career_builder` enriches the vault, `resume_builder` generates a master
> resume, `resume_tailoring` tailors it to a JD, `cover_letter` writes cover
> letters, `interview` generates prep packs, `resume_review` reviews resumes,
> `job_tracker` tracks applications, `career_update` watches for vault changes.
> You can install all of them or just the ones you need.

---

## What NOT to do

- Do NOT tell the human to edit generated resumes directly. The invariant is:
  update the knowledge base, regenerate everything.
- Do NOT claim the system can write resumes without a knowledge base. It cannot.
  The knowledge base IS the product. The resume is a projection.
- Do NOT skip the demos. The demos are how humans understand the system. Running
  `pytest` and seeing 407 passed is not the same as watching `demo_sprint5.py`
  produce different resumes for different JDs.
- Do NOT explain all 21 ADRs unless the human asks. They are there for
  contributors and architects, not first-time users.

---

## Troubleshooting (for you, the AI)

### Tests fail on first run

Most common cause: dependencies not installed or Python version too old.

```bash
python --version                    # must be 3.9+
pip install -r scripts/requirements.txt
python -m pytest tests -q
```

If the git fixture tests fail (`test_git_repo_e2e`), the `tests/conftest.py`
auto-regenerates the git fixture on first run. Make sure `git` is on PATH.

### `ModuleNotFoundError: No module named 'runtime'`

The repo root must be on `sys.path`. The `conftest.py` at the repo root handles
this for pytest. If running a script directly, run it from the repo root:

```bash
cd /path/to/ResumeOS
python scripts/demo_sprint5.py
```

### CRLF warnings on Windows

Harmless. Suppress with:

```bash
git config --global core.autocrlf true
```

### Obsidian doesn't show the vault correctly

Make sure they opened `vault/` specifically, not the repo root. The repo root
is not an Obsidian vault.

---

## Key files to know (if the human asks for details)

| File | What it is |
|---|---|
| `README.md` | Project overview, quick start, architecture (start here) |
| `README.zh-CN.md` | Chinese version of README |
| `DEPLOYMENT.md` | Step-by-step deployment guide for humans |
| `ROADMAP.md` | What's done (Sprint 1-5) and what's planned |
| `docs/decisions/` | 21 Architecture Decision Records (ADR-0000 to ADR-0020) |
| `docs/architecture/README.md` | C4 model, system context, container diagrams |
| `docs/ux/` | UX specifications (inbox workflow, conversation design, CLI, data lifecycle) |
| `docs/runtime/` | Runtime module documentation, event catalog |
| `docs/guides/` | Skill authoring, plugin development, schema extension, MCP, Obsidian setup |
| `skills/registry.yaml` | Skill registry — all 9 skills with versions and dependencies |
| `resumeos.config.yaml` | Central configuration |
| `scripts/requirements.txt` | Python dependencies |
| `schemas/` | JSON Schemas for every entity, artifact, and runtime structure |

---

## The elevator pitch (if the human asks "why should I use this?")

> Most resume tools are generators: you type, they format, and your career data
> dies when you close the tab. ResumeOS inverts this. Your career lives in
> Markdown files you own — one project note, one skill note, one award note at a
> time. When you need a resume, the system assembles one from your knowledge
> base, tailored to the job, with every bullet traceable to a source. When you
> need a cover letter, it projects from the same knowledge. When you need
> interview prep, same knowledge. Build once, project anywhere. And the runtime
> is LLM-agnostic — you can swap Claude for GPT for DeepSeek without changing a
> line of core code.

---

## One last thing

If the human says "this is cool, what's next?", point them to:

1. `docs/guides/obsidian-setup.md` — set up the vault properly
2. `docs/guides/skill-authoring-spec.md` — build their own Skill
3. `ROADMAP.md` — see what's planned (CLI, real LLM providers, benchmarks)
4. `CONTRIBUTING.md` — contribute back

If they say "I want to actually use this for my career", tell them:

> Start by creating your first project note in `vault/career/projects/`. Use the
> template in `templates/project.md`. Fill in the YAML frontmatter — title,
> role, tech stack, timeline, metrics. That's your first knowledge entry. Drop a
> README or PDF into `vault/inbox/` and the system will help you extract more.
> Once you have 5-10 entries, run `demo_sprint5.py` with your own JD to see your
> first tailored resume.
