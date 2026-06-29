# ResumeOS — Conversation Design

> **Scope:** the interaction protocol between the user and ResumeOS. This document
> defines what ResumeOS asks, when it asks, why, and how it remembers. It is read
> together with the keystone UX principles, the anti-hallucination contract
> ([ADR-0007](../decisions/ADR-0007-anti-hallucination-contract.md)), the core
> prompt ([`prompts/core/ask-never-invent.md`](../../prompts/core/ask-never-invent.md)),
> and the inbox lifecycle in
> [ADR-0011](../decisions/ADR-0011-inbox-asset-lifecycle-directories.md).
>
> ResumeOS is an intelligent career assistant, not a resume editor. The user's
> only required gesture is "drop a file." Every downstream utterance — question,
> confirmation, nudge — must earn its place.

---

## 1. Conversation principles

The conversation model is a strict subset of the keystone UX principles and the
anti-hallucination contract. ResumeOS obeys these rules in every utterance:

| Rule | Meaning | Enforced by |
|------|---------|-------------|
| **One question at a time** | Never batch. Each prompt awaits an answer before the next. | `inbox_ingest` state `NeedsConfirm`; prompt template in `ask-never-invent`. |
| **Only questions that improve the vault** | Ask only when an `entity_id:field` is `confidence: missing` and recoverable by the user. | `career_builder` gap detector; see §6. |
| **Never repeat an answered question** | Session memory holds every `(entity, field, value, source)` answered this run. ResumeOS queries memory before asking. | `inbox_ingest` session context; see §3 examples. |
| **Never fabricate** | If a fact is unknown, ask; never guess metrics, roles, tech, dates, or numbers. ADR-0007 is absolute. | Provenance check; `confidence: missing` blocks derived output. |
| **Confidence labels** | Every fact is `confirmed` / `inferred` / `missing`. Only `confirmed` flows into `output/**`. `missing` triggers a gap prompt; `inferred` triggers confirmation or is re-classified on next import. | ADR-0007 §4; `career_builder` frontmatter. |
| **Cite the gap that caused the question** | Each prompt names the entity and field: "Gap for `Project:PX4-UAV:metrics` — the JD wants quantified impact." | Prompt template in `ask-never-invent.md`. |
| **Polite, not interruptive** | Non-blocking gaps (stale entities, peripheral missing facts) surface via the dashboard, never mid-workflow. | §4 proactive nudge rules. |
| **Omit on silence, never infer** | A "no" or no answer → omit the fact. Never promote silence to `confirmed`. | `ask-never-invent` §final rule. |
| **Derive what the user should not have to** | Percentage improvements computed from known before/after values are not asked for. The user supplies raw numbers; ResumeOS computes. | See §5 anti-pattern 5. |

**Utterance types.** ResumeOS emits exactly one of four kinds per turn:

1. **Confirmation** — "I extracted X. Confirm / correct." (only when OCR/parse is ambiguous)
2. **Gap question** — one precise question, tied to a missing field.
3. **Status line** — "Recorded. Updated `entity_id`. Filed to `vault/assets/<cat>/<year>/<slug>.`" (never a question)
4. **Choice** — mutually exclusive options for a single decision (e.g. duplicate resolution).

ResumeOS never mixes types in a single utterance.

---

## 2. User journey map

A week of use. Ratings follow Mermaid `journey` scale (1–5, where 5 is "delighted").

```mermaid
journey
    title A week with ResumeOS
    section Day 1 — First drop
      Drop files into vault/inbox/: 3: User
      ResumeOS classifies, extracts, asks one question at a time: 4: User, ResumeOS
    section Day 2 — Inbox empties
      All files moved to vault/assets/ with knowledge recorded: 5: User
    section Day 3 — Knowledge grows
      Dashboard shows entities, backlinks, STAR stories: 5: User
    section Day 4 — Tailor a resume
      resume tailor produces resume + cover letter from confirmed facts: 5: User
    section Day 5 — Interview prep
      resume interview delivers Q&A grounded in vault citations: 5: User
    section Day 6 — Confidence
      Every bullet is defensible; user enters interview prepared: 5: User
```

**Why the arc is shaped this way.** Day 1 is the trust bottleneck. The user has
never seen the system work; the drop is frictionless but the "does it understand
my work?" question is open. Satisfaction rises sharply on Day 2 (Inbox empties
— visible completion), peaks by Day 3 once the dashboard renders the vault as a
navigable knowledge graph, and is sustained by Days 4–6, when the user
experiences the *derived* outputs (resume, cover letter, interview Q&A) and
sees every claim cited back to the vault.

The only point where the rating dips is the first drop. All subsequent design
decisions — single-question prompts, no re-asks, dashboard-only nudges,
citable output — exist to protect the 4 → 5 climb.

---

## 3. Conversation examples (worked)

Transcripts below are the production contract. Any implementation that produces
longer, shorter, or differently-shaped turns violates the principles in §1.
Each example respects §5 (never-ask list) and ADR-0007 (no invented facts).

### 3.1 Certificate → project linkage

User drops a certificate file. ResumeOS has extracted the recipient name, the
issuing body, and the date. It needs to link the certificate to a project and
capture role/team info.

```text
> User: [drops PX4-Completion-Certificate.pdf into vault/inbox/]

ResumeOS: Detected certificate:
            - issuer: PX4 Autopilot
            - title:  Developer Completion
            - date:   2026-05
          Which project does this certificate relate to?
          Candidates: Project:PX4-UAV, Project:SwarmDemo, None / separate credential.

User: PX4-UAV.

ResumeOS: Linked to Project:PX4-UAV. What was your role on PX4-UAV when you
          completed this? (e.g. flight-control lead, contributor, reviewer)

User: Flight control lead.

ResumeOS: Recorded role. How large was the team, including yourself?

User: 4.

ResumeOS: Updated Project:PX4-UAV:
            - role:      flight-control lead
                         (source: vault/assets/certificates/2026/px4-completion-7f3a.pdf)
            - team_size: 4 (source: user, session 2026-06-29)
          Certificate filed to vault/assets/certificates/2026/px4-completion-7f3a.pdf.
          Import entry appended to logs/imports/2026-06-29.jsonl.
```

**Notes.** Three questions, each gated on the previous answer. Candidates are
offered because the vault already contains two plausible project entities; this
is a classification aid, not a burden on the user. No fact is invented — if the
user had answered with a new project name, ResumeOS would create
`Project:<new>` and ask further.

### 3.2 Competition award missing info

User drops a photo of a competition award. OCR extracts most fields, but the
date and team size are not legible in the image.

```text
> User: [drops robotics-award-photo.jpg into vault/inbox/]

ResumeOS: OCR of image extracted:
            - competition: National Robotics Challenge
            - placing:     1st, autonomous-navigation track
            - date:        NOT legible in the photo
            - team_size:   NOT legible in the photo
          When was the competition held? (month and year is enough.)

User: November 2025.

ResumeOS: Recorded. How large was your team?

User: 3.

ResumeOS: Recorded Award:National-Robotics-Challenge:
            - date:      2025-11
            - placing:   1st, autonomous-navigation track
            - team_size: 3
          Filed to vault/assets/awards/2025/robotics-award-9c1d.jpg.
```

**Notes.** Only the two fields not legible from the image are asked. The
competition name, placing, and track are already extracted with high
confidence — asking for them again would violate §1 "never ask for info that
can be confirmed without the user."

### 3.3 Research paper missing DOI

User drops a PDF of a published paper. Title, venue, and authors are
extracted. The DOI is not in the PDF metadata and CrossRef has no match.

```text
> User: [drops adaptive-guidance-icra2025.pdf into vault/inbox/]

ResumeOS: Extracted paper:
            - title:  Adaptive Guidance for Quadrotors in GPS-Denied Environments
            - venue:  ICRA 2025
            - authors: [Zhang, Li, Chen] — is the first author you?

User: Yes.

ResumeOS: Marked first author = you.
          I could not locate a DOI from PDF metadata or CrossRef.
          Can you provide the DOI?

User: 10.1109/ICRA.2025.1098765.

ResumeOS: Recorded Research:Adaptive-Guidance-Quadrotors:
            - authors:     [Zhang (you), Li, Chen]
            - venue:       ICRA 2025
            - doi:         10.1109/ICRA.2025.1098765
          Filed to vault/assets/research/2025/adaptive-guidance-2b4e.pdf.
```

**Notes.** The first-author confirmation is a one-shot verification, not a
fabrication. The DOI question is asked precisely because the system could not
recover it; if it had, the question would have been suppressed.

### 3.4 Project missing metrics

User drops a README from an existing project. Stack and collaborators are
extracted. No outcome metric appears in the text.

```text
> User: [drops README.md into vault/inbox/]

ResumeOS: README matches existing Project:PX4-UAV. Extracted additions:
            - stack additions:     MAVLink, SITL, ROS 2 Humble
            - new collaborators:   [Kim]
          The README lists features but no outcome metric.
          What headline metric would you put on a resume for this project?
          (e.g. % reduction, time saved, throughput, error rate)

User: Cut flight-test iteration time from 4 hours to 2.5 hours.

ResumeOS: Metric captured as iteration time: 4 h → 2.5 h (computed: -37.5%).
          STAR story updated:
            S — flight-test iteration loop took a full afternoon
            T — pipeline needed to run multiple times per week
            A — rebuilt PX4 SITL + ROS 2 bridge with parallelized logs
            R — iteration time 4 h → 2.5 h (−37.5%)
          Merged into Project:PX4-UAV. README filed to
          vault/assets/projects/2026/px4-uav-readme-a8b2.md.
```

**Notes.** The raw before/after numbers come from the user; the percentage is
*computed by ResumeOS* and shown as a status line — never asked for. This is
exactly the "derive what the user should not have to" principle (§1). The
STAR structure is populated from vault facts only; the user never wrote a
bullet.

### 3.5 Ambiguous tech stack

User drops a README for a project. One of the technologies (FastAPI) appears
prominently but its role is not obvious from the text.

```text
> User: [drops README.md into vault/inbox/]

ResumeOS: Extracted Project:FleetOps. README mentions: FastAPI, PostgreSQL,
          Docker, Prometheus. FastAPI is not yet in the stack list for
          Project:FleetOps. Was FastAPI the primary framework for the
          fleet-dispatch API, or used peripherally (side tool, experiment,
          abandoned)?

User: Primary — it serves the fleet-dispatch REST API.

ResumeOS: Recorded Project:FleetOps.stack:
            - FastAPI    — primary,   role: fleet-dispatch REST API
            - PostgreSQL — primary,   role: fleet-db
            - Docker     — primary,   role: deployment
            - Prometheus — peripheral, role: observability
          The primary/peripheral distinction is preserved because it affects
          ATS keyword weighting: primary tools feature in bullets; peripheral
          tools appear under tooling. Filed to
          vault/assets/projects/2026/fleetops-readme-c3d9.md.
```

**Notes.** The primary/peripheral question is the one question that actually
improves the vault — it changes how an ATS parser weights the keyword. No
other technology gets the same question because their role is unambiguous
from context.

### 3.6 Duplicate detected (re-import of updated README)

User re-imports a README whose content has drifted from a previous import.

```text
> User: [drops updated README.md into vault/inbox/]

ResumeOS: Duplicate detected. Existing import:
            - asset:    vault/assets/projects/2026/px4-uav-readme-a8b2.md
            - imported: 2026-06-22
            - hash:     sha256:a8b2...
          New file differs in 3 sections: metrics, team_size, collaborators
          (added Park). Choose one:
            (1) Skip         — keep the existing import unchanged.
            (2) Replace      — archive the old, record the new as the source.
            (3) Merge        — apply the differences to the existing entity.
            (4) New version  — keep both; mark the new as v2 of the asset.

User: 3.

ResumeOS: Merged. Project:PX4-UAV updated:
            - metrics.iteration_time: 2.5 h → 1.8 h
            - team_size:              4 → 5
            - collaborators:          +Park
          New source asset: vault/assets/projects/2026/px4-uav-readme-f1a7.md.
          Import entry appended to logs/imports/2026-06-29.jsonl.
          Inbox root: empty.
```

**Notes.** Single question, four mutually exclusive choices — matches utterance
type 4 from §1. ResumeOS never guesses which to pick. The merge path is
explicit: the entity is updated incrementally (per keystone principle 8,
"incremental, never recreate"), and the new source asset is preserved for
provenance.

---

## 4. Career assistant — proactive behavior

ResumeOS surfaces gaps without interrupting. The distinction between
interruptive and proactive:

| Mode | Where it appears | Blocks current workflow? |
|------|------------------|--------------------------|
| **Gap question** | Mid-import, inside `needsConfirm` state | Yes (only for that file) |
| **Nudge** | Dashboard, `resume dashboard` output * | No |

\* Also renderable from the Obsidian Dataview dashboard note at
`vault/career/_import-log.md` when the user is working inside Obsidian.

### Nudge table

| Trigger | Detection heuristic | Nudge text | Action when accepted |
|---------|---------------------|------------|----------------------|
| Project has no metric | `Project:<X>.metrics` empty, `confidence: missing` | "`Project:<X>` has no metrics; want to add?" | One gap question (§3.4); STAR story updated. |
| Certificate lacks competition info | `Certificate:<X>` has no linked `Project:` or `Award:` | "`Certificate:<X>` has no linked project or competition; link it?" | One gap question (§3.1); link recorded. |
| Research paper missing DOI | `Research:<X>.doi: missing` | "Add DOI for `Research:<X>`?" | One gap question (§3.3); DOI stored. |
| Project has no GitHub / repo link | `Project:<X>.repository: missing` | "Add repo URL for `Project:<X>`?" | One gap question; URL stored with source. |
| Resume stale | `career_update.stale: true` AND `N` new entities since last tailor | "`N` new entities since last resume; run `resume tailor`?" | Invokes `resume tailor` pipeline from the CLI. |
| Skill last_used > 2 years | `Skill:<X>.last_used` older than 24 months | "Skill `<X>` last used `<year>` — refresh or archive?" | Ask whether to update `last_used` or archive the entity. |

### Nudge rules

1. **Nudges never block.** They render only on `resume dashboard` (or the
   Obsidian dashboard note). They never appear mid-import, mid-tailor, or
   during any active `inbox_ingest` session.
2. **One nudge, one question, one answer.** If the user acts on a nudge, exactly
   one gap question is asked and the flow ends. The dashboard then refreshes,
   and if the vault still has gaps, the next most valuable nudge appears.
3. **Dismissable.** Every nudge carries a dismiss action. Dismissed nudges do
   not recur for `resumeos.config.yaml: nudges.cooldown_days` (default 30).
4. **Ordered by value to tailoring.** Nudges sort by how much they unblock
   bullet generation: missing metrics > missing stack-role > missing DOI >
   missing repo > stale resume > stale skill.
5. **Never accumulate.** A nudge whose gap is filled, explicitly dismissed, or
   becomes non-recoverable is removed from the queue. The dashboard never shows
   more than five active nudges at once; beyond that, the user is shown a
   count and can expand with `resume dashboard --all`.

---

## 5. What ResumeOS never asks

The following are explicit anti-patterns. Any prompt that matches one is a bug.

| Anti-pattern | Why it violates the contract |
|--------------|------------------------------|
| "What kind of file is this?" (asks user to classify) | Classification is `inbox_ingest`'s job. The user's gesture is "drop a file." Manual classification reintroduces the friction the pipeline exists to remove. |
| "What is your name / email / city?" (for info already in the vault) | `vault/career/profile.md` (or the relevant entity) is SSOT. Asking again would violate "never ask for info already in the vault" and risks drift between the vault and the user's stated answer. |
| More than one question before receiving an answer | Violates §1 "One question at a time." Batching questions forces the user to track state that ResumeOS should track. |
| "Could you draft your bullet points for this role?" | Bullet drafting is `resume_tailoring`'s job, sourced from confirmed vault facts. Asking the user to write bullets re-introduces the hallucination surface the contract exists to close. |
| "What was the percentage improvement?" (when raw before/after values are known) | ResumeOS computes derived metrics from raw vault data. Asking the user to compute is the inverse of §1 "derive what the user should not have to." |
| Anything that invites the user to rubber-stamp an invented fact | Violates `ask-never-invent` §final rule: ResumeOS never suggests an answer, because the user may rubber-stamp it without review. |
| "I think you used Kubernetes here — should I add it?" | Suggesting a specific technology the user never mentioned is fabrication with consent-bias. ResumeOS asks only for genuinely missing *human* knowledge. |

The positive rule that follows from the table:

> ResumeOS asks a question **only if** all five are true:
> 1. The field is `confidence: missing` on a specific `entity_id`.
> 2. The field cannot be derived from other vault data.
> 3. The field cannot be recovered from the dropped file or its cache.
> 4. The answer is known only to the user (role, responsibility, metric value, decision rationale).
> 5. Filling the field would change the tailoring output meaningfully (it unlocks a nudge or a bullet).

If any condition fails, ResumeOS leaves the field `missing` and waits for a
subsequent import or a manual vault edit — and, if the gap meets §4 rules,
surfaces a nudge instead.

---

## 6. Cross-references

- [**`./inbox-workflow.md`**](./inbox-workflow.md) — where conversation gates
  sit in the file lifecycle. The `NeedsConfirm` state is the only point at
  which §1 gap questions fire during an import.
- [**`./data-lifecycle.md`**](./data-lifecycle.md) — how answers merge
  incrementally into `vault/career/**`. Every accepted answer from §3 writes an
  entry to `_last_answer` and a `sources[]` reference.
- [**`./cli-specification.md`**](./cli-specification.md) — the `resume dashboard`
  command that renders §4 nudges, and the CLI surface for `resume process`,
  `resume tailor`, `resume inbox --errors`.
- [**ADR-0007**](../decisions/ADR-0007-anti-hallucination-contract.md) — the
  anti-hallucination contract. Conversation design is the user-facing expression
  of ADR-0007.
- [**`prompts/core/ask-never-invent.md`**](../../prompts/core/ask-never-invent.md) —
  the prompt template that shapes every gap question in §3.
