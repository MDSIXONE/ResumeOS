# ADR-0013: Embedding Cache — Per-Entity Vector Projection for Semantic Search

- **Status:** Accepted
- **Date:** 2026-06-29
- **Deciders:** ResumeOS lead, Runtime track
- **Related:** ADR-0008, ADR-0012, ADR-0014
- **Supersedes:** none
- **Superseded by:** none

## Context

As the vault grows past a few dozen entities, users will ask semantic questions — "which
projects relate to ROS?", "what experience involves multi-agent coordination?" — that keyword
search over the Knowledge Index (ADR-0012) cannot answer well. The index stores tags and
`key_fields` per entity (ADR-0012, lines 64–94), which supports exact-match filtering but not
synonym or concept retrieval. Scanning every note's full text per semantic query is O(n) in
vault size and repeats work that a precomputed vector representation would make O(1) per query
after an initial dot-product pass.

Three constraints shape the solution. First, ADR-0008 (lines 22–23) mandates local-first and
zero-MCP operation: *"ResumeOS works fully with zero MCP servers."* The embedding model is an
MCP adapter (`embeddings:generate` or equivalent), not a built-in dependency. The system must
work without embeddings and degrade gracefully to keyword search over the Knowledge Index.

Second, ADR-0012 (lines 41–54) establishes `vault/.library/` as the consolidated runtime data
root with typed subfolders (`cache/`, `index/`). This ADR adds `embeddings/` as a sibling,
keyed by the same entity ids as the Knowledge Index so that a Skill can go from
`knowledge-index.json` → `<entity-id>.vec` without a translation step.

Third, the vault is SSOT (ADR-0001). Embeddings are derived, rebuildable, and never canonical.
A deleted `.vec` file is regenerated from the vault on the next `resume index --embed` or the
next lazy query — never a data-loss event.

## Decision

An **Embedding Cache** at `vault/.library/embeddings/<entity-id>.vec`, one file per entity, in
a model-agnostic JSON format. The cache is a per-entity vector projection of vault content —
read by semantic search, written by the embedding worker, and rebuildable from the vault at any
time.

### Location

```
vault/.library/
├── cache/              # ADR-0011: transient OCR/hash/parse cache
├── index/              # ADR-0012: knowledge-index.json + .stale.json
├── embeddings/         # this ADR: <entity-id>.vec files
├── memory/             # ADR-0020: conversation.jsonl
└── events.jsonl        # ADR-0014: event bus audit log
```

The path is git-ignored and rebuildable, consistent with ADR-0012 §Location (lines 41–57).

### Per-entry format

Each `.vec` file is a single JSON object:

```json
{
  "entity_id": "px4-uav",
  "entity_type": "project",
  "model": "text-embedding-3-small",
  "model_version": "2024-01-25",
  "dim": 1536,
  "generated_at": "2026-06-29T09:14:00+08:00",
  "text_hash": "sha256:3b4c...",
  "vec": [0.0123, -0.0456, ...]
}
```

| Field | Type | Purpose |
|---|---|---|
| `entity_id` | string | Same id as `knowledge-index.json` (ADR-0012, line 70). Enables direct join. |
| `entity_type` | string | `project`, `award`, `research`, `skill`, `job`. |
| `model` | string | Embedding model name from the MCP adapter. |
| `model_version` | string | Model snapshot date or adapter-reported version. |
| `dim` | integer | Vector dimensionality; enables cross-file validation. |
| `generated_at` | ISO 8601 | Timestamp of generation. |
| `text_hash` | string | SHA-256 of the embedded source text. Stale detection key (rule 5). |
| `vec` | number[] | The embedding vector. |

JSON (not binary) is inspectable, git-diff-friendly before ignoring, and parsable by any
language without SDK dependencies. The file is named `<entity-id>.vec` (e.g. `px4-uav.vec`)
so it is trivially listable and individually loadable.

### Concrete rules

1. **Location and naming.** `vault/.library/embeddings/<entity-id>.vec`. One file per entity.
   The entity id matches the Knowledge Index (ADR-0012) — no separate key namespace. The file
   is git-ignored and rebuildable (ADR-0012, lines 56–57).

2. **Model-agnostic format.** The `model` + `model_version` fields record which model produced
   the vector. A model swap invalidates all `.vec` files (the runtime compares `model` against
   the configured adapter; mismatch triggers regeneration). The runtime NEVER mixes vectors
   from different models in one cosine similarity pass — mismatched dimensions or models are
   a hard error, not a silent ranking.

3. **Optional (ADR-0008).** With zero MCP or no embedding adapter configured, the
   `embeddings/` directory is empty. Semantic search degrades to keyword search over the
   Knowledge Index (ADR-0012 `key_fields` + `tags`). The system works; it just lacks semantic
   ranking. No Skill crashes, no user-facing error.

4. **Stale detection.** Each `.vec` stores `text_hash` — SHA-256 of the embedded source text
   (the entity note's full content or a configured summary projection). On `KnowledgeUpdated`
   event (ADR-0014, line 101), the runtime recomputes the note's text hash; if it differs
   from the `.vec`'s `text_hash`, the entry is stale and is regenerated on the next semantic
   query or the next `resume index --embed`.

5. **Rebuild trigger.** `resume index --embed` regenerates all embeddings (full rebuild).
   Lazy per-entity regeneration on semantic query is allowed: the runtime checks staleness
   for the queried entity's `.vec`, regenerates if stale, then proceeds with similarity
   search. This keeps cold-start fast and avoids regenerating 500 vectors when the user
   asked about one entity.

6. **Skills declare the MCP tool, not consume it at read time.** A Skill that produces
   embeddings declares `mcp_tools: ["embeddings:generate"]` in `plugin.json` (ADR-0008,
   line 24). The search Skill reads `.vec` files directly — it does not need the MCP tool
   at read time because vectors are precomputed. This means semantic search works even if
   the embedding adapter is offline at query time, so long as `.vec` files exist from a
   prior build.

7. **Privacy: local preferred.** Embeddings are derived from local vault content. If a cloud
   embedding API is used via MCP (e.g. OpenAI `text-embedding-3-small` over HTTPS), the
   adapter configuration MUST warn the user that vault content is being sent to an external
   service. Local embedding models (e.g. `all-MiniLM-L6-v2` via a local MCP adapter) are
   the preferred default. This is a direct application of ADR-0008's local-first principle
   (lines 22–23).

8. **No vector DB in v1.** Cosine similarity is computed in-process over the loaded `.vec`
   files. At personal-vault scale (<1000 entities, each vector ~1536 dims) this is sub-second
   on commodity hardware. A vector DB (FAISS, Chroma, Qdrant) is a documented future option
   for when the vault exceeds ~5000 entities or when real-time similarity over a streaming
   corpus is needed. The Skill contract (load `.vec` files, compute similarity) stays
   stable; only the backend changes. This mirrors ADR-0012's JSON→SQLite upgrade path
   (ADR-0012, lines 135–138).

9. **Event-driven invalidation.** On `KnowledgeUpdated` (ADR-0014), the embedding worker
   (a runtime component, not a Skill) checks staleness and marks dirty entities in
   `vault/.library/embeddings/.stale.json`. This mirrors the Knowledge Index stale flag
   (ADR-0012, lines 115–119). Subsequent `resume index --embed` or lazy query picks up
   the dirty list. The embedding worker does NOT emit events — it *consumes*
   `KnowledgeUpdated`.

## Consequences

- **Positive:** O(1) per-entity vector lookup for semantic search — `resume_tailoring` can
  rank entities by vector similarity to a JD, the dashboard can cluster projects by topic,
  and the user can ask "find related work" without a full vault scan.
- **Positive:** Model-agnostic format means switching embedding providers (OpenAI → local →
  another cloud) is a config change + rebuild, not a code change. The `model` field in each
  `.vec` makes mixed-model bugs impossible to miss.
- **Positive:** Optional (ADR-0008). Users who never configure an embedding adapter still get
  full keyword search via the Knowledge Index. Zero-MCP operation is preserved with no feature
  cliff — semantic ranking is additive, not foundational.
- **Positive:** JSON format is inspectable and debuggable. A user can `cat` a `.vec` file to
  verify its content, unlike a binary `.npy` or a FAISS index.
- **Negative:** Per-file overhead (one JSON file per entity) vs. a single consolidated file.
  Accepted: at <1000 entities the filesystem handles this easily, and per-file granularity
  enables lazy regeneration without rewriting a monolith.
- **Negative:** Cosine similarity over all loaded vectors is O(n) in entity count per query.
  Accepted at <1000 entities; vector DB is the documented upgrade path (rule 8).
- **Neutral:** The embedding worker is a new runtime component. It follows the same pattern
  as the indexer (ADR-0012): consumes events, writes to `.library/`, never reads from another
  runtime cache.

## Alternatives considered

- **Binary `.npy` format.** Rejected: not inspectable without Python/NumPy, not
  git-diff-friendly, and couples the runtime to a specific binary layout. JSON with a `vec`
  array is slightly larger on disk but readable by any tool and any language.

- **Single `embeddings.json` (load-all-or-nothing).** Rejected: a 500-entity file with 1536-dim
  vectors is ~3 MB of JSON; loading and deserializing the whole file for a single-entity
  query is wasteful. Per-file layout enables lazy load and per-entity staleness.

- **Cloud-only embeddings (no local adapter option).** Rejected: violates ADR-0008 local-first
  (line 22). The user's vault content should not require an external API to be searchable.
  Cloud is an *option* via MCP adapter; local is the *default*.

- **Vector DB (FAISS/Chroma) in v1.** Rejected: over-engineered for <1000 entities at
  personal-vault scale. Adds a binary runtime dependency, a non-inspectable artifact, and a
  new failure mode (index corruption). JSON `.vec` files + in-process cosine cover v1; the
  vector DB remains a documented upgrade path (rule 8) following the same pattern as
  ADR-0012's JSON→SQLite path.

- **Embeddings stored as vault notes.** Rejected: pollutes the vault SSOT with derived data.
  Embeddings are not career knowledge — they are a runtime projection. Storing them as notes
  clutters Graph View, bloats git, and violates ADR-0001's vault-as-canonical rule.
