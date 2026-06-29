"""Workflow Engine — declarative Skill orchestration (ADR-0018).

Loads a YAML workflow file, resolves skill dependencies, topologically
sorts steps into a DAG, and executes them in order.  A domain event is
published on step success when the step declares an
``on_success_event`` (ADR-0014).

Per ADR-0018:
    - Workflows are declarative, not imperative.
    - Steps reference Skills by id (resolved via the engine's registry).
    - Dependencies form a DAG; cycles are rejected at load time.
    - Checkpoints are logged; Sprint 1 does not pause for user input.
    - Events drive cross-workflow reaction via the Event Bus (ADR-0014).

This module is LLM-agnostic: it imports only stdlib, yaml, and
``runtime.event_bus``.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from runtime.event_bus import EventBus

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Declarative workflow executor (ADR-0018).

    A ``WorkflowEngine`` knows a set of registered Skill instances keyed
    by name.  ``run()`` parses a YAML workflow, resolves each step's
    skill reference, topologically sorts the step graph, and invokes
    each Skill's ``execute()`` in order.

    Args:
        event_bus: An :class:`EventBus` used to emit ``on_success_event``
            domain events after each successful step.  May be ``None``
            for workflows that declare no ``on_success_event``.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus
        self._skills: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Skill registry
    # ------------------------------------------------------------------

    def register_skill(self, name: str, skill: Any) -> None:
        """Register *skill* under *name*.

        When a workflow step declares ``skill: <name>``, the engine
        resolves this registration.  Missing registrations raise at
        execution time.

        Args:
            name: Skill id, matching the ``skill:`` field in the
                workflow YAML (and ``plugin.json`` / ``metadata()``).
            skill: Any object implementing ``execute(inputs, context)``
                (typically an :class:`sdk.python.skill.Skill` instance).
        """
        self._skills[name] = skill

    # ------------------------------------------------------------------
    # Workflow execution
    # ------------------------------------------------------------------

    def run(self, workflow_path: Path, context: dict) -> dict:
        """Execute a workflow file end-to-end (ADR-0018).

        1. Parse the YAML workflow.
        2. Validate the step graph (unknown dependencies and cycles are
           rejected).
        3. Topologically sort steps by ``depends_on``.
        4. For each step: call ``skill.execute(inputs, context)``,
           store the result in both the return map and the execution
           context, emit ``on_success_event`` (if declared), and log
           checkpoints.

        Args:
            workflow_path: Path to the YAML workflow file.
            context: Mutable execution context.  A defensive copy is
                made, so the caller's dict is not modified.  The copy
                is exposed to each ``skill.execute()`` call and is
                augmented with each step's result keyed by step id.

        Returns:
            ``{step_id: result}`` — one entry per executed step, in
            topological order.

        Raises:
            FileNotFoundError: If the workflow file does not exist.
            ValueError: If the workflow references an unknown step,
                forms a cycle, or references an unregistered skill.
            RuntimeError: If a Skill's ``execute()`` raises.  The
                message includes both the step id and the original
                exception details.
        """
        workflow_path = Path(workflow_path)
        with open(workflow_path, "r", encoding="utf-8") as fh:
            workflow = yaml.safe_load(fh)

        steps: List[Dict[str, Any]] = workflow.get("steps", [])
        if not steps:
            raise ValueError("Workflow has no steps")

        step_map: Dict[str, Dict[str, Any]] = {s["id"]: s for s in steps}

        # Validate and build the DAG.
        in_degree: Dict[str, int] = {s["id"]: 0 for s in steps}
        adj: Dict[str, List[str]] = defaultdict(list)

        for step in steps:
            step_id = step["id"]
            for dep in step.get("depends_on") or []:
                if dep not in step_map:
                    raise ValueError(
                        f"Step '{step_id}' depends on unknown step '{dep}'"
                    )
                adj[dep].append(step_id)
                in_degree[step_id] += 1

        # Kahn's algorithm for topological sort (with deterministic tie-
        # breaking by step id for reproducibility).
        queue: List[str] = sorted(
            [sid for sid, deg in in_degree.items() if deg == 0]
        )
        topo_order: List[str] = []

        while queue:
            u = queue.pop(0)
            topo_order.append(u)
            for v in sorted(adj[u]):
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)
            queue.sort()

        if len(topo_order) != len(step_map):
            raise ValueError(
                "Workflow contains a dependency cycle "
                f"(resolved {len(topo_order)} of {len(step_map)} steps)"
            )

        logger.info(
            "Running workflow '%s' (%s) with %d steps",
            workflow.get("id", "?"),
            workflow.get("description", ""),
            len(topo_order),
        )

        # Defensive copy so we don't mutate the caller's dict.
        execution_context: Dict[str, Any] = dict(context)
        results: Dict[str, Any] = {}

        for step_id in topo_order:
            step = step_map[step_id]
            skill_name = step["skill"]

            if skill_name not in self._skills:
                raise ValueError(
                    f"Workflow step '{step_id}' references unknown skill "
                    f"'{skill_name}'. Did you call register_skill()?"
                )

            skill = self._skills[skill_name]
            inputs = step.get("inputs") or {}

            logger.info("Executing step '%s' (skill=%s)", step_id, skill_name)
            try:
                result = skill.execute(inputs=inputs, context=execution_context)
            except Exception as exc:
                raise RuntimeError(
                    f"Workflow step '{step_id}' failed: {exc}"
                ) from exc

            results[step_id] = result
            execution_context[step_id] = result

            # Checkpoint: log only in Sprint 1 (ADR-0018 Rule 4). No
            # user interaction yet; the step's dependents proceed.
            if step.get("checkpoint"):
                logger.info(
                    "Checkpoint at step '%s' — Sprint 1 auto-proceed",
                    step_id,
                )

            # Publish on_success_event (ADR-0018 Rule 6, ADR-0014).
            on_success = step.get("on_success_event")
            if on_success and self._event_bus is not None:
                self._event_bus.publish(
                    event_type=on_success,
                    payload={"step_id": step_id, "result": result},
                    source_skill=skill_name,
                )

        logger.info(
            "Workflow '%s' completed successfully (%d steps)",
            workflow.get("id", "?"),
            len(topo_order),
        )
        return results
