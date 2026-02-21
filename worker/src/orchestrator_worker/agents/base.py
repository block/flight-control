import asyncio
from abc import ABC, abstractmethod
from typing import AsyncIterator


class AgentRunner(ABC):
    @abstractmethod
    async def run(
        self,
        task_prompt: str,
        agent_config: dict,
        mcp_servers: list[dict],
        env_vars: dict[str, str],
        credentials: dict[str, str],
        work_dir: str,
        timeout_seconds: int,
        run_id: str = "",
    ) -> AsyncIterator[tuple[str, str]]:
        """Run the agent. Yields (stream, line) tuples."""
        ...

    @abstractmethod
    async def get_exit_code(self) -> int | None:
        ...
