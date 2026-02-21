"""Download and write skill files to the worker's working directory."""

import hashlib
import logging
import os
import stat
from pathlib import Path

from orchestrator_worker.client import ServerClient

logger = logging.getLogger(__name__)


async def download_and_write_skills(
    client: ServerClient,
    skills: list[dict],
    work_dir: str,
) -> None:
    """Download skill files from the server and write them to disk.

    Args:
        client: Server HTTP client.
        skills: List of skill dicts from poll response (id, name, instructions, files).
        work_dir: Base working directory for the run.
    """
    if not skills:
        return

    # Write skills to .goose/skills/ so Goose discovers them natively
    skills_dir = Path(work_dir) / ".goose" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    for skill in skills:
        skill_id = skill["id"]
        skill_name = skill["name"]
        skill_dir = skills_dir / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        files = skill.get("files", [])
        for file_info in files:
            file_path = file_info["file_path"]
            expected_checksum = file_info["checksum_sha256"]

            try:
                data = await client.download_skill_file(skill_id, file_path)
            except Exception:
                logger.exception(f"Failed to download skill file {skill_name}/{file_path}")
                continue

            # Verify checksum
            actual_checksum = hashlib.sha256(data).hexdigest()
            if actual_checksum != expected_checksum:
                logger.warning(
                    f"Checksum mismatch for {skill_name}/{file_path}: "
                    f"expected {expected_checksum}, got {actual_checksum}"
                )
                continue

            # Write file
            dest = skill_dir / file_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)

            # Make scripts executable
            if file_path.startswith("scripts/"):
                dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        logger.info(f"Downloaded skill '{skill_name}' ({len(files)} files)")
