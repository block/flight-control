import hashlib
import os
import stat
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from orchestrator_worker.skill_writer import download_and_write_skills


@pytest.fixture
def mock_client():
    client = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_download_and_write_skills(tmp_path, mock_client):
    script_content = b"#!/bin/bash\necho hello"
    readme_content = b"# Reference\nSome docs."
    skill_md_content = b"---\nname: test-skill\n---\nInstructions here."

    mock_client.download_skill_file = AsyncMock(side_effect=lambda sid, fp: {
        "SKILL.md": skill_md_content,
        "scripts/run.sh": script_content,
        "references/readme.md": readme_content,
    }[fp])

    skills = [{
        "id": "abc123",
        "name": "test-skill",
        "instructions": "Instructions here.",
        "files": [
            {
                "file_path": "SKILL.md",
                "size_bytes": len(skill_md_content),
                "checksum_sha256": hashlib.sha256(skill_md_content).hexdigest(),
                "content_type": "text/markdown",
            },
            {
                "file_path": "scripts/run.sh",
                "size_bytes": len(script_content),
                "checksum_sha256": hashlib.sha256(script_content).hexdigest(),
                "content_type": "application/x-sh",
            },
            {
                "file_path": "references/readme.md",
                "size_bytes": len(readme_content),
                "checksum_sha256": hashlib.sha256(readme_content).hexdigest(),
                "content_type": "text/markdown",
            },
        ],
    }]

    await download_and_write_skills(mock_client, skills, str(tmp_path))

    # Verify files exist
    skill_dir = tmp_path / ".goose" / "skills" / "test-skill"
    assert (skill_dir / "SKILL.md").exists()
    assert (skill_dir / "scripts" / "run.sh").exists()
    assert (skill_dir / "references" / "readme.md").exists()

    # Verify content
    assert (skill_dir / "scripts" / "run.sh").read_bytes() == script_content

    # Verify scripts are executable
    run_sh = skill_dir / "scripts" / "run.sh"
    assert run_sh.stat().st_mode & stat.S_IEXEC


@pytest.mark.asyncio
async def test_checksum_mismatch_skips_file(tmp_path, mock_client):
    content = b"some content"
    mock_client.download_skill_file = AsyncMock(return_value=content)

    skills = [{
        "id": "abc123",
        "name": "bad-checksum",
        "instructions": "Test",
        "files": [
            {
                "file_path": "data.txt",
                "size_bytes": len(content),
                "checksum_sha256": "wrong_checksum_value",
                "content_type": "text/plain",
            },
        ],
    }]

    await download_and_write_skills(mock_client, skills, str(tmp_path))

    # File should not be written due to checksum mismatch
    assert not (tmp_path / ".goose" / "skills" / "bad-checksum" / "data.txt").exists()


@pytest.mark.asyncio
async def test_empty_skills_list(tmp_path, mock_client):
    await download_and_write_skills(mock_client, [], str(tmp_path))
    assert not (tmp_path / ".goose" / "skills").exists()


@pytest.mark.asyncio
async def test_download_error_continues(tmp_path, mock_client):
    good_content = b"good file"
    mock_client.download_skill_file = AsyncMock(side_effect=[
        Exception("Network error"),
        good_content,
    ])

    skills = [{
        "id": "abc123",
        "name": "partial-skill",
        "instructions": "Test",
        "files": [
            {
                "file_path": "bad.txt",
                "size_bytes": 10,
                "checksum_sha256": "irrelevant",
                "content_type": "text/plain",
            },
            {
                "file_path": "good.txt",
                "size_bytes": len(good_content),
                "checksum_sha256": hashlib.sha256(good_content).hexdigest(),
                "content_type": "text/plain",
            },
        ],
    }]

    await download_and_write_skills(mock_client, skills, str(tmp_path))

    # Bad file not written, good file written
    assert not (tmp_path / ".goose" / "skills" / "partial-skill" / "bad.txt").exists()
    assert (tmp_path / ".goose" / "skills" / "partial-skill" / "good.txt").exists()
