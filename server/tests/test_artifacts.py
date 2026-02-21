import hashlib

import pytest
import pytest_asyncio

from orchestrator.models.artifact import Artifact
from orchestrator.services import artifact_service


@pytest_asyncio.fixture
async def storage_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("orchestrator.storage.settings.artifact_storage_path", str(tmp_path))
    return tmp_path


@pytest.mark.asyncio
async def test_save_artifact(db, storage_dir):
    data = b"log line 1\nlog line 2\n"
    artifact = await artifact_service.save_artifact(
        db, run_id="run123", filename="output.log", data=data, content_type="text/plain"
    )
    assert artifact.run_id == "run123"
    assert artifact.filename == "output.log"
    assert artifact.content_type == "text/plain"
    assert artifact.size_bytes == len(data)
    assert artifact.checksum_sha256 == hashlib.sha256(data).hexdigest()
    assert artifact.storage_path == "run123/output.log"


@pytest.mark.asyncio
async def test_list_artifacts(db, storage_dir):
    await artifact_service.save_artifact(
        db, run_id="run1", filename="a.txt", data=b"aaa", content_type="text/plain"
    )
    await artifact_service.save_artifact(
        db, run_id="run1", filename="b.txt", data=b"bbb", content_type="text/plain"
    )
    await artifact_service.save_artifact(
        db, run_id="run2", filename="c.txt", data=b"ccc", content_type="text/plain"
    )

    artifacts = await artifact_service.list_artifacts(db, "run1")
    assert len(artifacts) == 2
    assert {a.filename for a in artifacts} == {"a.txt", "b.txt"}


@pytest.mark.asyncio
async def test_read_artifact_data(db, storage_dir):
    data = b"hello artifact"
    artifact = await artifact_service.save_artifact(
        db, run_id="run1", filename="test.bin", data=data, content_type="application/octet-stream"
    )
    read_data = await artifact_service.read_artifact_data(artifact)
    assert read_data == data


@pytest.mark.asyncio
async def test_checksum_verification(db, storage_dir):
    data = b"checksum test data"
    artifact = await artifact_service.save_artifact(
        db, run_id="run1", filename="check.txt", data=data, content_type="text/plain"
    )
    expected = hashlib.sha256(data).hexdigest()
    assert artifact.checksum_sha256 == expected


@pytest.mark.asyncio
async def test_empty_artifact(db, storage_dir):
    artifact = await artifact_service.save_artifact(
        db, run_id="run1", filename="empty.txt", data=b"", content_type="text/plain"
    )
    assert artifact.size_bytes == 0
    read_data = await artifact_service.read_artifact_data(artifact)
    assert read_data == b""
