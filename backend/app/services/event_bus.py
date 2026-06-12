# -*- coding: utf-8 -*-
"""In-process event bus for pushing real-time events to connected clients.

Each user can have multiple SSE connections (multiple browser tabs).
Events are dispatched to all active queues for a given user_id.

NOTE: Process-local — in multi-worker deployments, migrate to Redis pub/sub.
"""

import asyncio
import json
import logging
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)

_subscribers: dict[uuid.UUID, list[asyncio.Queue]] = defaultdict(list)


def subscribe(user_id: uuid.UUID) -> asyncio.Queue:
    """Register a new SSE listener for a user. Returns the queue to read from."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=64)
    _subscribers[user_id].append(queue)
    logger.debug("EventBus: user=%s subscribed (total=%d)", user_id, len(_subscribers[user_id]))
    return queue


def unsubscribe(user_id: uuid.UUID, queue: asyncio.Queue) -> None:
    """Remove an SSE listener. Safe to call multiple times."""
    queues = _subscribers.get(user_id)
    if queues is None:
        return
    try:
        queues.remove(queue)
    except ValueError:
        pass
    if not queues:
        del _subscribers[user_id]
    logger.debug("EventBus: user=%s unsubscribed (remaining=%d)", user_id, len(_subscribers.get(user_id, [])))


async def publish(user_id: uuid.UUID, event: dict) -> int:
    """Push an event to all active listeners for a user.

    Returns the number of listeners that received the event.
    Drops the event silently if a queue is full (slow consumer).
    """
    queues = _subscribers.get(user_id)
    if not queues:
        return 0

    delivered = 0
    for q in queues:
        try:
            q.put_nowait(event)
            delivered += 1
        except asyncio.QueueFull:
            logger.warning("EventBus: queue full for user=%s, dropping event", user_id)

    return delivered
