from unittest.mock import AsyncMock

import pytest

from orchestrator_worker.client import ServerClient


@pytest.fixture
def mock_client():
    client = AsyncMock(spec=ServerClient)
    client.post_logs = AsyncMock()
    client.upload_artifact = AsyncMock(return_value={"id": "art-1"})
    client.complete_run = AsyncMock()
    return client
