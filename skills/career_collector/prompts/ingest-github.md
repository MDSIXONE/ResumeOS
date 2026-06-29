---
fragment: ingest-github
inputs: [github-repo-ref]
outputs: [extracted-facts]
applies: ADR-0007
---

Extract structured career facts from a GitHub repository.

Use MCP tools `github:get_commits`, `github:get_prs`, and `github:get_releases` to retrieve
the contribution history.

Rules:

- For each repository, summarize: languages used, notable commits, merged PRs, published releases,
  and issue discussions.
- Map each fact to its likely entity type: `project`, `opensource`, `skill`.
- Tag every fact `confidence: inferred`. Contribution level and impact are approximations.
- Record the source token for every fact (`[src:github:commit:<sha>]`,
  `[src:github:pr:<number>]`, `[src:github:release:<tag>]`).
- If the repo is empty, private, or returns an error, report the failure — do not invent
  content.
- Do not infer metrics (stars, contributors, download counts) unless the API returns them
  explicitly.
- Emit facts as a flat bullet list with source tags.
