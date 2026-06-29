# ADR-0018: Workflow Engine — Declarative Sequences Over Hardcoded Pipelines

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS lead, Runtime track
- **Related:** ADR-0004, ADR-0006, ADR-0014, ADR-0012
- **Supersedes:** none
- **Superseded by:** none

## Context

ADR-0006 hardcoded a 6-phase checkpoint pipeline for `resume_tailoring` and `resume_review`:
Library Build → Research → Gap Analysis → Assembly → Generation → Library Update. Each phase
emits a validated JSON artifact; checkpoints gate the user. This works and is correct for
those two Skills. But the pattern is **duplicated per Skill in code** — adding a new pipeline
(e.g. a portfolio generation pipeline, a CV-renewal pipeline, a "refresh all stale skills"
batch pipeline) means writing a new Skill with a new hardcoded phase sequence. The user's
Phase 2 review asked for a Workflow Engine where "users can write their own workflow" as a
declarative `workflows/*.yaml`.

Two forces:

1. **Hardcoded pipelines do not compose.** A user who wants "import github → tailoring →
   review → cover letter → interview prep" as one command must invoke 5 Skills in sequence
   manually. There is no way to declare that chain once and run it. Each Skill knows nothing
   of its successor (which is good for decoupling per ADR-0014), but nothing orchestrates the
   chain either.
2. **ADR-0006's checkpoint pattern is valuable but locked into two Skills.** The checkpoint
   discipline (emit artifact, gate user, proceed) is a reusable runtime primitive, not a
   `resume_tailoring`-specific idea. A workflow engine generalizes it.

The Event Bus (ADR-0014) gives us decoupled Skills but does not sequence them — a
`ResumeGenerated` event lets `resume_review` react, but no one declares "run tailoring, then
on `ResumeGenerated` run review, then on `ReviewPassed` run cover letter." That declarative
sequencing is the workflow engine's job.

## Decision

A **declarative Workflow Engine** that runs named sequences of Skill invocations, gated by
events and optional checkpoints. Workflows are YAML files under `workflows/`; the runtime
loads and executes them. Skills remain decoupled (ADR-0014); the workflow is the only place
that knows the order.

### Workflow file format

`workflows/<name>.yaml`, validated by `schemas/runtime/workflow.schema.json`:

```yaml
id: resume.full
version: "1.0.0"
description: "Full resume generation — research → tailor → review → cover letter → interview."
trigger: manual                 # manual | event | cron (cron is future)
trigger_event: null             # required if trigger: event; an event type from the catalog
steps:
  - id: research
    skill: resume_tailoring     # the Skill to invoke
    phase: research             # which SKILL.md phase to run (ADR-0006)
    inputs:
      target_role: "${trigger.target_role}"
    checkpoint: true            # gate the user before proceeding
    on_success_event: ResearchCompleted   # event to emit on success
  - id: gap_analysis
    skill: resume_tailoring
    phase: gap_analysis
    depends_on: [research]      # only run after research succeeds
    inputs:
      research_artifact: "${steps.research.artifact_path}"
    checkpoint: true
    on_success_event: GapAnalysisCompleted
  - id: assembly
    skill: resume_tailoring
    phase: assembly
    depends_on: [gap_analysis]
    checkpoint: true
    on_success_event: AssemblyCompleted
  - id: generate
    skill: resume_tailoring
    phase: generation
    depends_on: [assembly]
    on_success_event: ResumeGenerated
  - id: review
    skill: resume_review
    depends_on: [generate]
    on_success_event: ReviewPassed
  - id: cover_letter
    skill: cover_letter
    depends_on: [generate]
    on_success_event: CoverLetterGenerated
  - id: interview
    skill: interview
    depends_on: [generate]
    on_success_event: InterviewPrepGenerated
```

### Concrete rules

1. **Workflows are declarative, not imperative.** A workflow file names the steps, their
   Skill + phase, their dependencies, their inputs, and whether each is a checkpoint. The
   runtime executes them. There is no `workflow.run()` code inside Skills — a Skill is
   invoked by the runtime per the workflow; it does not know it is in a workflow.

2. **Steps reference Skills by id, not path.** `skill: resume_tailoring` resolves via
   `skills/registry.yaml` (ADR-0004 §4). A workflow breaks if a Skill is uninstalled; the
   runtime reports the missing dependency before execution.

3. **Dependencies form a DAG, not just a chain.** `depends_on: [...]` lets steps run in
   parallel when independent (cover_letter + interview both depend on generate but not on
   each other). The runtime topologically sorts and runs ready steps concurrently when
   possible. Cycles are rejected at load time.

4. **Checkpoints gate the user (ADR-0006).** A step with `checkpoint: true` pauses
   execution after the Skill's phase emits its artifact, surfaces the artifact to the user,
   and waits for explicit approval before running dependent steps. A checkpoint rejection
   terminates the workflow with status `checkpoint_rejected` and the artifacts produced so
   far are retained (regenerable, not rolled back).

5. **Step inputs interpolate from trigger + prior steps.** `${trigger.<field>}` reads the
   workflow trigger payload; `${steps.<id>.artifact_path}` reads a prior step's emitted
   artifact path; `${steps.<id>.output.<field>}` reads a prior step's structured output.
   The runtime resolves interpolations before invoking the Skill.

6. **Events drive cross-workflow reaction.** A step's `on_success_event` emits a domain
   event (ADR-0014). A workflow with `trigger: event` and `trigger_event: ResumeGenerated`
   starts when that event fires. This lets a user wire "when tailoring finishes, auto-run
   review" without editing the tailoring workflow. Workflows compose via events, the same
   decoupling model as Skills.

7. **Manual trigger is the default.** `resume workflow run resume.full --target-role "..."
   ` invokes a workflow by id. `resume workflow list` lists available workflows. `resume
   workflow show <id>` prints the resolved DAG. Watch mode (ADR-0011 V2) additionally
   reacts to `trigger: event` workflows automatically.

8. **The existing ADR-0006 pipelines become workflows.** `resume_tailoring`'s 6-phase
   pipeline is expressible as `workflows/resume.tailoring.yaml`; `resume_review`'s as
   `workflows/resume.review.yaml`. The hardcoded phase logic inside the Skill stays (the
   Skill still knows how to run phase N); the workflow declares the sequence + checkpoints
   + cross-Skill chaining. This is a refactor target for Phase 4, not a Phase 3 deliverable
   — Phase 3 ships the engine + the `resume.full` example, and existing Skills keep working
   via direct CLI invocation as today.

9. **Workflows are versioned.** `version` in the workflow file follows semver. Breaking
   changes (renamed steps, removed checkpoints) bump major. The runtime warns if a workflow
   references a Skill version it was not tested against.

10. **Failure handling.** A step that fails (Skill returns an error, anti-hallucination
    block per ADR-0007, or a checkpoint rejection) halts the workflow. Already-completed
    steps' artifacts are retained (idempotent re-runs skip completed steps unless
    `--force-rerun`). The workflow status is recorded in `vault/.library/workflows/<run-id>.json`
    (git-ignored, audit trail) so a crashed workflow can be resumed from the last
    successful step.

11. **User-authored workflows.** A user drops a YAML file into `workflows/` and it appears
    in `resume workflow list`. No code, no Skill modification. This is the extensibility
    point the Phase 2 review asked for. Community workflows namespace as
    `com_<author>_<name>`.

## Consequences

- **Positive:** Pipelines are declarative and reusable — the ADR-0006 checkpoint pattern
  generalizes to any Skill chain without per-Skill code duplication.
- **Positive:** Users compose their own workflows ("import github → tailoring → review →
  cover letter" in one command) without modifying any Skill.
- **Positive:** Workflows compose via events (ADR-0014) — one workflow's success can
  trigger another, achieving cross-workflow orchestration without a meta-orchestrator.
- **Positive:** Parallel steps (cover_letter + interview) run concurrently when independent,
  shortening end-to-end runtime.
- **Positive:** Failed workflows resume from the last successful step — no lost work, no
  forced restart.
- **Negative:** Indirection — debugging a failed workflow requires reading the run state at
  `vault/.library/workflows/<run-id>.json` plus `events.jsonl`. Mitigated by `resume workflow
  status <run-id>` and step-level status records.
- **Negative:** Two ways to run a Skill (direct CLI `resume tailor` vs workflow `resume
  workflow run resume.full`). Documented clearly: direct CLI = single Skill ad-hoc;
  workflow = declared chain. They coexist; neither is deprecated.
- **Neutral:** The engine is in-process v1 (same as the Event Bus, ADR-0014 §5). A
  long-running workflow daemon is a watch-mode concern, not a v1 concern.

## Alternatives considered

- **Keep hardcoded pipelines per Skill (status quo).** Rejected: does not compose, does not
  let users author chains, duplicates the checkpoint discipline. The Phase 2 review
  explicitly asked for declarative workflows.

- **Workflow-as-code (Python scripts that call Skills).** Rejected: code is not declarative,
  not inspectable by `resume workflow list`, and not authorable by non-developers. YAML keeps
  the bar low (matches the user's "users can write their own workflow" ask).

- **Event-only orchestration (no workflow files; chain via event subscriptions).** Rejected:
  event subscriptions (ADR-0014) are reactive and stateless — they cannot express "run these
  7 steps in order with 3 checkpoints and parallel cover_letter + interview." Events compose
  workflows; they do not replace the workflow declaration.

- **An external orchestrator (Airflow, Prefect, Temporal).** Rejected: violates local-first
  (ADR-0008), adds heavy dependencies, and over-engineers a single-user CLI. The in-process
  YAML engine covers v1.

- **Workflows that call Skills by path, not id.** Rejected: fragile (path moves break
  workflows), no version pinning, no registry resolution. Id-based references match
  ADR-0004 §4 and ADR-0017 (prompt registry).
