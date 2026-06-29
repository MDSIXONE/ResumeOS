# ADR-0006: Checkpoint-Based Phased Pipeline for Tailoring & Review

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS maintainers
- **Related:** ADR-0001, ADR-0007

## Context

We studied three resume-tailoring pipelines:

- **resume-tailoring-skill** — a 6-phase **sequential** pipeline with checkpoints and
  confidence-scored content selection, plus a self-improving library.
- **Resume Matcher** — parse → embed → vector search → score; per-job, no checkpoints.
- **nishilbhave/ats-resume-tailor** — a 7-agent sequential pipeline that *experimented* with parallel
  agents and reverted, because "each agent would work blind" without the prior phase's output.

All three converge on the same lesson: **a phased, sequential pipeline with user checkpoints beats
one-shot generation and beats parallel agent execution.** The checkpoint (user review between phases)
is what makes tailoring trustworthy: the user corrects the research/gap analysis *before* a resume is
generated from it.

## Decision

`resume_tailoring` (and `resume_review`) run as a **sequential, checkpoint-based phased pipeline**.
Each phase emits a **validated JSON artifact** under `output/<job>/artifacts/`. Phases run strictly in
order; a phase never starts until the previous phase's artifact is approved at its checkpoint.

### `resume_tailoring` phases

| Phase | Name | Output artifact | Checkpoint |
|---|---|---|---|
| 0 | Library Build | `library.json` | no |
| 1 | Research (JD, company, ATS keywords) | `research.json` | **yes** |
| 2 | Gap Analysis (missing/underdeveloped/misaligned) | `gaps.json` | **yes** |
| 3 | Assembly (ranked projects, reworded bullets, scores) | `assembly.json` | **yes** |
| 4 | Generation (MD → DOCX/LaTeX/JSON Resume) | `resume.*` | no |
| 5 | Library Update (self-improving memory) | `vault/.library/<job>.json` | no |

### Rules

1. **Sequential.** No parallel phase execution. Phase N depends on phase N-1's artifact.
2. **Artifacts are validated.** Each artifact conforms to a JSON Schema
   (`schemas/artifacts/*.schema.json`), so a phase's output is machine-checkable.
3. **Checkpoints pause for user review.** At a checkpoint the Skill presents the artifact and waits.
   The user may approve, edit the artifact, or send the Skill back to an earlier phase.
4. **Provenance preserved.** Every bullet in `assembly.json` cites the vault entity + field it came
   from. This is how anti-hallucination (ADR-0007) is enforced in the pipeline.
5. **Self-improving library (Phase 5).** Learnings (what worked, what the user edited) are saved to
   `vault/.library/` and fed into the next run's Phase 0.
6. **Re-runnable.** Because artifacts are files, any phase can be re-run independently after a
   checkpoint edit, without redoing earlier phases.

## Consequences

- **Positive:** user catches errors before generation → dramatically higher quality and trust.
- **Positive:** artifacts are an audit trail; a recruiter or the user can inspect *why* a project was
  selected and *where* each bullet came from.
- **Positive:** re-runnability saves cost (edit one phase, not the whole pipeline).
- **Negative:** sequential is slower than parallel. Accepted — parallel was empirically worse
  ("agents working blind").
- **Negative:** more moving parts (artifact schemas, checkpoint UX). Justified by quality.

## Alternatives considered

- **One-shot generation.** Rejected: no error correction before output; low trust; no audit trail.
- **Parallel multi-agent.** Rejected: the nishilbhave experiment showed dependent phases cannot be
  parallelized without each agent losing context.
- **No checkpoints, full sequential.** Rejected: a mistake in Phase 1 propagates to Phase 4
  uncorrected; checkpoints are the cheap insurance.
