import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestrator_worker.agents.goose import GooseRunner


def _mock_process():
    """Create a mock process that yields no output and exits 0."""
    proc = AsyncMock()
    proc.stdout = AsyncMock()
    proc.stderr = AsyncMock()
    # readline returns empty bytes to signal EOF
    proc.stdout.readline = AsyncMock(return_value=b"")
    proc.stderr.readline = AsyncMock(return_value=b"")
    proc.wait = AsyncMock(return_value=0)
    return proc


def _mock_settings(server_url="http://test-server:8080", api_key="test-key"):
    s = MagicMock()
    s.server_url = server_url
    s.api_key = api_key
    return s


async def _drain(runner, **kwargs):
    """Run the runner and collect all output, returning (cmd, env) from the mock."""
    lines = []
    async for stream, line in runner.run(**kwargs):
        lines.append((stream, line))
    return lines


@pytest.mark.asyncio
async def test_basic_command_structure(tmp_path):
    proc = _mock_process()
    captured = {}

    async def capture_exec(*args, **kwargs):
        captured["cmd"] = args
        captured["env"] = kwargs.get("env")
        return proc

    with (
        patch("asyncio.create_subprocess_exec", side_effect=capture_exec),
        patch("orchestrator_worker.agents.goose.settings", _mock_settings()),
    ):
        runner = GooseRunner()
        await _drain(
            runner,
            task_prompt="Do something",
            agent_config={"provider": "openai", "model": "gpt-4"},
            mcp_servers=[],
            env_vars={},
            credentials={},
            work_dir=str(tmp_path),
            timeout_seconds=60,
            run_id="",
        )

    cmd = captured["cmd"]
    assert cmd[0] == "goose"
    assert cmd[1] == "run"
    assert "--no-session" in cmd
    assert "--output-format" in cmd
    idx_fmt = cmd.index("--output-format")
    assert cmd[idx_fmt + 1] == "stream-json"
    # Default max turns should always be present
    assert "--max-turns" in cmd
    assert "-t" in cmd
    idx = cmd.index("-t")
    assert cmd[idx + 1] == "Do something"
    assert "--provider" in cmd
    assert "--model" in cmd
    # No system prompt when run_id is empty
    assert "--system" not in cmd


@pytest.mark.asyncio
async def test_system_prompt_with_run_id(tmp_path):
    proc = _mock_process()
    captured = {}

    async def capture_exec(*args, **kwargs):
        captured["cmd"] = args
        captured["env"] = kwargs.get("env")
        return proc

    with (
        patch("asyncio.create_subprocess_exec", side_effect=capture_exec),
        patch("orchestrator_worker.agents.goose.settings", _mock_settings()),
    ):
        runner = GooseRunner()
        await _drain(
            runner,
            task_prompt="Do something",
            agent_config={},
            mcp_servers=[],
            env_vars={},
            credentials={},
            work_dir=str(tmp_path),
            timeout_seconds=60,
            run_id="run-123",
        )

    cmd = captured["cmd"]
    assert "--system" in cmd
    idx = cmd.index("--system")
    system_prompt = cmd[idx + 1]
    assert "artifact" in system_prompt.lower() or "upload" in system_prompt.lower()
    assert "FLIGHT_CONTROL_UPLOAD_URL" in system_prompt


@pytest.mark.asyncio
async def test_no_system_prompt_without_run_id(tmp_path):
    proc = _mock_process()
    captured = {}

    async def capture_exec(*args, **kwargs):
        captured["cmd"] = args
        return proc

    with (
        patch("asyncio.create_subprocess_exec", side_effect=capture_exec),
        patch("orchestrator_worker.agents.goose.settings", _mock_settings()),
    ):
        runner = GooseRunner()
        await _drain(
            runner,
            task_prompt="Task",
            agent_config={},
            mcp_servers=[],
            env_vars={},
            credentials={},
            work_dir=str(tmp_path),
            timeout_seconds=60,
            run_id="",
        )

    assert "--system" not in captured["cmd"]


@pytest.mark.asyncio
async def test_artifact_env_vars_with_run_id(tmp_path):
    proc = _mock_process()
    captured = {}

    async def capture_exec(*args, **kwargs):
        captured["env"] = kwargs.get("env")
        return proc

    settings = _mock_settings(server_url="http://srv:8080", api_key="my-key")

    with (
        patch("asyncio.create_subprocess_exec", side_effect=capture_exec),
        patch("orchestrator_worker.agents.goose.settings", settings),
    ):
        runner = GooseRunner()
        await _drain(
            runner,
            task_prompt="Task",
            agent_config={},
            mcp_servers=[],
            env_vars={},
            credentials={},
            work_dir=str(tmp_path),
            timeout_seconds=60,
            run_id="run-456",
        )

    env = captured["env"]
    assert env["FLIGHT_CONTROL_UPLOAD_URL"] == "http://srv:8080/api/v1/workers/runs/run-456/artifacts"
    assert env["FLIGHT_CONTROL_API_KEY"] == "my-key"


@pytest.mark.asyncio
async def test_no_artifact_env_vars_without_run_id(tmp_path):
    proc = _mock_process()
    captured = {}

    async def capture_exec(*args, **kwargs):
        captured["env"] = kwargs.get("env")
        return proc

    with (
        patch("asyncio.create_subprocess_exec", side_effect=capture_exec),
        patch("orchestrator_worker.agents.goose.settings", _mock_settings()),
    ):
        runner = GooseRunner()
        await _drain(
            runner,
            task_prompt="Task",
            agent_config={},
            mcp_servers=[],
            env_vars={},
            credentials={},
            work_dir=str(tmp_path),
            timeout_seconds=60,
            run_id="",
        )

    env = captured["env"]
    assert "FLIGHT_CONTROL_UPLOAD_URL" not in env
    assert "FLIGHT_CONTROL_API_KEY" not in env


@pytest.mark.asyncio
async def test_max_turns(tmp_path):
    proc = _mock_process()
    captured = {}

    async def capture_exec(*args, **kwargs):
        captured["cmd"] = args
        return proc

    with (
        patch("asyncio.create_subprocess_exec", side_effect=capture_exec),
        patch("orchestrator_worker.agents.goose.settings", _mock_settings()),
    ):
        runner = GooseRunner()
        await _drain(
            runner,
            task_prompt="Task",
            agent_config={"max_turns": 5},
            mcp_servers=[],
            env_vars={},
            credentials={},
            work_dir=str(tmp_path),
            timeout_seconds=60,
            run_id="",
        )

    cmd = captured["cmd"]
    assert "--max-turns" in cmd
    idx = cmd.index("--max-turns")
    assert cmd[idx + 1] == "5"


@pytest.mark.asyncio
async def test_mcp_config_sets_profile_env(tmp_path):
    proc = _mock_process()
    captured = {}

    async def capture_exec(*args, **kwargs):
        captured["env"] = kwargs.get("env")
        return proc

    servers = [{"name": "test-mcp", "command": "npx", "args": ["-y", "test"]}]

    with (
        patch("asyncio.create_subprocess_exec", side_effect=capture_exec),
        patch("orchestrator_worker.agents.goose.settings", _mock_settings()),
    ):
        runner = GooseRunner()
        await _drain(
            runner,
            task_prompt="Task",
            agent_config={},
            mcp_servers=servers,
            env_vars={},
            credentials={},
            work_dir=str(tmp_path),
            timeout_seconds=60,
            run_id="",
        )

    env = captured["env"]
    assert env["GOOSE_PROFILE"] == "orchestrator"
    assert "GOOSE_CONFIG_DIR" in env


@pytest.mark.asyncio
async def test_env_var_merging(tmp_path):
    proc = _mock_process()
    captured = {}

    async def capture_exec(*args, **kwargs):
        captured["env"] = kwargs.get("env")
        return proc

    with (
        patch("asyncio.create_subprocess_exec", side_effect=capture_exec),
        patch("orchestrator_worker.agents.goose.settings", _mock_settings()),
    ):
        runner = GooseRunner()
        await _drain(
            runner,
            task_prompt="Task",
            agent_config={},
            mcp_servers=[],
            env_vars={"MY_VAR": "val1"},
            credentials={"SECRET": "val2"},
            work_dir=str(tmp_path),
            timeout_seconds=60,
            run_id="",
        )

    env = captured["env"]
    assert env["MY_VAR"] == "val1"
    assert env["SECRET"] == "val2"
