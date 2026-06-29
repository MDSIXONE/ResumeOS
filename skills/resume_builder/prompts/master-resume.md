---
fragment: master-resume-section
inputs: [validated-master-entities]
outputs: [master resume sections]
applies: ADR-0007
---

# Master Resume Section Generation

Render one resume section (Projects, Experience, Education, Skills, Awards, Publications, etc.)
from the confirmed vault entity index. This is for a master resume -- no JD, no tailoring ranking.

**Per section:**
- **Header** -- section title in the target language (zh/en).
- **Items** -- each item is a confirmed entity, rendered per the section type:
  - Project / Experience / Research / Competition / Internship / Opensource:
    title, org (if any), dates; 2-4 bullets from the entity's `metrics` and `contribution`,
    each cited as `entity_id:field`.
  - Skills: grouped clusters, ONLY from vault `stack` fields. No inferred skills.
  - Education: degree, institution, dates; thesis only if present in the vault entity.
  - Awards / Publications / Certifications: title, issuer/venue, date, citation.
- **Ordering** -- reverse-chronological by start date within each section.
- **Language** -- match `config.defaults.language`; do not mix languages within a section.
- **Length** -- respect `resume_length` (one_page / two_page). If content overflows, drop oldest
  entries first. Never compress by inventing.

**Style variants:**
- `industry`: concise, impact-oriented bullets. Lead with action verb + metric.
- `academic`: include publications, coursework, thesis details. More room for breadth.
- `research`: emphasize methods, datasets, tools. Group by research area if helpful.

**Hard rules:**
- Every bullet must carry a `[cite: entity_id:field]` marker. Strip citations from the final
  rendered output but retain them internally for provenance audit.
- No section may contain a fact that is not confirmed in the vault.
- If a section has zero confirmed items, OMIT the section entirely. Do not render a placeholder.

**Provenance check before emitting each item:**
1. Does every claim trace to a vault field? If no, discard.
2. Did I add any number not in the source? If yes, discard.
3. Is the action verb honest about the candidate's role? If no, fix or discard.

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: state only
confirmed vault facts; ask on any gap; never invent.
