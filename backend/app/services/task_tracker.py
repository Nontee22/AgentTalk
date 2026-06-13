# -*- coding: utf-8 -*-
"""Lightweight background task tracker.

Keeps strong references to fire-and-forget tasks so exceptions are
properly logged and tasks are awaited on shutdown.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task] = set()


def create_background_task(coro, *, name: str | None = None) -> asyncio.Task:
    """Create a tracked background task that auto-removes on completion."""
    task = asyncio.create_task(coro, name=name)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


async def shutdown_tasks(timeout: float = 10.0) -> None:
    """Wait for all background tasks to finish (called on app shutdown)."""
    if not _background_tasks:
        return
    logger.info("Waiting for %d background tasks to complete...", len(_background_tasks))
    _, pending = await asyncio.wait(_background_tasks, timeout=timeout)
    for t in pending:
        t.cancel()
    if pending:
        logger.warning("Cancelled %d background tasks on shutdown", len(pending))
