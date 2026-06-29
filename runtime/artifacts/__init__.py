"""ResumeOS Artifacts — the universal output contract of Importers.

An Artifact is a normalized, source-agnostic representation of imported
material. Importers (Sprint 2.5) produce Artifacts; downstream Skills
(Career Builder, Sprint 4) consume them. Skills NEVER see source files
or know whether an Artifact came from a PDF, a git repo, or a README.

Design rules (user directive, Sprint 2 review):
    1. Artifact is the ONLY thing an Importer outputs.
    2. Importers never write Markdown — that is a downstream Skill's job.
    3. Artifacts are deterministic and zero-AI (no LLM in the Importer).
    4. Every Artifact carries provenance (source file hash + path).
    5. Artifacts serialize to JSON for persistence / event payloads.

No ADR is added for this layer — it is an implementation detail of
ADR-0019 (Importer) encoded in code and tests, per the project rule
"stop writing ADRs; code implements ADRs."
"""

from runtime.artifacts.base import Artifact, ArtifactProvenance

__all__ = ["Artifact", "ArtifactProvenance"]
