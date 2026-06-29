# Vault .library

This directory holds **machine-managed tailoring memory** written by `resume_tailoring` Phase 5
and consumed on the next tailoring run. Contents are JSON files keyed by job slug (e.g.,
`<job-slug>.json`).

## Do not hand-edit

The files in this directory are generated, not authored. Editing them by hand will be overwritten
the next time `resume_tailoring` runs Phase 5, and the contents are not validated by any
frontmatter schema (they are not entities).

## What lives here

After every `resume_tailoring` run, Phase 5 writes a library file that captures:

- The research artifact (Phase 1) for that job
- The gap analysis (Phase 2)
- The assembly (Phase 3): which entities were selected, with tailoring scores
- Any user edits made at checkpoints

The next run reads this library when the same job slug is requested, so the pipeline can skip
re-running phases whose outputs have not changed, and so it can carry forward user preferences
(e.g., "I prefer to emphasize project X over project Y for this company").

## Lifecycle

Library files are safe to delete. They are rebuilt on demand. Deleting `vault/.library/` entirely
simply resets the self-improving memory — the next tailoring run starts fresh.

## Reference

See [ADR-0006](../../docs/decisions/ADR-0006-checkpoint-phased-pipeline.md) for the phased
pipeline contract, and the data-flow diagram in
[`docs/architecture/data-flow.md`](../../docs/architecture/data-flow.md).
