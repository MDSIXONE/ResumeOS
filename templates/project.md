---
entity_type: project
title: <% tp.file.title %>
id: <% tp.file.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') %>
status: planned
timeline:
  start: <% tp.date.now("YYYY-MM-DD") %>
  end: null
  ongoing: false
role: ""
team_size: null
company: null
competition: null
stack:
  hardware: []
  software: []
  protocol: []
  algorithm: []
  dataset: []
metrics: []
contribution: ""
ats_keywords: []
interview_questions: []
evidence:
  github: null
  paper: null
  patent: null
  presentation: null
  images: []
  demo: null
related: []
tags: []
confidence: confirmed
sources:
  - kind: manual
    ref: ""
    note: null
$resumeos:
  schema_version: "1.0.0"
---

## Background
> What was the context? When did this project start and why?

## Problem
> What specific problem were you trying to solve?

## Goal
> What was the target outcome or success metric?

## Architecture
> How was the system designed? What were the key components?

## Workflow
> How did the team work together? What was the development process?

## Challenges
> What were the main technical or organizational obstacles?

## Solutions
> How did you overcome each challenge? What trade-offs did you make?

## Metrics (detail)
> Expand on the metrics in frontmatter. How were they measured? What was the baseline?

## Contribution
> What did YOU specifically do? Expand on the one-line summary in frontmatter.

## Lessons Learned
> What would you do differently? What did this project teach you?

## STAR Story
> Situation, Task, Action, Result — a concise narrative for interviews.

## Future Improvements
> If you had more time or resources, what would you add or change?

## Related Notes
> Use [[wikilinks]] to connect to related projects, skills, competitions, jobs.
