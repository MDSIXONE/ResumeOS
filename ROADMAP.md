# Roadmap

ResumeOS development is organized into specification phases and implementation sprints. The spec phases defined the architecture; the sprints built it.

---

## Phase 1-3: Specification (DONE)

**Goal:** Define the architecture, data model, plugin system, and skill contracts before writing implementation code.

| Deliverable | Status | Reference |
|---|---|---|
| Architecture Decision Records | Done | 21 ADRs (ADR-0000 through ADR-0020) |
| Vault schemas (9 entity types, JSON Schema draft 2020-12) | Done | ADR-0002, `schemas/` |
| Plugin manifest schema + root bundle manifest | Done | ADR-0004, ADR-0005 |
| 9 Skill definitions (SKILL.md, plugin.json, prompts/) | Done | `skills/registry.yaml` |
| UX specifications | Done | `docs/ux/` |
| Runtime design (event bus, knowledge index, workflow, memory) | Done | ADR-0012 through ADR-0020 |
| Central configuration schema | Done | `resumeos.config.yaml` |
| CI pipeline (schema validation, pytest) | Done | `.github/workflows/` |
| All documentation guides | Done | `docs/guides/` |

---

## Sprint 1: Core Runtime (DONE)

**Goal:** Build the foundational runtime modules that every other layer depends on.

| Module | File | Status |
|---|---|---|
| Event Bus (pub/sub) | `runtime/event_bus.py` | Done |
| Knowledge Index (vault search) | `runtime/knowledge_index.py` | Done |
| Workflow Engine (DAG execution) | `runtime/workflow.py` | Done |
| Conversation Memory | `runtime/memory.py` | Done |
| Dispatcher | `runtime/dispatcher.py` | Done |
| LLM Provider interface | `runtime/llm_provider.py` | Done |
| DummyLLM adapter | `adapters/llm/dummy.py` | Done |
| Skill base class | `sdk/python/skill.py` | Done |

**Demo:** `scripts/demo_sprint1.py`

---

## Sprint 2: Artifact Layer (DONE)

**Goal:** Define the immutable Artifact type with full provenance tracking.

| Module | File | Status |
|---|---|---|
| Artifact base class | `runtime/artifacts/base.py` | Done |
| Artifact type definitions | `runtime/artifacts/types.py` | Done |
| Dependency-direction CI enforcement | `tests/integration/test_dependency_direction.py` | Done |

**Demo:** Integrated into Sprint 2.5 demo.

---

## Sprint 2.5: Importer Runtime (DONE)

**Goal:** Parse raw files into Artifacts without any LLM calls — pure file processing.

| Module | File | Status |
|---|---|---|
| Detector (file type identification) | `runtime/importer/detector.py` | Done |
| Extractor base + registry | `runtime/importer/extractor.py`, `registry.py` | Done |
| PDF text extractor | `runtime/importer/extractors/pdf_text.py` | Done |
| DOCX text extractor | `runtime/importer/extractors/docx_text.py` | Done |
| Git log extractor | `runtime/importer/extractors/git_log.py` | Done |
| Image EXIF extractor | `runtime/importer/extractors/image_exif.py` | Done |
| README parser extractor | `runtime/importer/extractors/readme_parser.py` | Done |
| Normalizer | `runtime/importer/normalizer.py` | Done |
| Importer pipeline | `runtime/importer/pipeline.py` | Done |

**Demo:** `scripts/demo_sprint25.py`

---

## Sprint 3: Inbox Orchestrator (DONE)

**Goal:** Batch import multiple files with event emission, receipts, archiving, and deterministic replay.

| Module | File | Status |
|---|---|---|
| Inbox orchestrator | `runtime/inbox/orchestrator.py` | Done |
| Inbox state machine | `runtime/inbox/state.py` | Done |
| Transaction (atomic operations) | `runtime/transaction.py` | Done |
| Replay (deterministic re-execution) | `runtime/replay.py` | Done |
| Import receipt | `runtime/receipt.py` | Done |

**Demo:** `scripts/demo_sprint3.py`

---

## Sprint 4: Career Builder (DONE)

**Goal:** Transform Artifacts into structured KnowledgeObjects through an LLM-powered pipeline with provenance and conflict detection.

| Module | File | Status |
|---|---|---|
| Planner (decompose enrichment task) | `runtime/builder/planner.py` | Done |
| Retriever (find relevant context) | `runtime/builder/retriever.py` | Done |
| Validator (check LLM output) | `runtime/builder/validator.py` | Done |
| Merger (merge into knowledge base) | `runtime/builder/merger.py` | Done |
| Builder pipeline | `runtime/builder/pipeline.py` | Done |
| KnowledgeObject | `runtime/knowledge/object.py` | Done |
| Provenance tracking | `runtime/knowledge/provenance.py` | Done |
| Conflict detection | `runtime/knowledge/conflict.py` | Done |
| Draft management | `runtime/knowledge/draft.py` | Done |
| Writer | `runtime/knowledge/writer.py` | Done |

**Demo:** `scripts/demo_sprint4.py`

---

## Sprint 5: Resume Assembly (DONE)

**Goal:** Select, rank, and render KnowledgeObjects into tailored resumes in multiple formats, with full explainability.

| Module | File | Status |
|---|---|---|
| Selector (match knowledge to JD) | `runtime/resume/selector.py` | Done |
| Ranker (score and order entries) | `runtime/resume/ranker.py` | Done |
| Layout engine | `runtime/resume/layout.py` | Done |
| ResumeIR (intermediate representation) | `runtime/resume/ir.py` | Done |
| Resume pipeline | `runtime/resume/pipeline.py` | Done |
| Tailoring orchestrator | `runtime/resume/tailoring.py` | Done |
| Review engine | `runtime/resume/review.py` | Done |
| Markdown renderer | `runtime/resume/renderer/markdown.py` | Done |
| JSON Resume renderer | `runtime/resume/renderer/json_resume.py` | Done |
| HTML renderer | `runtime/resume/renderer/html.py` | Done |
| Renderer base class | `runtime/resume/renderer/base.py` | Done |

**Demo:** `scripts/demo_sprint5.py`

---

## What is next

The specification and core runtime are complete. The next phase focuses on making ResumeOS usable in the real world.

### Near-term (planned)

- **CLI** — Command-line interface for running pipelines without an AI agent
- **Real LLM providers** — OpenAI, Anthropic, and local model adapters in `adapters/llm/`
- **Performance benchmarks** — Measure and publish pipeline throughput
- **PDF and DOCX renderers** — Extend the renderer layer beyond MD/JSON/HTML
- **More importers** — LinkedIn export, email parsing, OCR for scanned documents
- **Obsidian plugin** — `resumeos-bridge` for tighter UI integration inside Obsidian

### Mid-term (planned)

- **TypeScript SDK** — `sdk/typescript/` for building Skills in TypeScript
- **MCP adapters** — GitHub, Browser, Google Drive, Notion integrations
- **Dataview dashboards** — Pre-built Obsidian views for career timeline, skill gaps, job pipeline
- **JSON Resume 1.0.0 round-trip** — Bidirectional converter between ResumeOS and JSON Resume
- **Portfolio / website generator** — Vault to static site projection

### Long-term (ideas)

- CRDT sync for multi-device concurrent edits (Automerge / Yjs)
- Voice-based vault entry (transcribe interview notes)
- Email adapter for parsing application and offer confirmation emails
- Multi-language vault support (EN/ZH parallel frontmatter)
- Export to Europass CV, academic CV (IEEE/ACM formats)
- Plugin marketplace and community Skill contributions

---

## How this roadmap is updated

- Completed sprints: marked Done with links to demos and modules.
- Planned items: committed to but not yet started. Promoted from ideas when an ADR and prototype exist.
- Ideas: no commitment. To promote an idea, open a PR with an ADR and a working prototype.
