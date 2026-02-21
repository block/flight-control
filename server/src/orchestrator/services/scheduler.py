import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select

from orchestrator.database import async_session
from orchestrator.models.schedule import Schedule
from orchestrator.services import job_service
from orchestrator.services.schedule_service import compute_next_run

logger = logging.getLogger(__name__)

TICK_INTERVAL = 30  # seconds


async def _initialize_next_run_times():
    """Recompute next_run_at for all enabled schedules on startup."""
    async with async_session() as db:
        result = await db.execute(
            select(Schedule).where(Schedule.enabled == True)  # noqa: E712
        )
        schedules = list(result.scalars().all())
        for schedule in schedules:
            schedule.next_run_at = compute_next_run(schedule.cron_expression)
        await db.commit()
        logger.info("Initialized next_run_at for %d enabled schedules", len(schedules))


async def _tick():
    """Fire all schedules that are due."""
    now = datetime.now(UTC)
    async with async_session() as db:
        result = await db.execute(
            select(Schedule).where(
                Schedule.enabled == True,  # noqa: E712
                Schedule.next_run_at <= now,
            )
        )
        due_schedules = list(result.scalars().all())

        for schedule in due_schedules:
            try:
                run = await job_service.trigger_run(db, schedule.job_definition_id, workspace_id=schedule.workspace_id)
                schedule.last_run_at = now
                schedule.last_run_id = run.id
                logger.info(
                    "Schedule '%s' fired run %s for job %s",
                    schedule.name or schedule.id,
                    run.id,
                    schedule.job_definition_id,
                )
            except Exception:
                logger.exception(
                    "Failed to fire schedule '%s' for job %s",
                    schedule.name or schedule.id,
                    schedule.job_definition_id,
                )
            # Always advance next_run_at to prevent infinite retry
            schedule.next_run_at = compute_next_run(schedule.cron_expression)

        if due_schedules:
            await db.commit()


async def run_scheduler():
    """Background loop that checks for due schedules every TICK_INTERVAL seconds."""
    logger.info("Scheduler starting (tick every %ds)", TICK_INTERVAL)
    await _initialize_next_run_times()

    while True:
        try:
            await _tick()
        except Exception:
            logger.exception("Scheduler tick error")
        await asyncio.sleep(TICK_INTERVAL)
