"""Agent runner registry."""

from orchestrator_worker.agents.base import AgentRunner
from orchestrator_worker.agents.goose import GooseRunner

AGENT_REGISTRY: dict[str, type[AgentRunner]] = {
    "goose": GooseRunner,
}


def get_runner(agent_type: str) -> AgentRunner:
    """Return a runner instance for the given agent type."""
    cls = AGENT_REGISTRY.get(agent_type)
    if cls is None:
        raise ValueError(
            f"Unknown agent type: {agent_type!r}. "
            f"Available: {', '.join(AGENT_REGISTRY)}"
        )
    return cls()
