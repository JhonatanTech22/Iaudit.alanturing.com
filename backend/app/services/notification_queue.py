"""IAudit - Async Notification Queue with Exponential Backoff.

Provides resilient delivery by retrying failed sends (Twilio/SMTP)
without external dependencies like Redis or Celery.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0   # 1s → 2s → 4s
MAX_DELAY_SECONDS = 16.0


@dataclass
class NotificationTask:
    """A unit of work for the queue."""
    task_id: str
    channel: str                          # "email" | "whatsapp"
    send_fn: Callable[..., Awaitable[bool]]  # async callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    attempt: int = 0
    created_at: float = field(default_factory=time.time)
    last_error: str | None = None


class NotificationQueue:
    """In-process async retry queue.

    Usage:
        queue = NotificationQueue()
        asyncio.create_task(queue.start_worker())

        await queue.enqueue(NotificationTask(
            task_id="boleto-123-email",
            channel="email",
            send_fn=send_email,
            args=("user@example.com", "Subject", "<html>..."),
        ))
    """

    def __init__(self, max_retries: int = MAX_RETRIES):
        self._queue: asyncio.Queue[NotificationTask] = asyncio.Queue()
        self._max_retries = max_retries
        self._running = False
        self._stats = {"enqueued": 0, "sent": 0, "failed": 0}
        # Optional: callback for persisting final failures
        self._on_failure: Callable | None = None

    # ── Public API ───────────────────────────────────────────────────

    async def enqueue(self, task: NotificationTask) -> None:
        """Add a notification to the queue."""
        await self._queue.put(task)
        self._stats["enqueued"] += 1
        logger.debug(f"[Queue] Enqueued {task.task_id} ({task.channel})")

    async def start_worker(self) -> None:
        """Start the consumer loop. Call once at app startup."""
        if self._running:
            return
        self._running = True
        logger.info("[Queue] Notification worker started.")
        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=5.0)
                await self._process(task)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Queue] Worker error: {e}")

    def stop_worker(self) -> None:
        """Signal the worker to stop."""
        self._running = False
        logger.info("[Queue] Worker stopping...")

    def set_failure_callback(self, callback: Callable) -> None:
        """Set a callback for tasks that exhaust all retries."""
        self._on_failure = callback

    @property
    def stats(self) -> dict:
        return {**self._stats, "pending": self._queue.qsize()}

    # ── Internal ─────────────────────────────────────────────────────

    async def _process(self, task: NotificationTask) -> None:
        """Try to send; requeue with backoff on failure."""
        task.attempt += 1
        try:
            success = await task.send_fn(*task.args, **task.kwargs)
            if success:
                self._stats["sent"] += 1
                logger.info(
                    f"[Queue] ✓ Delivered {task.task_id} ({task.channel}) "
                    f"on attempt {task.attempt}"
                )
                return

            raise RuntimeError("send_fn returned False")

        except Exception as e:
            task.last_error = str(e)
            logger.warning(
                f"[Queue] ✗ {task.task_id} attempt {task.attempt}/{self._max_retries}: {e}"
            )

            if task.attempt < self._max_retries:
                delay = min(
                    BASE_DELAY_SECONDS * (2 ** (task.attempt - 1)),
                    MAX_DELAY_SECONDS,
                )
                logger.info(f"[Queue] Retrying {task.task_id} in {delay}s...")
                await asyncio.sleep(delay)
                await self._queue.put(task)
            else:
                self._stats["failed"] += 1
                logger.error(
                    f"[Queue] ✗ FINAL FAIL {task.task_id} after {task.attempt} attempts: "
                    f"{task.last_error}"
                )
                if self._on_failure:
                    try:
                        await self._on_failure(task)
                    except Exception as cb_err:
                        logger.error(f"[Queue] Failure callback error: {cb_err}")


# ─── Singleton ───────────────────────────────────────────────────────

notification_queue = NotificationQueue()
