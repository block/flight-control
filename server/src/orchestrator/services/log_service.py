import asyncio
import logging
import re
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.models.artifact import Artifact
from orchestrator.schemas.workers import LogLine
from orchestrator.services import artifact_service

logger = logging.getLogger(__name__)

# In-memory subscribers for SSE log streaming
_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

_LOG_LINE_RE = re.compile(r"^\[(stdout|stderr)\] (.*)$")


@dataclass
class LogEntry:
    stream: str
    line: str
    sequence: int


async def append_logs(db: AsyncSession, run_id: str, lines: list[LogLine]) -> int:
    # SSE pub/sub only — no DB writes
    for queue in _subscribers.get(run_id, []):
        for line in lines:
            await queue.put(line)

    return len(lines)


async def get_logs(
    db: AsyncSession, run_id: str, after_sequence: int = 0
) -> list[LogEntry]:
    """Read logs from the run-output.log artifact."""
    artifacts = await artifact_service.list_artifacts(db, run_id)
    log_artifact: Artifact | None = None
    for a in artifacts:
        if a.filename == "run-output.log":
            log_artifact = a
            break

    if not log_artifact:
        return []

    data = await artifact_service.read_artifact_data(log_artifact)
    text = data.decode("utf-8", errors="replace")

    entries: list[LogEntry] = []
    for seq, raw_line in enumerate(text.splitlines(), start=1):
        if seq <= after_sequence:
            continue
        match = _LOG_LINE_RE.match(raw_line)
        if match:
            entries.append(LogEntry(stream=match.group(1), line=match.group(2), sequence=seq))
        else:
            entries.append(LogEntry(stream="stdout", line=raw_line, sequence=seq))

    return entries


def subscribe(run_id: str) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers[run_id].append(queue)
    return queue


def unsubscribe(run_id: str, queue: asyncio.Queue) -> None:
    if run_id in _subscribers:
        _subscribers[run_id] = [q for q in _subscribers[run_id] if q is not queue]
        if not _subscribers[run_id]:
            del _subscribers[run_id]
