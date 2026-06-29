# Skill Authoring Spec

This is the **authoritative spec** for writing a ResumeOS Skill. Every Skill — built-in or
community — follows it. It implements ADR-0004 (plugin system), ADR-0005 (internal structure),
ADR-0007 (anti-hallucination), and ADR-0009 (prompt modularity).

> **Reference implementation:** [`skills/resume_tailoring/`](../../skills/resume_tailoring/) — read
> it alongside this spec.

---

## 1. Folder layout (fixed)

```
skills/<skill-name>/
├── SKILL.md            # Agent Skill standard: frontmatter + orchestration
├── plugin.json         # Manifest (validates against schemas/plugin-manifest.schema.json)
├── README.md           # User-facing doc
└── prompts/            # Skill-local prompt fragments (.md); compose global prompts/ too
    └── *.md
```

Do not add files outside this layout without an ADR. The loader expects exactly this.

---

## 2. `plugin.json` (manifest)

Required keys: `name`, `version`, `description`. See
`schemas/plugin-manifest.schema.json` for the full contract. Key fields:

```json
{
  "name": "<skill-name>",
  "version": "0.1.0",
  "description": "<one line>",
  "depends_on": ["resume_builder@1.0.0", "schema@1.0.0"],
  "hooks": ["onVaultChange"],
  "mcp_tools": ["github:get_commits", "browser:fetch"],
  "permissions": {
    "read":  ["vault/career/**", "schemas/**"],
    "write": ["output/**"],
    "deny":  ["vault/.obsidian/**", "output/** as input"]
  }
}
```

- `permissions.write` may point at `vault/` only for **enrichment** skills
  (`career_collector`, `career_builder`, `career_update`, `job_tracker`). Generator skills write
  only to `output/`.
- **Never** grant a generator skill write access to `vault/` (ADR-0001, ADR-0010).

---

## 3. `SKILL.md` frontmatter (required keys)

```yaml
---
name: <skill-name>            # matches folder; runtime-namespace resumeos:<skill-name>
version: 0.1.0
description: <one line>
schema_version: 1.0.0         # vault schema version this skill targets (ADR-0002)
inputs: [project, job]        # entity types this skill reads
outputs: [derived-resume]     # entity types or derived kinds this skill writes
mcp_tools: []                 # optional; must match plugin.json
checkpoints: [research, gap_analysis, assembly]   # only for phased-pipeline skills (ADR-0006)
anti_hallucination: true      # ADR-0007 contract — always true for built-in skills
---
```

---

## 4. `SKILL.md` body — orchestration, not prompt text

The body describes **steps**. Each step:

1. **Inputs** — names the entity types / artifacts it reads and validates them against schemas.
2. **Compose prompts** — references fragments from `prompts/` (local) and global `prompts/`:
   `Compose: prompts/analysis/gap-classification.md + prompts/core/anti-hallucination.md`.
3. **Work** — what the model does, stated as an instruction, not as the prompt itself.
4. **Outputs** — what it produces and where (vault path or `output/` path); validate against schema.
5. **Checkpoints** — if a step is a checkpoint, say so and describe what the user reviews
   (ADR-0006).
6. **Anti-hallucination** — for any generation step, include the line:
   `Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.`

**Do not inline prompt prose in the body.** Prompt prose lives in `prompts/*.md`. The body says
*which* prompts to compose and *how* to use their output.

---

## 5. Prompts (`prompts/*.md`)

A prompt fragment is a small Markdown file with a frontmatter block declaring inputs/outputs,
then the prompt prose:

```markdown
---
fragment: bullet-rewrite
inputs: [assembly.json]
outputs: [rewritten-bullets]
applies: ADR-0007
---
You are rewriting resume bullets. Rules:
- You may rephrase, condense, or reorder a CONFIRMED fact.
- You may NOT add metrics, responsibilities, or technologies not present in the source bullet.
- Start every bullet with a strong action verb.
- Quantify ONLY if the source already contains the number.
...
```

Global fragments live in `prompts/` at repo root; skill-local fragments live in
`skills/<skill>/prompts/`. Prefer global fragments for reusable behavior.

---

## 6. Anti-hallucination checklist (every generator skill)

- [ ] Every output fact traces to a `entity_id:field` citation.
- [ ] `confidence: inferred` or `missing` facts trigger an **ask**, not a guess.
- [ ] Rewording never adds metrics/responsibilities/technologies.
- [ ] An uncitable bullet is a build failure, not a warning.
- [ ] `anti_hallucination: true` is set in SKILL.md frontmatter.

---

## 7. Checkpoint skills (phased pipeline)

If your skill is a phased pipeline (ADR-0006):
- list phases and their artifacts in the body,
- declare `checkpoints:` in frontmatter,
- write each phase's artifact schema under `schemas/artifacts/<phase>.schema.json` (or reuse
  existing ones),
- pause at each checkpoint and present the artifact for user review,
- never start phase N+1 until phase N's checkpoint is approved.

---

## 8. Tests

Add a behavior contract under `tests/<skill-name>.contract.md` describing:
- happy path (vault fixture → expected output),
- anti-hallucination path (vault with a gap → skill must ask, not invent),
- checkpoint path (for pipeline skills).

Use the fixtures in `examples/` as test inputs.

---

## 9. Registry

Add the skill to `skills/registry.yaml`:

```yaml
- name: <skill-name>
  version: 0.1.0
  path: skills/<skill-name>
  enabled: true
  depends_on: [...]
```

---

## 10. Quality bar

- A new contributor reads one Skill + this spec and can write another.
- The loader can validate the skill without running it.
- No prompt prose is duplicated across skills (share via global `prompts/`).
- Permissions are least-privilege.
- The skill never edits `output/` as if it were canonical.
