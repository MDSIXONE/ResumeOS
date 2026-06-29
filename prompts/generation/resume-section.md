---
fragment: resume-section
applies: resume_builder, resume_tailoring Phase 4
inputs: [assembly.json]
outputs: [resume section markdown]
---

# Resume Section Generation

Render one resume section (e.g. Projects, Experience, Skills, Education) from validated assembly
data.

**Per section:**
- **Header** — section title in the target language (zh/en).
- **Items** — each item is a confirmed entity, rendered per the section type:
  - Project/Experience: role • org • dates; 2–4 bullets (from `bullet-rewrite`), each cited.
  - Skills: grouped clusters, only skills present in vault `stack` fields.
  - Education: degree • institution • dates; optional thesis (only if in vault).
- **Ordering** — by relevance score (assembly) for tailored resumes; reverse-chronological for
  master resumes.
- **Language** — match `config.defaults.language`; do not mix languages within a section.
- **Length** — respect `resume_length` (one_page / two_page). If content overflows, drop
  lowest-relevance items first, never compress by inventing.

**Hard rules:**
- Every bullet carries a `[cite: ...]` marker in the source artifact; strip citations from the final
  rendered resume but keep them in `assembly.json` for audit.
- No section may contain a fact without a vault source.
- If a section has zero confirmed items, OMIT the section (do not write a placeholder section that
  implies experience you do not have).

Output Markdown matching the JSON Resume section structure so the DOCX/LaTeX/JSON Resume
exporters can consume it.
