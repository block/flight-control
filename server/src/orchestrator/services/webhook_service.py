"""Webhook notification service for run completion events."""

import asyncio
import hashlib
import hmac
import json
import logging

import httpx

from orchestrator.models.job_run import JobRun

logger = logging.getLogger(__name__)


def _compute_signature(payload: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook payload."""
    return hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()


def _build_payload(run: JobRun) -> dict:
    """Build webhook notification payload."""
    duration_seconds = None
    if run.started_at and run.completed_at:
        duration_seconds = (run.completed_at - run.started_at).total_seconds()

    return {
        "run_id": run.id,
        "job_id": run.job_definition_id,
        "status": run.status,
        "exit_code": run.exit_code,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "duration_seconds": duration_seconds,
    }


async def send_webhook(run: JobRun) -> None:
    """
    Send webhook notification for a completed run.
    
    This is designed to be called with asyncio.create_task() so it doesn't
    block the run completion response.
    """
    if not run.webhook_url:
        return

    payload = _build_payload(run)
    payload_bytes = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "FlightControl-Webhook/1.0",
    }

    # Add HMAC signature if secret is configured
    if run.webhook_secret:
        signature = _compute_signature(payload_bytes, run.webhook_secret)
        headers["X-FlightControl-Signature"] = f"sha256={signature}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                run.webhook_url,
                content=payload_bytes,
                headers=headers,
            )
            response.raise_for_status()
            logger.info(
                f"Webhook sent successfully for run {run.id} to {run.webhook_url}"
            )
    except httpx.HTTPStatusError as e:
        logger.warning(
            f"Webhook failed for run {run.id}: HTTP {e.response.status_code}"
        )
    except httpx.RequestError as e:
        logger.warning(
            f"Webhook failed for run {run.id}: {type(e).__name__}: {e}"
        )
    except Exception as e:
        logger.error(
            f"Unexpected error sending webhook for run {run.id}: {e}"
        )


def fire_webhook(run: JobRun) -> None:
    """
    Fire webhook notification asynchronously (non-blocking).
    
    Call this from the completion handler to send webhook without
    blocking the response.
    """
    if run.webhook_url:
        asyncio.create_task(send_webhook(run))
