import json
import os
import tempfile
from pathlib import Path


def write_goose_config(mcp_servers: list[dict], work_dir: str) -> str | None:
    """Write Goose MCP server config (goose config format) to a temp directory.
    Returns the path to the config file, or None if no MCP servers configured."""
    if not mcp_servers:
        return None

    # Build Goose-compatible config
    extensions = {}
    for server in mcp_servers:
        name = server.get("name", "mcp-server")
        extensions[name] = {
            "type": server.get("type", "stdio"),
            "command": server.get("command", ""),
            "args": server.get("args", []),
        }
        if server.get("env"):
            extensions[name]["env"] = server["env"]

    config = {"extensions": extensions}

    config_path = os.path.join(work_dir, "goose-config.yaml")
    # Write as YAML-like format that goose understands
    # Actually write as JSON profile for simplicity
    profile_dir = os.path.join(work_dir, ".config", "goose")
    os.makedirs(profile_dir, exist_ok=True)
    profile_path = os.path.join(profile_dir, "profiles.json")

    with open(profile_path, "w") as f:
        json.dump(
            {
                "orchestrator": {
                    "extensions": extensions,
                }
            },
            f,
            indent=2,
        )

    return profile_path
