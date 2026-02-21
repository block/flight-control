import asyncio
import logging
import platform
import signal
import sys

from orchestrator_worker.client import ServerClient
from orchestrator_worker.config import settings
from orchestrator_worker.runner import execute_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("orchestrator_worker")


async def main():
    client = ServerClient()
    worker_name = settings.worker_name or f"worker-{platform.node()}"

    # Parse labels
    labels = {}
    if settings.labels:
        for pair in settings.labels.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                labels[k.strip()] = v.strip()

    # Register
    logger.info(f"Registering worker '{worker_name}' with server {settings.server_url}")
    try:
        result = await client.register(worker_name, labels)
        worker_id = result["id"]
        logger.info(f"Registered as worker {worker_id}")
    except Exception as e:
        logger.error(f"Failed to register: {e}")
        sys.exit(1)

    # Shutdown handling
    shutdown = asyncio.Event()

    def handle_signal(*_):
        logger.info("Shutdown signal received")
        shutdown.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_event_loop().add_signal_handler(sig, handle_signal)

    # Main loop
    heartbeat_counter = 0
    while not shutdown.is_set():
        try:
            # Heartbeat every N poll cycles
            heartbeat_counter += 1
            if heartbeat_counter >= settings.heartbeat_interval // settings.poll_interval:
                await client.heartbeat(worker_id)
                heartbeat_counter = 0

            # Poll for jobs
            job = await client.poll(worker_id)
            if job:
                await execute_run(client, worker_id, job)
                # Heartbeat after completing a job
                await client.heartbeat(worker_id)
            else:
                # Wait before next poll
                try:
                    await asyncio.wait_for(shutdown.wait(), timeout=settings.poll_interval)
                except asyncio.TimeoutError:
                    pass

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(settings.poll_interval)

    logger.info("Worker shutting down")


if __name__ == "__main__":
    asyncio.run(main())
