import asyncio
import logging
import tempfile

from orchestrator_worker.agents import get_runner
from orchestrator_worker.client import ServerClient
from orchestrator_worker.log_streamer import LogStreamer
from orchestrator_worker.skill_writer import download_and_write_skills

logger = logging.getLogger(__name__)


async def _upload_log_artifact(
    client: ServerClient, run_id: str, log_lines: list[tuple[str, str]]
) -> None:
    """Upload captured log lines as a run-output.log artifact."""
    if not log_lines:
        return
    content = "\n".join(f"[{stream}] {line}" for stream, line in log_lines) + "\n"
    try:
        await client.upload_artifact(
            run_id=run_id,
            filename="run-output.log",
            data=content.encode("utf-8"),
            content_type="text/plain",
        )
    except Exception:
        logger.exception(f"Failed to upload log artifact for run {run_id}")


async def execute_run(client: ServerClient, worker_id: str, job: dict) -> None:
    """Execute a job run: set up agent, stream logs, report completion."""
    run_id = job["run_id"]
    logger.info(f"Starting run {run_id}: {job['name']}")

    streamer = LogStreamer(client, run_id)
    flush_task = asyncio.create_task(streamer.run_flush_loop())
    captured_lines: list[tuple[str, str]] = []

    try:
        with tempfile.TemporaryDirectory(prefix=f"orch-{run_id}-") as work_dir:
            # Download skill files
            skills = job.get("skills", [])
            if skills:
                await download_and_write_skills(client, skills, work_dir)

            runner = get_runner(job.get("agent_type", "goose"))

            async for stream, line in runner.run(
                task_prompt=job["task_prompt"],
                agent_config=job.get("agent_config", {}),
                mcp_servers=job.get("mcp_servers", []),
                env_vars=job.get("env_vars", {}),
                credentials=job.get("credentials", {}),
                work_dir=work_dir,
                timeout_seconds=job.get("timeout_seconds", 1800),
                run_id=run_id,
            ):
                await streamer.add_line(stream, line)
                captured_lines.append((stream, line))
                logger.debug(f"[{stream}] {line}")

            exit_code = await runner.get_exit_code()

        # Final flush
        await streamer.flush()

        # Upload log artifact
        await _upload_log_artifact(client, run_id, captured_lines)

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
        captured_lines.append(("stderr", f"Worker error: {e}"))
        await streamer.flush()

        # Upload log artifact even on failure
        await _upload_log_artifact(client, run_id, captured_lines)

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
