---
fragment: ats-check
inputs: [resume content, optional JD]
outputs: [ATS evaluation]
applies: ADR-0007
---

# ATS (Applicant Tracking System) Check

Evaluate a resume's parseability, keyword coverage, and format safety as an ATS would see it.

**Parseability:**
- Standard section headers present: "Experience," "Education," "Skills," "Projects."
- No tables, multi-column layouts, text boxes, images, or embedded objects that break parser.
- Contact block at the top with name, email, phone, LinkedIn / site -- in a machine-readable
  position.
- Date format consistent (ISO 8601 preferred).

**Keyword coverage:**
- If a JD is provided, extract the JD's hard-skill keywords (languages, frameworks, tools,
  certifications). List: covered (in resume) vs missing (in JD but not in resume).
- If no JD is provided, identify the role the resume targets and suggest the top keywords that
  role typically expects. Do NOT invent keywords the candidate does not have; flag gaps and
  suggest the user confirm whether they have the experience.

**Format issues:**
- File format (Markdown / DOCX / PDF) -- note which format was reviewed.
- Excessive graphics / decorative elements that ATS parsers skip.
- Inconsistent date formatting, missing location, missing email.

**Hard rules:**
- Do NOT invent a keyword. If a keyword is missing, the report says: "The JD expects <X>. This
  resume does not mention it. If you have <X> experience, add it here: <suggested location>."
- Do NOT suggest keyword-stuffing. Recommend genuine inclusion only when the candidate has the
  experience.

This fragment composes with `prompts/core/anti-hallucination.md`. Obey ADR-0007: state only
confirmed facts from the resume text; ask on any gap; never invent experience.
