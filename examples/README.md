# ResumeOS — Example Vault & Derived Outputs

This is a **complete reference vault plus derived outputs**, used as a fixture for tests,
onboarding, and documentation.

> **Facts here are fictional but internally consistent.** Do not copy these notes into your real
> vault. They exist to show how ResumeOS works end-to-end.

## Structure

```
examples/
├── vault/                          # the example knowledge base (the SSOT)
│   ├── career/{projects,research,competitions,internships,opensource,awards,education,skills}/
│   ├── jobs/                       # job applications
│   ├── inbox/                      # raw import awaiting enrichment
│   └── canvas/                     # career-graph .canvas
└── output/                         # derived documents (regenerable, never edited)
    ├── acme-perception-2024/
    │   ├── artifacts/              # pipeline phase artifacts (auditable)
    │   ├── resume.md
    │   ├── cover-letter.md
    │   └── interview-prep.md
    └── dashboard.md
```

## What it demonstrates

1. **Knowledge base as SSOT (ADR-0001):** every derived fact traces to a vault entity.
2. **Schema validation (ADR-0002):** every entity's frontmatter validates against `schemas/`.
3. **Anti-hallucination (ADR-0007):** `gaps.json` contains a `missing` high-severity gap with a
   follow-up question (ask, never invent); every `assembly.json` bullet carries `provenance`
   citations; `resume.md` contains no fact untraceable to the vault.
4. **Checkpoint pipeline (ADR-0006):** the three artifacts (`research`, `gaps`, `assembly`) are the
   checkpoint outputs of `resume_tailoring` Phases 1–3.
5. **Content/derived separation (ADR-0010):** vault facts in `vault/`, derived docs in `output/`.

## The example candidate

An engineering student with robotics + computer-vision projects (PX4 UAV, ROS Navigation, YOLO
Detection, Brain-Computer Interface), applying to perception/autonomy roles.
