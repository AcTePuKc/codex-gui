import json
from pathlib import Path

AGENTS_DIR = Path("resources/agents")

def load_agents() -> list[dict]:
    agents = []
    for file in AGENTS_DIR.glob("*.json"):
        with file.open("r", encoding="utf-8") as f:
            try:
                agents.append(json.load(f))
            except json.JSONDecodeError:
                print(f"Failed to parse agent: {file.name}")
    return agents
