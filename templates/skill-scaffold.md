---
name: <% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') %>
version: 0.1.0
description: ""
schema_version: 1.0.0
inputs: []
outputs: []
mcp_tools: []
checkpoints: []
anti_hallucination: true
---

# <% tp.file.title %>

> This is a scaffold for a new ResumeOS Skill plugin. Follow the structure in docs/guides/skill-authoring-spec.md.

## Folder Layout

```
skills/<% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') %>/
├── SKILL.md            # You are here
├── plugin.json         # Manifest (validate against schemas/plugin-manifest.schema.json)
├── README.md           # User-facing documentation
└── prompts/            # Skill-local prompt fragments
    └── *.md
```

## Step 1: Inputs

> What entity types or artifacts does this skill read? Validate against schemas.

## Step 2: Compose Prompts

> Reference prompt fragments from prompts/ (local) and global prompts/.

## Step 3: Work

> What does the model do? State as instructions, not prompt prose.

## Step 4: Outputs

> What does it produce? Where does it write (vault/ or output/)? Validate against schema.

## Step 5: Checkpoints

> If this is a phased pipeline, list checkpoints. Pause for user review at each.

## Anti-hallucination

> Obey ADR-0007: state only confirmed vault facts; ask on any gap; never invent.

## Next Steps

- [ ] Create plugin.json with name, version, description, permissions
- [ ] Write README.md explaining what the skill does and how to use it
- [ ] Add prompt fragments under prompts/
- [ ] Register in skills/registry.yaml
- [ ] Add tests under tests/<skill-name>.contract.md
