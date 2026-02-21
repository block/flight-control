import json

from orchestrator_worker.config_writer import write_goose_config


def test_returns_none_for_empty_servers(tmp_path):
    result = write_goose_config([], str(tmp_path))
    assert result is None


def test_single_mcp_server(tmp_path):
    servers = [
        {
            "name": "my-server",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@my/server"],
        }
    ]
    path = write_goose_config(servers, str(tmp_path))

    assert path is not None
    with open(path) as f:
        config = json.load(f)

    assert "orchestrator" in config
    ext = config["orchestrator"]["extensions"]
    assert "my-server" in ext
    assert ext["my-server"]["command"] == "npx"
    assert ext["my-server"]["args"] == ["-y", "@my/server"]
    assert ext["my-server"]["type"] == "stdio"
    assert "env" not in ext["my-server"]


def test_multiple_mcp_servers(tmp_path):
    servers = [
        {"name": "server-a", "command": "cmd-a", "args": []},
        {"name": "server-b", "command": "cmd-b", "args": ["--flag"]},
    ]
    path = write_goose_config(servers, str(tmp_path))

    with open(path) as f:
        config = json.load(f)

    ext = config["orchestrator"]["extensions"]
    assert "server-a" in ext
    assert "server-b" in ext
    assert ext["server-a"]["command"] == "cmd-a"
    assert ext["server-b"]["command"] == "cmd-b"


def test_includes_env_when_present(tmp_path):
    servers = [
        {
            "name": "with-env",
            "command": "cmd",
            "args": [],
            "env": {"TOKEN": "secret"},
        }
    ]
    path = write_goose_config(servers, str(tmp_path))

    with open(path) as f:
        config = json.load(f)

    ext = config["orchestrator"]["extensions"]["with-env"]
    assert ext["env"] == {"TOKEN": "secret"}


def test_creates_config_directory_structure(tmp_path):
    servers = [{"name": "s", "command": "c", "args": []}]
    path = write_goose_config(servers, str(tmp_path))

    assert path is not None
    assert path.endswith("profiles.json")
    assert (tmp_path / ".config" / "goose").is_dir()
