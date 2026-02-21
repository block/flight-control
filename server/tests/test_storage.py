import pytest

from orchestrator.storage import LocalStorageBackend


@pytest.fixture
def storage(tmp_path):
    return LocalStorageBackend(str(tmp_path))


@pytest.mark.asyncio
async def test_save_and_read(storage):
    data = b"hello world"
    await storage.save("test.txt", data)
    result = await storage.read("test.txt")
    assert result == data


@pytest.mark.asyncio
async def test_save_nested_path(storage):
    data = b"nested content"
    await storage.save("a/b/c/file.txt", data)
    result = await storage.read("a/b/c/file.txt")
    assert result == data


@pytest.mark.asyncio
async def test_delete(storage):
    await storage.save("to_delete.txt", b"bye")
    await storage.delete("to_delete.txt")
    with pytest.raises(FileNotFoundError):
        await storage.read("to_delete.txt")


@pytest.mark.asyncio
async def test_delete_nonexistent(storage):
    # Should not raise
    await storage.delete("nonexistent.txt")


@pytest.mark.asyncio
async def test_overwrite(storage):
    await storage.save("file.txt", b"first")
    await storage.save("file.txt", b"second")
    result = await storage.read("file.txt")
    assert result == b"second"
