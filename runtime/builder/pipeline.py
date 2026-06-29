"""Builder Pipeline -- the core Career Builder orchestration.

Wires together: Planner -> Retriever -> LLM -> Draft -> Validator
-> Merger -> MarkdownWriter -> EventBus -> KnowledgeIndex.

Per the user's 3 principles:
    Principle 1: Markdown is just a View (KnowledgeObject -> Writer)
    Principle 2: Builder never directly writes files (uses KnowledgeWriter)
    Principle 3: LLM always outputs Draft (Draft -> Validator -> Knowledge)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from runtime.artifacts.base import Artifact
from runtime.event_bus import EventBus
from runtime.knowledge.conflict import Conflict
from runtime.knowledge.draft import Draft
from runtime.knowledge.object import KnowledgeObject
from runtime.knowledge.provenance import KnowledgeProvenance
from runtime.knowledge.writer import KnowledgeWriter
from runtime.knowledge_index import KnowledgeIndex
from runtime.llm_provider import LLMProvider

from runtime.builder.merger import Merger
from runtime.builder.planner import Planner
from runtime.builder.retriever import Retriever
from runtime.builder.validator import Validator


@dataclass
class BuilderResult:
    """Result of a BuilderPipeline run.

    Fields:
        success: Whether the pipeline completed successfully.
        knowledge_object: The produced KnowledgeObject (or None on failure).
        draft: The last Draft produced (even on validation failure).
        written_path: Path to the Markdown file written.
        events_published: List of event types published during the run.
        conflicts: List of conflicts detected during merge.
        error: Error message if the pipeline failed.
    """

    success: bool = False
    knowledge_object: Optional[KnowledgeObject] = None
    draft: Optional[Draft] = None
    written_path: Optional[Path] = None
    events_published: List[str] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)
    error: str = ""


class BuilderPipeline:
    """Full Career Builder pipeline.

    Flow:
        Plan -> Retrieve -> LLM -> Draft -> Validate -> Merge -> Write
        -> Events -> KnowledgeIndex.update()
    """

    def __init__(
        self,
        planner: Planner,
        retriever: Retriever,
        llm: LLMProvider,
        validator: Validator,
        merger: Merger,
        writer: KnowledgeWriter,
        event_bus: EventBus,
        knowledge_index: Optional[KnowledgeIndex] = None,
    ) -> None:
        self.planner = planner
        self.retriever = retriever
        self.llm = llm
        self.validator = validator
        self.merger = merger
        self.writer = writer
        self.event_bus = event_bus
        self.knowledge_index = knowledge_index

    def run(self, artifact: Artifact, vault_root: Path) -> BuilderResult:
        """Run the full pipeline: Artifact -> KnowledgeObject -> Markdown.

        Args:
            artifact: The input Artifact to process.
            vault_root: Root of the Obsidian vault (knowledge target).

        Returns:
            BuilderResult with success/failure, outputs, and events.
        """
        events_published: List[str] = []

        # 1. Plan
        plan = self.planner.plan(artifact)

        # 2. Retrieve (check for existing entity)
        retrieved = self.retriever.retrieve(plan, vault_root)

        # 3. Build prompt for the LLM
        prompt = self._build_prompt(artifact, plan, retrieved)

        # 4. Call LLM to get raw YAML output
        try:
            raw_output = self.llm.generate(prompt)
        except Exception as exc:
            return BuilderResult(
                success=False,
                error=f"LLM generation failed: {exc}",
                events_published=events_published,
            )

        # 5. Parse the YAML output into draft fields
        draft_fields = self._parse_yaml_output(raw_output)

        # Ensure entity_type is in fields (schema requires it)
        if "entity_type" not in draft_fields:
            draft_fields["entity_type"] = plan["entity_type"]

        # 6. Create Draft
        draft = Draft(
            entity_type=plan["entity_type"],
            entity_id=plan["entity_id"],
            fields=draft_fields,
            raw_output=raw_output,
            provenance=KnowledgeProvenance(
                generated_by="career_builder",
                llm=self.llm.name,
                prompt="career.project.v1",
                artifact=artifact.source_sha256,
            ),
            attempt=1,
        )

        # 7. Publish KnowledgeDraftCreated event
        events_published.append("KnowledgeDraftCreated")
        self.event_bus.publish(
            "KnowledgeDraftCreated",
            payload={
                "entity_type": draft.entity_type,
                "entity_id": draft.entity_id,
                "attempt": draft.attempt,
            },
            source_skill="career_builder",
        )

        # 8. Validate
        draft = self.validator.validate(draft)

        # 9. Retry up to 3 times if validation fails
        max_attempts = 3
        while not draft.is_valid and draft.attempt < max_attempts:
            draft.attempt += 1

            # Re-prompt with validation errors
            retry_prompt = self._build_retry_prompt(
                artifact, plan, retrieved, draft.validation_errors
            )
            try:
                raw_output = self.llm.generate(retry_prompt)
            except Exception:
                break

            draft_fields = self._parse_yaml_output(raw_output)
            if "entity_type" not in draft_fields:
                draft_fields["entity_type"] = plan["entity_type"]

            draft = Draft(
                entity_type=plan["entity_type"],
                entity_id=plan["entity_id"],
                fields=draft_fields,
                raw_output=raw_output,
                provenance=draft.provenance,
                attempt=draft.attempt,
            )

            # Re-publish draft event for the retry
            events_published[-1] = "KnowledgeDraftCreated"  # keep single entry
            self.event_bus.publish(
                "KnowledgeDraftCreated",
                payload={
                    "entity_type": draft.entity_type,
                    "entity_id": draft.entity_id,
                    "attempt": draft.attempt,
                },
                source_skill="career_builder",
            )

            draft = self.validator.validate(draft)

        if not draft.is_valid:
            return BuilderResult(
                success=False,
                error=f"validation failed after {draft.attempt} attempts",
                draft=draft,
                events_published=events_published,
            )

        # 10. Merge
        knowledge = self.merger.merge(draft, retrieved["existing"], plan)

        # 11. Write
        path = self.writer.write(knowledge, vault_root)

        # 12. Update index
        if self.knowledge_index:
            self.knowledge_index.update()

        # 13. Publish KnowledgeCommitted event
        events_published.append("KnowledgeCommitted")
        self.event_bus.publish(
            "KnowledgeCommitted",
            payload={
                "entity_type": knowledge.entity_type,
                "entity_id": knowledge.entity_id,
                "path": str(path),
                "version": knowledge.version,
            },
            source_skill="career_builder",
            entity_refs=[
                {
                    "entity_type": knowledge.entity_type,
                    "entity_id": knowledge.entity_id,
                }
            ],
        )

        # 14. Return success
        return BuilderResult(
            success=True,
            knowledge_object=knowledge,
            draft=draft,
            written_path=path,
            events_published=events_published,
            conflicts=knowledge.conflicts,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        artifact: Artifact,
        plan: Dict[str, Any],
        retrieved: Dict[str, Any],
    ) -> str:
        """Build the LLM prompt from artifact, plan, and retrieved data."""
        artifact_json = json.dumps(
            artifact.to_dict(), ensure_ascii=False, indent=2
        )
        existing_info = ""
        if retrieved.get("existing"):
            # Convert existing to JSON-safe format (handles dates, etc.)
            existing_safe = self._make_json_safe(retrieved["existing"])
            existing_info = f"\nEXISTING_ENTITY: {json.dumps(existing_safe, ensure_ascii=False)}"

        prompt = (
            f"You are a career knowledge builder. Given an artifact, "
            f"produce a YAML draft for a {plan['entity_type']} entity.\n\n"
            f"ARTIFACT_JSON:\n{artifact_json}\n"
            f"\nPLAN:\n"
            f"entity_type: {plan['entity_type']}\n"
            f"entity_id: {plan['entity_id']}\n"
            f"{existing_info}"
            f"\nProduce a YAML draft with the required fields for a "
            f"{plan['entity_type']} entity per the schema. Include: "
            f"title, status, role, timeline, stack, tags, confidence, sources. "
            f"Only use facts from the artifact. Set confidence to \"inferred\"."
        )
        return prompt

    def _build_retry_prompt(
        self,
        artifact: Artifact,
        plan: Dict[str, Any],
        retrieved: Dict[str, Any],
        validation_errors: List[str],
    ) -> str:
        """Build a retry prompt that includes validation error feedback."""
        base_prompt = self._build_prompt(artifact, plan, retrieved)
        errors_text = "\n".join(f"  - {e}" for e in validation_errors)
        return (
            f"{base_prompt}\n\n"
            f"VALIDATION ERRORS (fix these):\n{errors_text}\n"
            f"\nPlease produce a corrected YAML draft that addresses "
            f"all validation errors above."
        )

    def _make_json_safe(self, obj: Any) -> Any:
        """Convert non-JSON-serializable objects (dates, datetimes) to strings."""
        if isinstance(obj, dict):
            return {k: self._make_json_safe(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_safe(item) for item in obj]
        elif hasattr(obj, 'isoformat'):
            # datetime, date, time objects
            return obj.isoformat()
        else:
            return obj

    @staticmethod
    def _parse_yaml_output(raw: str) -> Dict[str, Any]:
        """Parse YAML from LLM output into a dict.

        Handles cases where the LLM wraps YAML in code fences.
        """
        text = raw.strip()

        # Strip code fences if present.
        if text.startswith("```"):
            # Remove opening fence line
            first_newline = text.index("\n")
            text = text[first_newline + 1 :]
            # Remove closing fence
            if text.endswith("```"):
                text = text[: -len("```")]
                text = text.rstrip()

        try:
            result = yaml.safe_load(text)
        except yaml.YAMLError:
            return {}

        if isinstance(result, dict):
            return result
        return {}
