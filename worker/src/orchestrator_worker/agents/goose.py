import asyncio
import os
import shutil
from typing import AsyncIterator

from orchestrator_worker.agents.base import AgentRunner
from orchestrator_worker.config_writer import write_goose_config


class GooseRunner(AgentRunner):
    def __init__(self):
        self._exit_code: int | None = None

    async def run(
        self,
        task_prompt: str,
        agent_config: dict,
        mcp_servers: list[dict],
        env_vars: dict[str, str],
        credentials: dict[str, str],
        work_dir: str,
        timeout_seconds: int,
    ) -> AsyncIterator[tuple[str, str]]:
        # Build environment
        env = os.environ.copy()
        env.update(env_vars)
        env.update(credentials)

        # Write MCP config
        config_path = write_goose_config(mcp_servers, work_dir)

        # Provider/model config
        provider = agent_config.get("provider", "anthropic")
        model = agent_config.get("model", "claude-sonnet-4-5")
        env["GOOSE_PROVIDER"] = provider
        env["GOOSE_MODEL"] = model

        # Build goose command
        cmd = ["goose", "run", "--no-session"]

        # Add task prompt
        cmd.extend(["-t", task_prompt])

        # Add max turns if specified
        max_turns = agent_config.get("max_turns")
        if max_turns:
            cmd.extend(["--max-turns", str(max_turns)])

        # Pass provider/model as CLI flags too (more reliable than env vars)
        cmd.extend(["--provider", provider])
        cmd.extend(["--model", model])

        # Set profile if we have MCP servers configured
        if config_path:
            env["GOOSE_PROFILE"] = "orchestrator"
            env["GOOSE_CONFIG_DIR"] = os.path.join(work_dir, ".config", "goose")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=work_dir,
                env=env,
            )

            # Read both streams concurrently using tasks
            async def read_stream(stream, stream_name, queue):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace").rstrip()
                    if text:  # Skip empty lines
                        await queue.put((stream_name, text))
                await queue.put(None)  # Sentinel

            queue = asyncio.Queue()
            stdout_task = asyncio.create_task(
                read_stream(process.stdout, "stdout", queue)
            )
            stderr_task = asyncio.create_task(
                read_stream(process.stderr, "stderr", queue)
            )

            streams_done = 0
            while streams_done < 2:
                item = await queue.get()
                if item is None:
                    streams_done += 1
                else:
                    yield item

            # Wait for reader tasks to finish
            await stdout_task
            await stderr_task

            try:
                self._exit_code = await asyncio.wait_for(
                    process.wait(), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                process.kill()
                self._exit_code = -1
                yield ("stderr", "Process timed out and was killed")

        except FileNotFoundError:
            self._exit_code = 127
            yield ("stderr", "Error: 'goose' command not found. Is Goose installed?")

    async def get_exit_code(self) -> int | None:
        return self._exit_code
