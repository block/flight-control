import asyncio
import logging

from orchestrator_worker.client import ServerClient
from orchestrator_worker.config import settings

logger = logging.getLogger(__name__)


class LogStreamer:
    """Batches log lines and sends them to the server periodically."""

    def __init__(self, client: ServerClient, run_id: str):
        self.client = client
        self.run_id = run_id
        self._buffer: list[dict] = []
        self._sequence = 0
        self._lock = asyncio.Lock()

    async def add_line(self, stream: str, line: str) -> None:
        async with self._lock:
            self._sequence += 1
            self._buffer.append(
                {"stream": stream, "line": line, "sequence": self._sequence}
            )

    async def flush(self) -> None:
        async with self._lock:
            if not self._buffer:
                return
            batch = self._buffer[:]
            self._buffer.clear()

        try:
            await self.client.post_logs(self.run_id, batch)
        except Exception as e:
            logger.error(f"Failed to send logs: {e}")
            # Put lines back
            async with self._lock:
                self._buffer = batch + self._buffer

    async def run_flush_loop(self) -> None:
        """Periodically flush buffered logs."""
        while True:
            await asyncio.sleep(settings.log_batch_interval)
            await self.flush()
