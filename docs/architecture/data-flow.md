# Data Flow

How data moves through ResumeOS: from raw career material to a derived, job-tailored resume.
Every arrow below is a **validated** transition. Skills never pass unvalidated data between stages.

---

## 1. End-to-end pipeline

```mermaid
flowchart TB
  RAW["Raw material\nPDF / DOCX / MD / GitHub / LinkedIn / images / certs"]
  INBOX["vault/inbox/*.md\n(staged, unvalidated)"]
  KB["vault/career/*\n(validated entities)"]
  JD["Job Description\n(input to tailoring)"]
  ART["output/<job>/artifacts/*.json\n(phase artifacts)"]
  DERIVED["output/<job>/*\nresume / cover / prep"]
  LIB["vault/.library/\ntailoring memory"]

  RAW -- "career_collector" --> INBOX
  INBOX -- "career_builder\n(ask follow-ups)" --> KB
  KB -- "resume_builder" --> DERIVED
  KB --> RT["resume_tailoring\n(6-phase pipeline)"]
  JD --> RT
  RT -- "phase artifacts" --> ART
  ART -- "checkpoint review" --> RT
  RT --> DERIVED
  RT -- "Phase 5" --> LIB
  LIB -- "next run" --> RT
```

---

## 2. The ingest path (career_collector → career_builder)

```mermaid
sequenceDiagram
  participant U as Career Owner
  participant CC as career_collector
  participant IN as vault/inbox
  participant CB as career_builder
  participant KB as vault/career
  participant S as schemas/

  U->>CC: Drop PDF/DOCX/GitHub export into inbox source
  CC->>IN: Write staging note(s) with extracted text + source provenance
  CC->>U: Report what was collected, flag low-confidence extractions
  U->>CB: Run career_builder on inbox
  CB->>IN: Read staged notes
  CB->>S: Validate any partial frontmatter
  CB->>U: Ask follow-up questions for gaps (never guess)
  U->>CB: Answer
  CB->>KB: Write enriched entity note(s) validated against schema
  CB->>U: Show knowledge-graph diff (new backlinks, tags)
```

**Provenance rule:** every entity created by `career_collector` records its source(s) in
`frontmatter.sources[]`. `career_builder` never removes provenance. This is the audit trail that
makes anti-hallucination enforceable (ADR-0007).

---

## 3. The tailoring path (resume_tailoring, 6 phases)

Adopted from the `resume-tailoring-skill` pattern and hardened with checkpoints
([ADR-0006](../decisions/ADR-0006-checkpoint-phased-pipeline.md)). Each phase emits a **validated
JSON artifact** so a phase can be re-run, audited, or checkpoint-reviewed independently.

```mermaid
flowchart LR
  P0["Phase 0\nLibrary Build\nindex vault + skill vectors"] --> P1
  P1["Phase 1\nResearch\nJD + company + ATS keywords"] --> C1{{"checkpoint"}}
  C1 --> P2["Phase 2\nGap Analysis\nmissing/weak/misaligned"] --> C2{{"checkpoint"}}
  C2 --> P3["Phase 3\nAssembly\nconfidence-scored selection"] --> C3{{"checkpoint"}}
  C3 --> P4["Phase 4\nGeneration\nMD→DOCX/LaTeX/JSON Resume"]
  P4 --> P5["Phase 5\nLibrary Update\nself-improving memory"]
```

| Phase | Input | Output artifact | Checkpoint? |
|---|---|---|---|
| 0 Library Build | `vault/career/*` | `library.json` (entity index + vectors) | no |
| 1 Research | JD, company | `research.json` (requirements, culture, ATS keywords) | **yes** |
| 2 Gap Analysis | library + research | `gaps.json` (missing/underdeveloped/misaligned) | **yes** |
| 3 Assembly | library + gaps | `assembly.json` (ranked projects, reworded bullets, scores) | **yes** |
| 4 Generation | assembly | `resume.md` + `resume.docx` + `resume.tex` + `resume.json` | no |
| 5 Library Update | assembly + feedback | `vault/.library/<job>.json` | no |

**Checkpoint contract:** at a checkpoint, the Skill pauses and presents the artifact for user review.
The next phase does **not** run until the user approves or edits the artifact. Phases are sequential
by design — parallel execution would make each phase "work blind" (ADR-0006).

---

## 4. The regeneration path (career_update)

`career_update` watches the vault. When a new file appears (or an entity changes), it:

1. Validates the file against its schema (infer entity type from folder).
2. Calls `career_builder` enrichment on it (ask follow-ups for gaps).
3. Marks derived documents that depended on this entity as **stale** (written to
   `output/.stale.json`).
4. Prompts the user to regenerate stale derived docs (does **not** auto-regenerate without consent).

```mermaid
flowchart LR
  EVT["vault change event"] --> CU["career_update"]
  CU --> VAL{"schema valid?"}
  VAL -- no --> ASK["ask user to fix frontmatter"]
  VAL -- yes --> ENR["career_builder enrichment"]
  ENR --> STALE["mark derived docs stale"]
  STALE --> PROMPT["prompt user to regenerate"]
```

---

## 5. What never happens

These flows are **forbidden** by the architecture and enforced by `plugin.json` permissions:

- Writing derived documents into the vault.
- Reading `output/` as input to any Skill (derived data is not a source of truth).
- A Skill inventing a fact not present in the vault (ADR-0007).
- MCP servers writing directly to the vault (they go through a Skill).
- Editing a derived file to "fix" it (fix the vault, then regenerate).
