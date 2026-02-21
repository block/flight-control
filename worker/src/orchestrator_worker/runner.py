import asyncio
import logging
import tempfile

from orchestrator_worker.agents.goose import GooseRunner
from orchestrator_worker.client import ServerClient
from orchestrator_worker.log_streamer import LogStreamer

logger = logging.getLogger(__name__)


async def execute_run(client: ServerClient, worker_id: str, job: dict) -> None:
    """Execute a job run: set up agent, stream logs, report completion."""
    run_id = job["run_id"]
    logger.info(f"Starting run {run_id}: {job['name']}")

    streamer = LogStreamer(client, run_id)
    flush_task = asyncio.create_task(streamer.run_flush_loop())

    try:
        with tempfile.TemporaryDirectory(prefix=f"orch-{run_id}-") as work_dir:
            runner = GooseRunner()

            async for stream, line in runner.run(
                task_prompt=job["task_prompt"],
                agent_config=job.get("agent_config", {}),
                mcp_servers=job.get("mcp_servers", []),
                env_vars=job.get("env_vars", {}),
                credentials=job.get("credentials", {}),
                work_dir=work_dir,
                timeout_seconds=job.get("timeout_seconds", 1800),
            ):
                await streamer.add_line(stream, line)
                logger.debug(f"[{stream}] {line}")

            exit_code = await runner.get_exit_code()

        # Final flush
        await streamer.flush()

        status = "completed" if exit_code == 0 else "failed"
        await client.complete_run(
            run_id=run_id,
            worker_id=worker_id,
            status=status,
            exit_code=exit_code,
        )
        logger.info(f"Run {run_id} {status} (exit code: {exit_code})")

    except Exception as e:
        logger.exception(f"Run {run_id} failed with error: {e}")
        await streamer.add_line("stderr", f"Worker error: {e}")
        await streamer.flush()

        try:
            await client.complete_run(
                run_id=run_id,
                worker_id=worker_id,
                status="failed",
                result=str(e),
                exit_code=-1,
            )
        except Exception:
            logger.exception("Failed to report run failure")
    finally:
        flush_task.cancel()
        try:
            await flush_task
        except asyncio.CancelledError:
            pass
