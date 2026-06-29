---
entity_type: job
title: <% tp.file.title %>
id: <% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') %>
company: ""
location: null
remote: null
url: null
status: discovered
applied_at: null
timeline: []
resume_version: null
cover_letter_version: null
interview_prep_version: null
contacts: []
feedback: null
outcome: null
tags: []
confidence: confirmed
sources:
  - kind: manual
    ref: ""
    note: null
$resumeos:
  schema_version: "1.0.0"
---

## Job Description
> Paste or summarize the job posting. What are the key requirements?

## Why This Role
> Why are you applying? What aligns with your career goals?

## Prep Notes
> company research, team structure, tech stack, interview format

## Contacts
> Recruiters, hiring managers, referrals. Add to contacts[] in frontmatter.

## Feedback
> Record any feedback received during the process.

## Timeline
> Log each stage: discovered, applied, screen, interview, offer, reject.
