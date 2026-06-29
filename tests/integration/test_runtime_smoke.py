"""Sprint 1 acceptance test — ResumeOS 0.1 Core Runtime smoke test.

This file is the CONTRACT for Sprint 1. The fixer must implement
``runtime/`` modules so that every test in this file passes.

Verifies the four runtime subsystems work together:
    1. EventBus publishes and delivers events to subscribers.
    2. EventBus persists events to events.jsonl (ADR-0014).
    3. KnowledgeIndex builds from vault/career/ and answers queries (ADR-0012).
    4. KnowledgeIndex updates incrementally when a note is added.
    5. WorkflowEngine loads and executes a workflow end-to-end (ADR-0018).
    6. Memory appends and recalls conversation entries (ADR-0020).

Architectural constraint (user directive + ADR-0014):
    runtime/ must NOT import any LLM SDK. Verified by TestNoLLMDependency.
"""

import json
import sys
import textwrap
from pathlib import Path

import pytest
import yaml


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_vault(tmp_path):
    """Create a minimal vault with one project note."""
    vault = tmp_path / "vault"
    career = vault / "career" / "projects"
    career.mkdir(parents=True)

    (career / "demo-project.md").write_text(textwrap.dedent("""\
        ---
        id: demo-project
        type: project
        title: Demo Project
        tags: [AI, Python]
        status: completed
        timeline:
          start: 2024-01-01
          end: 2024-06-01
        ---
        # Demo Project
        A test project for runtime smoke testing.
        """), encoding="utf-8")

    library = vault / ".library"
    library.mkdir()
    (library / "index").mkdir()
    (library / "memory").mkdir()
    yield vault


@pytest.fixture
def echo_skill():
    """A minimal no-LLM skill for workflow tests."""
    from sdk.python.skill import Skill

    class _Echo(Skill):
        def metadata(self):
            return {"name": "echo", "version": "1.0", "subscribes": []}

        def execute(self, inputs, context):
            return {"echo": inputs.get("message", ""), "inputs": inputs}

    return _Echo()


# ---------------------------------------------------------------------------
# 1. Event Bus
# ---------------------------------------------------------------------------

class TestEventBus:
    """Acceptance: bus.publish("ProjectImported") -> handler receives it."""

    def test_publish_delivers_to_subscriber(self, temp_vault):
        from runtime.event_bus import EventBus

        bus = EventBus(events_log=temp_vault / ".library" / "events.jsonl")
        received = []
        bus.subscribe("ProjectImported", lambda evt: received.append(evt))
        bus.publish(
            "ProjectImported",
            payload={"project_id": "demo"},
            source_skill="inbox_ingest",
        )
        assert len(received) == 1
        assert received[0]["type"] == "ProjectImported"
        assert received[0]["payload"]["project_id"] == "demo"
        assert received[0]["source_skill"] == "inbox_ingest"

    def test_publish_persists_to_events_jsonl(self, temp_vault):
        from runtime.event_bus import EventBus

        log_path = temp_vault / ".library" / "events.jsonl"
        bus = EventBus(events_log=log_path)
        bus.publish(
            "KnowledgeUpdated",
            payload={"entity_id": "demo-project"},
            source_skill="career_builder",
        )
        assert log_path.exists()
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        evt = json.loads(lines[0])
        assert evt["type"] == "KnowledgeUpdated"
        assert evt["source_skill"] == "career_builder"
        assert "time" in evt  # ISO 8601 string

    def test_non_subscribed_event_not_delivered(self, temp_vault):
        from runtime.event_bus import EventBus

        bus = EventBus(events_log=temp_vault / ".library" / "events.jsonl")
        received = []
        bus.subscribe("ProjectImported", lambda evt: received.append(evt))
        bus.publish("KnowledgeUpdated", payload={}, source_skill="test")
        assert len(received) == 0

    def test_events_read_back(self, temp_vault):
        from runtime.event_bus import EventBus

        bus = EventBus(events_log=temp_vault / ".library" / "events.jsonl")
        bus.publish("ProjectImported", payload={"a": 1}, source_skill="s1")
        bus.publish("KnowledgeUpdated", payload={"b": 2}, source_skill="s2")
        events = bus.events()
        assert len(events) == 2
        assert events[0]["type"] == "ProjectImported"
        assert events[1]["type"] == "KnowledgeUpdated"

    def test_wildcard_subscriber_receives_all(self, temp_vault):
        """Subscribing with '*' receives every event (ADR-0014 Rule 4)."""
        from runtime.event_bus import EventBus

        bus = EventBus(events_log=temp_vault / ".library" / "events.jsonl")
        received = []
        bus.subscribe("*", lambda evt: received.append(evt))
        bus.publish("ProjectImported", payload={}, source_skill="t")
        bus.publish("KnowledgeUpdated", payload={}, source_skill="t")
        assert len(received) == 2


# ---------------------------------------------------------------------------
# 2. Knowledge Index
# ---------------------------------------------------------------------------

class TestKnowledgeIndex:
    """Acceptance: build from vault, query, incremental update."""

    def test_build_and_query(self, temp_vault):
        from runtime.knowledge_index import KnowledgeIndex

        idx = KnowledgeIndex(vault_root=temp_vault)
        idx.build()
        projects = idx.query(entity_type="project")
        assert len(projects) == 1
        assert projects[0]["id"] == "demo-project"
        assert projects[0]["title"] == "Demo Project"
        assert "AI" in projects[0]["tags"]

    def test_build_writes_index_file(self, temp_vault):
        from runtime.knowledge_index import KnowledgeIndex

        idx = KnowledgeIndex(vault_root=temp_vault)
        idx.build()
        index_path = temp_vault / ".library" / "index" / "knowledge-index.json"
        assert index_path.exists()
        data = json.loads(index_path.read_text(encoding="utf-8"))
        assert data["schema_version"] == "1.0"
        assert data["entity_count"] == 1
        assert len(data["entities"]["projects"]) == 1

    def test_incremental_update_adds_new_note(self, temp_vault):
        from runtime.knowledge_index import KnowledgeIndex

        idx = KnowledgeIndex(vault_root=temp_vault)
        idx.build()
        # Add a second project
        (temp_vault / "career" / "projects" / "second.md").write_text(
            textwrap.dedent("""\
                ---
                id: second
                type: project
                title: Second Project
                tags: [ROS]
                status: active
                ---
                # Second Project
                """),
            encoding="utf-8",
        )
        idx.update()
        projects = idx.query(entity_type="project")
        assert len(projects) == 2

    def test_query_by_tags(self, temp_vault):
        from runtime.knowledge_index import KnowledgeIndex

        idx = KnowledgeIndex(vault_root=temp_vault)
        idx.build()
        results = idx.query(tags=["AI"])
        assert len(results) == 1
        assert results[0]["id"] == "demo-project"

    def test_query_no_results(self, temp_vault):
        from runtime.knowledge_index import KnowledgeIndex

        idx = KnowledgeIndex(vault_root=temp_vault)
        idx.build()
        assert idx.query(entity_type="award") == []


# ---------------------------------------------------------------------------
# 3. Workflow Engine
# ---------------------------------------------------------------------------

class TestWorkflowEngine:
    """Acceptance: load and execute a simple workflow."""

    def _write_workflow(self, path: Path):
        path.write_text(yaml.dump({
            "id": "test-wf",
            "version": "1.0",
            "description": "Sprint 1 smoke test workflow",
            "trigger": "manual",
            "steps": [
                {
                    "id": "step1",
                    "skill": "echo",
                    "phase": "test",
                    "inputs": {"message": "hello"},
                },
                {
                    "id": "step2",
                    "skill": "echo",
                    "phase": "test",
                    "depends_on": ["step1"],
                    "inputs": {"message": "world"},
                    "on_success_event": "TestWorkflowCompleted",
                },
            ],
        }), encoding="utf-8")

    def test_execute_simple_workflow(self, temp_vault, echo_skill):
        from runtime.event_bus import EventBus
        from runtime.workflow import WorkflowEngine

        bus = EventBus(events_log=temp_vault / ".library" / "events.jsonl")
        engine = WorkflowEngine(event_bus=bus)
        engine.register_skill("echo", echo_skill)

        wf_path = temp_vault / "test-workflow.yaml"
        self._write_workflow(wf_path)
        results = engine.run(wf_path, context={})
        assert "step1" in results
        assert "step2" in results
        assert results["step1"]["echo"] == "hello"
        assert results["step2"]["echo"] == "world"

    def test_workflow_emits_on_success_event(self, temp_vault, echo_skill):
        from runtime.event_bus import EventBus
        from runtime.workflow import WorkflowEngine

        bus = EventBus(events_log=temp_vault / ".library" / "events.jsonl")
        engine = WorkflowEngine(event_bus=bus)
        engine.register_skill("echo", echo_skill)

        wf_path = temp_vault / "test-workflow.yaml"
        self._write_workflow(wf_path)
        engine.run(wf_path, context={})

        events = bus.events()
        types = [e["type"] for e in events]
        assert "TestWorkflowCompleted" in types

    def test_workflow_respects_dependency_order(self, temp_vault, echo_skill):
        """step2 depends on step1; step2 must see step1's result in context."""
        from runtime.event_bus import EventBus
        from runtime.workflow import WorkflowEngine

        bus = EventBus(events_log=temp_vault / ".library" / "events.jsonl")
        engine = WorkflowEngine(event_bus=bus)
        engine.register_skill("echo", echo_skill)

        wf_path = temp_vault / "dep-wf.yaml"
        wf_path.write_text(yaml.dump({
            "id": "dep-wf",
            "version": "1.0",
            "description": "Dependency order test",
            "trigger": "manual",
            "steps": [
                {"id": "s1", "skill": "echo", "phase": "t",
                 "inputs": {"message": "first"}},
                {"id": "s2", "skill": "echo", "phase": "t",
                 "depends_on": ["s1"],
                 "inputs": {"message": "second"}},
            ],
        }), encoding="utf-8")
        results = engine.run(wf_path, context={})
        # s2 ran after s1 — context should contain s1's result
        assert results["s1"]["echo"] == "first"
        assert results["s2"]["echo"] == "second"


# ---------------------------------------------------------------------------
# 4. Memory
# ---------------------------------------------------------------------------

class TestMemory:
    """Acceptance: remember and recall (ADR-0020)."""

    def test_remember_and_recall(self, temp_vault):
        from runtime.memory import Memory

        mem = Memory(
            store=temp_vault / ".library" / "memory" / "conversation.jsonl"
        )
        mem.remember(
            entity_id="demo-project",
            topic="team_size",
            question="What was the team size?",
            answer="5",
        )
        results = mem.recall(entity_id="demo-project")
        assert len(results) == 1
        assert results[0]["answer"] == "5"
        assert results[0]["confidence"] == "confirmed"

    def test_recall_by_topic(self, temp_vault):
        from runtime.memory import Memory

        mem = Memory(
            store=temp_vault / ".library" / "memory" / "conversation.jsonl"
        )
        mem.remember("proj-a", "metrics", "FPS?", "30")
        mem.remember("proj-a", "role", "Your role?", "lead")
        results = mem.recall(entity_id="proj-a", topic="metrics")
        assert len(results) == 1
        assert results[0]["answer"] == "30"

    def test_recall_empty(self, temp_vault):
        from runtime.memory import Memory

        mem = Memory(
            store=temp_vault / ".library" / "memory" / "conversation.jsonl"
        )
        assert mem.recall(entity_id="nonexistent") == []

    def test_memory_is_append_only(self, temp_vault):
        """Multiple remembers for the same entity+topic are all kept."""
        from runtime.memory import Memory

        mem = Memory(
            store=temp_vault / ".library" / "memory" / "conversation.jsonl"
        )
        mem.remember("proj", "q", "old?", "1")
        mem.remember("proj", "q", "new?", "2")
        results = mem.recall(entity_id="proj", topic="q")
        assert len(results) == 2


# ---------------------------------------------------------------------------
# 5. LLM-agnostic constraint
# ---------------------------------------------------------------------------

class TestNoLLMDependency:
    """Architectural constraint: runtime/ must NOT import any LLM SDK.

    The runtime is pure infrastructure (events, index, workflow, memory).
    LLM access is always a plugin/adapter, never a runtime dependency.
    """

    @pytest.mark.parametrize("module_name", [
        "runtime",
        "runtime.event_bus",
        "runtime.dispatcher",
        "runtime.knowledge_index",
        "runtime.workflow",
        "runtime.memory",
    ])
    def test_no_llm_imports(self, module_name):
        import importlib

        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            pytest.skip(f"{module_name} not yet implemented")
            return

        source = Path(mod.__file__).read_text(encoding="utf-8")
        forbidden = [
            "anthropic",
            "openai",
            "google.generativeai",
            "dashscope",
            "qwen",
            "deepseek",
            "zhipuai",
            "litellm",
            "langchain",
        ]
        for keyword in forbidden:
            assert keyword not in source.lower(), (
                f"{module_name} references LLM SDK '{keyword}' — "
                "runtime must be LLM-agnostic (user directive + ADR-0014)"
            )
