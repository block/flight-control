import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from orchestrator_worker.runner import execute_run


def _make_job(run_id="run-1", **overrides):
    job = {
        "run_id": run_id,
        "name": "Test Job",
        "task_prompt": "Do the thing",
        "agent_config": {},
        "mcp_servers": [],
        "env_vars": {},
        "credentials": {},
        "timeout_seconds": 60,
    }
    job.update(overrides)
    return job


def _mock_runner(lines=None, exit_code=0):
    """Create a mock GooseRunner that yields given lines and returns exit_code."""
    runner = AsyncMock()

    async def fake_run(**kwargs):
        for item in (lines or []):
            yield item

    runner.run = MagicMock(side_effect=fake_run)
    runner.get_exit_code = AsyncMock(return_value=exit_code)
    return runner


def _mock_runner_that_raises(exc):
    """Create a mock GooseRunner whose run() raises an exception."""
    runner = AsyncMock()

    async def exploding_run(**kwargs):
        raise exc
        # Make it an async generator
        yield  # noqa: unreachable

    runner.run = MagicMock(side_effect=exploding_run)
    runner.get_exit_code = AsyncMock(return_value=-1)
    return runner


@pytest.mark.asyncio
async def test_successful_run(mock_client):
    runner = _mock_runner(
        lines=[("stdout", "hello"), ("stderr", "debug info")],
        exit_code=0,
    )

    with patch("orchestrator_worker.runner.GooseRunner", return_value=runner):
        await execute_run(mock_client, "worker-1", _make_job())

    # Should upload log artifact
    mock_client.upload_artifact.assert_called_once()
    call_kwargs = mock_client.upload_artifact.call_args[1]
    assert call_kwargs["run_id"] == "run-1"
    assert call_kwargs["filename"] == "run-output.log"

    # Should report completed
    mock_client.complete_run.assert_called_once()
    call_kwargs = mock_client.complete_run.call_args[1]
    assert call_kwargs["status"] == "completed"
    assert call_kwargs["exit_code"] == 0


@pytest.mark.asyncio
async def test_failed_run_nonzero_exit(mock_client):
    runner = _mock_runner(lines=[("stderr", "error occurred")], exit_code=1)

    with patch("orchestrator_worker.runner.GooseRunner", return_value=runner):
        await execute_run(mock_client, "worker-1", _make_job())

    call_kwargs = mock_client.complete_run.call_args[1]
    assert call_kwargs["status"] == "failed"
    assert call_kwargs["exit_code"] == 1


@pytest.mark.asyncio
async def test_exception_during_run(mock_client):
    runner = _mock_runner_that_raises(RuntimeError("boom"))

    with patch("orchestrator_worker.runner.GooseRunner", return_value=runner):
        await execute_run(mock_client, "worker-1", _make_job())

    # Should still upload log artifact
    mock_client.upload_artifact.assert_called_once()

    # Should report failed
    mock_client.complete_run.assert_called_once()
    call_kwargs = mock_client.complete_run.call_args[1]
    assert call_kwargs["status"] == "failed"
    assert call_kwargs["exit_code"] == -1


@pytest.mark.asyncio
async def test_run_id_passed_to_agent(mock_client):
    runner = _mock_runner()

    with patch("orchestrator_worker.runner.GooseRunner", return_value=runner):
        await execute_run(mock_client, "worker-1", _make_job(run_id="run-xyz"))

    runner.run.assert_called_once()
    call_kwargs = runner.run.call_args[1]
    assert call_kwargs["run_id"] == "run-xyz"
    assert call_kwargs["task_prompt"] == "Do the thing"
