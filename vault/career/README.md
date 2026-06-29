# Career Vault

This is the single source of truth for all career data.

## Structure

- `projects/` - Technical projects with evidence, metrics, and contributions
- `research/` - Academic papers, publications, and research work
- `competitions/` - Competition participation and achievements
- `internships/` - Internship experiences and responsibilities
- `opensource/` - Open source contributions
- `awards/` - Awards, honors, and recognitions
- `education/` - Educational background and credentials
- `skills/` - Technical and soft skills with proficiency levels

## Rules

1. **Only confirmed facts** can have `confidence: "confirmed"`
2. Every entity must have `sources` array with provenance
3. Use templates from `templates/` directory for consistency
4. Never reference external sources that cannot be verified
5. All frontmatter must validate against schemas in `schemas/`
