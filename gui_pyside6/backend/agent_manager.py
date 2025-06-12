from __future__ import annotations

from .agent_loader import load_agents


class AgentManager:
    """Manage available agents and the active selection."""

    def __init__(self) -> None:
        self._agents: list[dict] = load_agents()
        self._active_index: int = 0 if self._agents else -1

    @property
    def agents(self) -> list[dict]:
        """Return the list of loaded agent dictionaries."""
        return self._agents

    @property
    def active_agent(self) -> dict | None:
        """Return the currently active agent dictionary, if any."""
        if 0 <= self._active_index < len(self._agents):
            return self._agents[self._active_index]
        return None

    def set_active_agent(self, name: str) -> bool:
        """Set the active agent by its ``name``. Returns ``True`` if found."""
        for idx, agent in enumerate(self._agents):
            if agent.get("name") == name:
                self._active_index = idx
                return True
        return False

    def reload(self) -> None:
        """Reload agents from disk, keeping the previous active agent if possible."""
        previous = self.active_agent.get("name") if self.active_agent else None
        self._agents = load_agents()
        self._active_index = 0 if self._agents else -1
        if previous:
            self.set_active_agent(previous)
