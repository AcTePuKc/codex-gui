from __future__ import annotations

import json
from pathlib import Path

from .agent_loader import load_agents, AGENTS_DIR


class AgentManager:
    """Manage available agents and the active selection."""

    def __init__(self) -> None:
        self._agents: list[dict] = load_agents()
        self._active_index: int = 0 if self._agents else -1

    def is_default(self, agent: dict) -> bool:
        """Return ``True`` if the agent comes from the bundled presets."""
        path = agent.get("_path")
        if not path:
            return False
        try:
            return Path(path).resolve().is_relative_to(AGENTS_DIR.resolve())
        except Exception:
            return False

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

    def save_agent(self, agent: dict, path: Path | None = None) -> Path:
        """Save ``agent`` to ``path`` or its existing location."""
        save_path = Path(path or agent.get("_path", ""))
        data = {k: v for k, v in agent.items() if k != "_path"}
        save_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        agent["_path"] = str(save_path)
        self.reload()
        return save_path

    def rename_agent(self, agent: dict, new_path: Path) -> Path:
        """Rename the agent file to ``new_path``."""
        old = Path(agent.get("_path", ""))
        new = new_path.with_suffix(".json")
        old.rename(new)
        agent["_path"] = str(new)
        agent["name"] = new.stem.replace("_", " ").title()
        self.save_agent(agent, new)
        return new

    def delete_agent(self, agent: dict) -> None:
        """Delete the agent file from disk."""
        path = Path(agent.get("_path", ""))
        if path.exists():
            path.unlink()
        self.reload()
