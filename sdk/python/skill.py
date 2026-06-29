"""ResumeOS Skill base class.

Every Tier-1 Skill (ADR-0004) extends this class. The runtime calls:

- ``execute()`` — when a workflow step (ADR-0018) references this skill.
- ``on_event()`` — when an event the skill subscribed to (ADR-0014) fires.
- ``metadata()`` — to read the skill's manifest (matches plugin.json).

The runtime never imports an LLM SDK. Skills that need LLM capability
inject a provider through their constructor or via MCP tools declared
in plugin.json:mcp_tools (ADR-0008).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class Skill(ABC):
    """Base class for all ResumeOS Tier-1 Skills."""

    # ------------------------------------------------------------------
    # Manifest
    # ------------------------------------------------------------------

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Return the skill manifest.

        Must match the shape of ``plugin.json`` (ADR-0005):
        ``{name, version, description, type, depends_on, hooks,
        subscribes, mcp_tools, permissions}``.
        """
        ...

    # ------------------------------------------------------------------
    # Workflow execution
    # ------------------------------------------------------------------

    @abstractmethod
    def execute(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute the skill's primary action.

        Called by ``WorkflowEngine.run()`` when a workflow step
        references this skill by name. ``context`` carries results
        of prior steps keyed by step id.

        Returns a JSON-serializable dict stored as the step result.
        """
        ...

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def on_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a subscribed event.

        Override if the skill subscribes to events via
        ``plugin.json:subscribes[]``. The default is a no-op so
        workflow-only skills can ignore the event bus entirely.

        ``event`` matches the event schema (ADR-0014):
        ``{type, time, source_skill, payload, entity_refs}``.

        Returns an optional result dict (e.g. a follow-up action).
        """
        return None

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Skill name from metadata(). Convenience accessor."""
        return self.metadata().get("name", self.__class__.__name__)

    @property
    def subscribes(self) -> List[str]:
        """Event types this skill subscribes to. Default: none."""
        return self.metadata().get("subscribes", [])
