import asyncio
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from orchestrator.models.job_log import JobLog
from orchestrator.schemas.workers import LogLine

# In-memory subscribers for SSE log streaming
_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)


async def append_logs(db: AsyncSession, run_id: str, lines: list[LogLine]) -> int:
    logs = []
    for line in lines:
        log = JobLog(
            run_id=run_id,
            stream=line.stream,
            line=line.line,
            sequence=line.sequence,
        )
        logs.append(log)
    db.add_all(logs)
    await db.commit()

    # Notify SSE subscribers
    for queue in _subscribers.get(run_id, []):
        for line in lines:
            await queue.put(line)

    return len(logs)


async def get_logs(
    db: AsyncSession, run_id: str, after_sequence: int = 0
) -> list[JobLog]:
    result = await db.execute(
        select(JobLog)
        .where(JobLog.run_id == run_id, JobLog.sequence > after_sequence)
        .order_by(JobLog.sequence.asc())
    )
    return list(result.scalars().all())


def subscribe(run_id: str) -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue()
    _subscribers[run_id].append(queue)
    return queue


def unsubscribe(run_id: str, queue: asyncio.Queue) -> None:
    if run_id in _subscribers:
        _subscribers[run_id] = [q for q in _subscribers[run_id] if q is not queue]
        if not _subscribers[run_id]:
            del _subscribers[run_id]
