"""Unit tests for :mod:`runtime.workflow`.

These tests complement the acceptance tests in
``tests/integration/test_runtime_smoke.py::TestWorkflowEngine`` by covering:
    - Missing skill registration raises ``ValueError`` before execution.
    - Circular dependencies are detected and rejected at load time.
    - Parallel steps (multiple steps with no ``depends_on``) all execute.
    - ``checkpoint: true`` is logged but does not pause execution.
    - ``on_success_event`` carries step_id + result + correct source_skill.
    - Unknown ``depends_on`` raises ``ValueError``.
    - Step failure is wrapped in ``RuntimeError`` with step id in message.
    - Caller's context dict is not mutated.
    - Empty workflow (no steps) raises ``ValueError``.

Per ADR-0018 (Workflow Engine).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest
import yaml

from runtime.event_bus import EventBus
from runtime.workflow import WorkflowEngine
from sdk.python.skill import Skill


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


class _Echo(Skill):
    """A simple echo skill for deterministic tests."""

    def __init__(self, fail_on: str | None = None) -> None:
        self._fail_on = fail_on
        self.calls: list = []

    def metadata(self):
        return {"name": "echo", "version": "1.0", "subscribes": []}

    def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append((inputs, context))
        if self._fail_on and inputs.get("message") == self._fail_on:
            raise RuntimeError(f"forced failure on '{self._fail_on}'")
        return {"echo": inputs.get("message", ""), "inputs": inputs}


class _Identity(Skill):
    """Returns inputs verbatim (prefixed with 'id:')."""

    def metadata(self):
        return {"name": "identity", "version": "1.0", "subscribes": []}

    def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"identity": True, "inputs": inputs}


@pytest.fixture
def log_path(tmp_path):
    return tmp_path / ".library" / "events.jsonl"


@pytest.fixture
def bus(log_path):
    return EventBus(events_log=log_path)


@pytest.fixture
def engine(bus):
    eng = WorkflowEngine(event_bus=bus)
    eng.register_skill("echo", _Echo())
    return eng


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.dump(payload), encoding="utf-8")


def _simple_workflow(steps: list, wf_id: str = "wf") -> dict:
    """Wrap steps in a valid workflow envelope."""
    return {
        "id": wf_id,
        "version": "1.0.0",
        "description": "unit test workflow",
        "trigger": "manual",
        "steps": steps,
    }


# ---------------------------------------------------------------------------
# Missing skill registration
# ---------------------------------------------------------------------------


class TestMissingSkill:
    """Referencing an unregistered skill fails fast."""

    def test_unknown_skill_raises(self, engine, tmp_path):
        wf = _simple_workflow(
            [{"id": "s1", "skill": "not_registered", "inputs": {}}]
        )
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        with pytest.raises(ValueError, match="unknown skill"):
            engine.run(p, context={})


# ---------------------------------------------------------------------------
# Dependency validation
# ---------------------------------------------------------------------------


class TestDependencyValidation:
    """Cycles and unknown dependencies must be rejected."""

    def test_circular_dependency_detected(self, engine, tmp_path):
        wf = _simple_workflow([
            {"id": "a", "skill": "echo", "depends_on": ["b"], "inputs": {}},
            {"id": "b", "skill": "echo", "depends_on": ["a"], "inputs": {}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        with pytest.raises(ValueError, match="cycle"):
            engine.run(p, context={})

    def test_self_cycle_detected(self, engine, tmp_path):
        wf = _simple_workflow([
            {"id": "a", "skill": "echo", "depends_on": ["a"], "inputs": {}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        with pytest.raises(ValueError, match="cycle"):
            engine.run(p, context={})

    def test_unknown_dependency_raises(self, engine, tmp_path):
        wf = _simple_workflow([
            {"id": "s1", "skill": "echo", "depends_on": ["ghost"], "inputs": {}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        with pytest.raises(ValueError, match="unknown step"):
            engine.run(p, context={})

    def test_empty_workflow_raises(self, engine, tmp_path):
        wf = _simple_workflow([])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        with pytest.raises(ValueError, match="no steps"):
            engine.run(p, context={})


# ---------------------------------------------------------------------------
# Parallel steps (no depends_on)
# ---------------------------------------------------------------------------


class TestParallelSteps:
    """Multiple steps with no depends_on all execute."""

    def test_no_depends_on_all_run(self, engine, tmp_path):
        wf = _simple_workflow([
            {"id": "a", "skill": "echo", "inputs": {"message": "A"}},
            {"id": "b", "skill": "echo", "inputs": {"message": "B"}},
            {"id": "c", "skill": "echo", "inputs": {"message": "C"}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        results = engine.run(p, context={})
        assert {results[sid]["echo"] for sid in results} == {"A", "B", "C"}
        assert len(results) == 3

    def test_fan_out(self, tmp_path, bus):
        """One root -> N independent leaves."""
        eng = WorkflowEngine(event_bus=bus)
        eng.register_skill("echo", _Echo())
        wf = _simple_workflow([
            {"id": "root", "skill": "echo", "inputs": {"message": "R"}},
            {"id": "l1", "skill": "echo", "depends_on": ["root"],
             "inputs": {"message": "L1"}},
            {"id": "l2", "skill": "echo", "depends_on": ["root"],
             "inputs": {"message": "L2"}},
            {"id": "l3", "skill": "echo", "depends_on": ["root"],
             "inputs": {"message": "L3"}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        results = eng.run(p, context={})
        assert len(results) == 4
        assert results["root"]["echo"] == "R"
        assert results["l1"]["echo"] == "L1"
        assert results["l2"]["echo"] == "L2"
        assert results["l3"]["echo"] == "L3"


# ---------------------------------------------------------------------------
# Checkpoint behaviour
# ---------------------------------------------------------------------------


class TestCheckpoints:
    """Checkpoints are logged but do not pause execution in Sprint 1."""

    def test_checkpoint_does_not_block(self, engine, tmp_path):
        wf = _simple_workflow([
            {"id": "s1", "skill": "echo", "checkpoint": True,
             "inputs": {"message": "first"}},
            {"id": "s2", "skill": "echo", "depends_on": ["s1"],
             "inputs": {"message": "second"}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        results = engine.run(p, context={})
        # s2 still runs after checkpoint step s1.
        assert results["s1"]["echo"] == "first"
        assert results["s2"]["echo"] == "second"


# ---------------------------------------------------------------------------
# on_success_event
# ---------------------------------------------------------------------------


class TestOnSuccessEvent:
    """Domain events emitted after step success."""

    def test_event_payload_carries_step_id_and_result(self, bus, tmp_path):
        eng = WorkflowEngine(event_bus=bus)
        eng.register_skill("echo", _Echo())
        wf = _simple_workflow([
            {"id": "done", "skill": "echo", "inputs": {"message": "ok"},
             "on_success_event": "StepDone"},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        eng.run(p, context={})
        events = bus.events()
        assert any(e["type"] == "StepDone" for e in events)
        done_evt = [e for e in events if e["type"] == "StepDone"][0]
        assert done_evt["payload"]["step_id"] == "done"
        assert done_evt["payload"]["result"]["echo"] == "ok"
        assert done_evt["source_skill"] == "echo"

    def test_on_success_event_not_emitted_on_failure(self, bus, tmp_path):
        eng = WorkflowEngine(event_bus=bus)
        eng.register_skill("echo", _Echo(fail_on="bad"))
        wf = _simple_workflow([
            {"id": "s1", "skill": "echo", "inputs": {"message": "bad"},
             "on_success_event": "ShouldNotFire"},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        with pytest.raises(RuntimeError):
            eng.run(p, context={})
        events = bus.events()
        assert not any(e["type"] == "ShouldNotFire" for e in events)

    def test_workflow_without_event_bus(self, tmp_path):
        """Engine with event_bus=None still runs steps that don't declare
        on_success_event."""
        eng = WorkflowEngine(event_bus=None)
        eng.register_skill("echo", _Echo())
        wf = _simple_workflow([
            {"id": "s1", "skill": "echo", "inputs": {"message": "x"}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        results = eng.run(p, context={})
        assert results["s1"]["echo"] == "x"


# ---------------------------------------------------------------------------
# Step failure
# ---------------------------------------------------------------------------


class TestStepFailure:
    """Skill error is wrapped in RuntimeError including the step id."""

    def test_failure_wraps_as_runtime_error(self, bus, tmp_path):
        eng = WorkflowEngine(event_bus=bus)
        eng.register_skill("echo", _Echo(fail_on="bad"))
        wf = _simple_workflow([
            {"id": "boom", "skill": "echo", "inputs": {"message": "bad"}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        with pytest.raises(RuntimeError, match="boom"):
            eng.run(p, context={})

    def test_failure_halts_remaining_steps(self, bus, tmp_path):
        eng = WorkflowEngine(event_bus=bus)
        echo = _Echo(fail_on="bad")
        eng.register_skill("echo", echo)
        wf = _simple_workflow([
            {"id": "s1", "skill": "echo", "inputs": {"message": "good"}},
            {"id": "s2", "skill": "echo", "inputs": {"message": "bad"}},
            {"id": "s3", "skill": "echo", "depends_on": ["s2"],
             "inputs": {"message": "never"}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        with pytest.raises(RuntimeError):
            eng.run(p, context={})
        # s3 never ran; s1 and s2 did.
        assert len(echo.calls) == 2


# ---------------------------------------------------------------------------
# Context / results
# ---------------------------------------------------------------------------


class TestContextIsolation:
    """Caller's original context dict is not mutated."""

    def test_caller_context_not_mutated(self, engine, tmp_path):
        original = {"initial": "value"}
        wf = _simple_workflow([
            {"id": "s1", "skill": "echo", "inputs": {"message": "hi"}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        engine.run(p, context=original)
        # The caller's dict must not gain step results.
        assert original == {"initial": "value"}

    def test_step_sees_prior_result_in_context(self, bus, tmp_path):
        """Each step's execute() sees a context containing prior results."""
        seen: list = []

        class _Spy(Skill):
            def metadata(self):
                return {"name": "spy", "version": "1.0", "subscribes": []}

            def execute(self, inputs, context):
                seen.append(dict(context))
                return {"spy": len(seen)}

        eng = WorkflowEngine(event_bus=bus)
        eng.register_skill("spy", _Spy())
        wf = _simple_workflow([
            {"id": "s1", "skill": "spy", "inputs": {}},
            {"id": "s2", "skill": "spy", "depends_on": ["s1"], "inputs": {}},
        ])
        p = tmp_path / "w.yaml"
        _write_yaml(p, wf)
        eng.run(p, context={"seed": 42})
        # s1's call sees the seed only; s2's call sees s1's result.
        assert seen[0] == {"seed": 42}
        assert seen[1] == {"seed": 42, "s1": {"spy": 1}}
