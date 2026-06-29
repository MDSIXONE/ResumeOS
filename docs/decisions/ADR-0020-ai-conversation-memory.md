# ADR-0020: AI Conversation Memory — Shared, Entity-Scoped Store of User Answers

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS lead, Runtime track
- **Related:** ADR-0001, ADR-0007, ADR-0012, ADR-0014
- **Supersedes:** none
- **Superseded by:** none

## Context

The Phase 2 conversation design (`docs/ux/conversation-design.md`, §1 line 27) mandates
"never repeat an answered question" and "remember previous answers." The conversation
examples in §3 demonstrate this: once a user answers "team size: 4" for `Project:PX4-UAV`
during one import, no subsequent Skill should re-ask the same question for the same entity.

Today there is no shared store for past Q&A across Skills or across runs. Each Skill would
independently ask "team size?" for the same project because `career_collector` already asked
and wrote the answer to the vault note, but `resume_tailoring` or `interview` have no
mechanism to check that answer without parsing the note's full content, and if the field was
asked but the vault write was deferred (the answer was captured but not yet merged), the
information exists nowhere except in the closed session.

The Phase 2 review called this "the most valuable thing in all of ResumeOS." The problem is
not hypothetical — it is the single fastest way to erode trust. A system that asks the same
question twice signals that it did not listen the first time.

Three constraints shape the solution. First, ADR-0007 (lines 28–30) mandates: *"A Skill may
only state a fact that exists in the vault and is validated against its schema."* Memory
stores only USER-CONFIRMED answers — never AI inferences, never fabrications. Second,
ADR-0012 establishes `vault/.library/memory/` as the home (ADR-0012, line 52). Third,
ADR-0014 (line 101) defines `KnowledgeUpdated` events keyed by `entity_id`; memory is keyed
by the same entity refs so it stays aligned with the Knowledge Index.

## Decision

A shared **AI Conversation Memory** at `vault/.library/memory/conversation.jsonl`, an
append-only JSONL file keyed by entity + topic. Memory captures user-confirmed answers at the
moment they are given, before they become vault facts. It is the mechanism that enforces
"never repeat questions" across Skills and across runs.

### Location

```
vault/.library/
├── cache/              # ADR-0011: transient OCR/hash/parse cache
├── index/              # ADR-0012: knowledge-index.json + .stale.json
├── embeddings/         # ADR-0013: <entity-id>.vec files
├── memory/             # this ADR: conversation.jsonl
└── events.jsonl        # ADR-0014: event bus audit log
```

The path is git-ignored by default (rule 8). The location is consistent with ADR-0012's
consolidated `.library/` runtime data root (ADR-0012, lines 41–54).

### Entry format

Each line in `conversation.jsonl` is one JSON object:

```json
{
  "time": "2026-06-29T09:14:00+08:00",
  "skill": "career_collector",
  "question": "How large was the team, including yourself?",
  "answer": "4",
  "entity_refs": [
    {"entity_type": "project", "entity_id": "px4-uav"}
  ],
  "topic": "team_size",
  "confidence": "confirmed",
  "superseded_by": null
}
```

| Field | Type | Purpose |
|---|---|---|
| `time` | ISO 8601 | When the user answered. Used for "latest wins" on duplicate lookups. |
| `skill` | string | Which Skill asked the question. Audit and debugging. |
| `question` | string | The exact question asked. Enables "have we asked this before?" matching. |
| `answer` | string | The user's verbatim answer. |
| `entity_refs[]` | array | `{entity_type, entity_id}` — same keys as ADR-0012 and ADR-0014. Scopes the answer. |
| `topic` | string | Short key (e.g. `team_size`, `role`, `tech_stack`, `doi`). Scopes within an entity. |
| `confidence` | string | Always `confirmed`. Memory stores only user answers (rule 7, ADR-0007). |
| `superseded_by` | string/null | If the user corrected this answer, points to the replacement entry's `time`. |

### Concrete rules

1. **Location and persistence.** `vault/.library/memory/conversation.jsonl` (JSONL, one
   entry per line). Git-ignored by default. **Memory is the ONLY runtime artifact under
   `.library/` that is NOT fully rebuildable from the vault.** The index, embeddings, and
   cache are all derivable from `vault/career/**`. Memory captures the user's spoken answers
   *before* they become vault facts — if the vault note was never written (the answer was
   given but the import was cancelled), the answer exists only in memory. Deleting
   `conversation.jsonl` loses conversation history. For a personal system this is acceptable;
   the user may opt in to committing `vault/.library/memory/` via
   `resumeos.config.yaml: runtime.memory.commit: true` (default `false`). Document this
   trade-off explicitly.

2. **JSONL format.** Append-only. One entry per line. Newlines are event boundaries. This
   avoids the load-all-or-nothing problem of a single JSON object and preserves write
   atomicity (each `resume` invocation appends; concurrent appends are safe with file-level
   locking). A Skill reads the file by scanning lines and filtering in memory — the file is
   expected to stay small (hundreds of entries per year, not millions).

3. **Shared across Skills.** Before asking the user any question, every Skill queries memory:
   "have we asked `{entity_id}` + `{topic}` before?" If a `confirmed` answer exists, reuse
   it; do not re-ask. This is the mechanism for "never repeat questions" (conversation-design
   §1, line 27). The lookup is:

   ```
   memory.latest(entity_id=<id>, topic=<topic>) → answer or null
   ```

   If `null`, the Skill asks. If an answer is returned, the Skill may (a) use it silently,
   (b) show "Reusing previous answer: team size = 4" as a status line, or (c) offer the user
   a chance to correct ("Is this still 4, or has it changed?"). Option (c) is the default
   for high-signal fields (metrics, role, dates); option (b) for low-signal fields (stack
   additions, collaborator names).

4. **Scoped by entity + topic.** The same question about different entities produces
   different memory entries. Asking "team size?" for `Project:PX4-UAV` and answering "4" does
   NOT answer "team size?" for `Project:FleetOps`. The `entity_refs[]` + `topic` compound
   key is the deduplication scope. A `topic` is a short, normalized key (e.g. `team_size`,
   not the full question text) so that two Skills asking the same conceptual question in
   different wording still match.

5. **Append-only, never edit.** Memory entries are immutable once written. If the user
   corrects a previous answer ("actually, the team was 5, not 4"), the runtime appends a new
   entry with the same `entity_id` + `topic`, a later `time`, and sets
   `superseded_by: null` on the new entry. The old entry's `superseded_by` field is updated
   to point to the new entry's `time` — this is the ONLY mutation to an existing entry. The
   runtime reads the latest entry by `time` for a given `entity_id` + `topic` combination.
   Correction history is preserved for audit.

6. **Write timing.** Memory is written AFTER the user confirms the answer and BEFORE the
   vault note is updated. The sequence: user answers → runtime appends to memory → runtime
   proceeds with Skill logic (vault write may follow, may be deferred). Memory is the
   capture layer; the vault note is the persistence layer. If the vault write fails or is
   cancelled, the answer still exists in memory and will be offered on the next relevant
   query.

7. **Anti-hallucination (ADR-0007).** Memory entries are USER answers ONLY. The `confidence`
   field is always `confirmed`. An AI-inferred value (e.g. "team size probably 5 based on
   similar projects") NEVER enters memory. Inferred values stay in the staged note as
   `confidence: inferred` (ADR-0007, line 47) and are presented to the user for
   confirmation. Only when the user confirms ("yes, 5") does the answer enter memory as
   `confidence: confirmed`. This is a hard rule: if a code path writes a memory entry with
   `confidence != "confirmed"`, it is a bug.

8. **Privacy: local, opt-in commit.** Memory is local to the user's machine and git-ignored
   by default. It contains the user's spoken answers, which may include personal information
   (team sizes, role details, project specifics). The user MAY opt to commit
   `vault/.library/memory/` to git via `resumeos.config.yaml: runtime.memory.commit: true`.
   Default is `false`. The `.gitignore` template respects this flag (the runtime generates
   `.gitignore` entries conditionally on config).

9. **No expiry, but supersession.** Memory entries do not expire. A user's answer to "team
   size?" from two years ago is still valid unless corrected. The `superseded_by` field
   chains corrections: the runtime reads the latest non-superseded entry for a given
   `entity_id` + `topic`. A query for `entity_id=px4-uav, topic=team_size` returns the
   entry with the latest `time` where `superseded_by == null` (or the entry pointed to by
   the terminal `superseded_by` link).

10. **Relation to events (ADR-0014).** Memory writes MAY emit a `MemoryUpdated` event
    (optional, for the dashboard "recent answers" widget or for community Skills that react
    to user input). This is NOT required — memory writes are frequent and low-latency, and
    making every write an event would flood the bus. The default is silent writes; a Skill
    that wants `MemoryUpdated` subscribes and the runtime emits for writes that match the
    Skill's declared entity scope.

## Consequences

- **Positive:** "Never repeat questions" is enforced across all Skills and across all runs.
  A user who answered "team size: 4" for `Project:PX4-UAV` during `career_collector` will
  not be asked again by `resume_tailoring`, `interview`, or any future Skill. This is the
  core trust mechanism identified in the Phase 2 review.
- **Positive:** Shared across Skills — no siloed per-Skill memory. A community Skill that
  subscribes to `CareerEntity` events can query the same memory as built-in Skills, keeping
  the ecosystem unified.
- **Positive:** Append-only JSONL is crash-safe. A mid-write crash loses at most one
  partial line; the rest of the file is intact. No transaction log needed.
- **Positive:** Anti-hallucination by construction (rule 7). Memory cannot contain
  fabricated answers because the only write path is a confirmed user response. This
  eliminates an entire class of "AI remembered wrong" bugs.
- **Negative:** Memory is not fully rebuildable from the vault (rule 1). A fresh clone of
  `vault/career/` without `.library/memory/` loses conversation history. Accepted for a
  personal system and mitigated by the opt-in commit flag. The vault is still SSOT for
  *career knowledge*; memory is SSOT for *conversation history* — a distinct, supplementary
  record.
- **Negative:** Linear scan of JSONL for lookups. Accepted at expected scale (hundreds of
  entries per year). If memory grows past ~10,000 entries, an in-memory index (loaded at
  session start) is the upgrade path; the JSONL format stays.
- **Neutral:** Memory is write-mostly-read. The write path (append on user answer) is the
  hot path; the read path (query before asking) is invoked only at the conversation gate.
  This asymmetry matches the usage pattern: many answers, fewer re-ask checks.

## Alternatives considered

- **Per-Skill memory (each Skill has its own memory store).** Rejected: siloed. `career_collector`
  asks "team size?" and records it; `resume_tailoring` has its own memory and asks again.
  This is the exact problem this ADR exists to solve. Shared memory is the whole point.

- **Memory as vault notes (store Q&A in `vault/career/_memory/*.md`).** Rejected: pollutes
  the vault SSOT with conversation data. Memory is not career knowledge — it is a runtime
  record of user interaction. Storing it as notes clutters Graph View, bloats git, and
  conflates "what the user did" with "what the user accomplished." The vault note for
  `Project:PX4-UAV` should contain confirmed facts (team size, role, dates); the
  conversation about those facts belongs in memory, not in the note.

- **Memory as a single JSON object (keyed by entity+topic).** Rejected: not append-friendly.
  Every write requires loading the entire file, mutating, and rewriting. Concurrent Skills
  or a crash mid-write corrupts the file. JSONL append-only avoids this.

- **Memory in a cloud service (synced across devices).** Rejected: violates ADR-0008
  local-first (line 22). The user's conversation history is personal and should not leave
  the machine without explicit opt-in. Cloud sync is a future concern, out of scope.

- **No memory (re-ask every time).** Rejected: violates conversation-design §1 (line 27)
  and the Phase 2 review's "most valuable thing" finding. Re-asking destroys trust and
  wastes user time. The system would feel stateless — the opposite of an intelligent
  assistant.

- **Memory stores AI inferences too (with `confidence: inferred`).** Rejected: violates
  ADR-0007 (lines 28–30). Memory must contain only user-confirmed answers. Allowing
  AI-inferred values into memory creates a "AI said so" feedback loop where an inference
  from one run influences a question in the next run, compounding errors. The boundary is
  hard: user confirms → memory; AI infers → staged note, not memory.
