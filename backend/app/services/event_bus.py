# -*- coding: utf-8 -*-
"""Redis-backed event bus for pushing real-time events to connected clients.

Uses Redis pub/sub to broadcast events across all workers. Each SSE connection
subscribes to a Redis channel and bridges messages into a local asyncio.Queue.

NOTE: Process-local queues are still used per SSE connection — Redis pub/sub
delivers the cross-worker broadcast, while the queue interface remains unchanged
for consumers (api/events.py).
"""

import asyncio
import json
import logging
import uuid

from app.core.database import redis_client

logger = logging.getLogger(__name__)


def _channel(user_id: uuid.UUID) -> str:
    return f"events:{user_id}"


# Track active subscriptions so we can clean up
_subscriptions: dict[int, tuple[asyncio.Task, object]] = {}  # id(queue) → (task, pubsub)


def subscribe(user_id: uuid.UUID) -> asyncio.Queue:
    """Register a new SSE listener for a user. Returns the queue to read from.

    Internally starts a background task that bridges Redis pub/sub messages
    into the returned asyncio.Queue.
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=64)

    async def _bridge() -> None:
        channel = _channel(user_id)
        pubsub = redis_client.pubsub()
        # Store pubsub ref for cleanup
        _subscriptions[id(queue)] = (asyncio.current_task(), pubsub)  # type: ignore
        try:
            await pubsub.subscribe(channel)
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event = json.loads(message["data"])
                        queue.put_nowait(event)
                    except (json.JSONDecodeError, asyncio.QueueFull):
                        logger.warning("EventBus: failed to deliver event for user=%s", user_id)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.warning("EventBus: subscriber error for user=%s", user_id, exc_info=True)
        finally:
            try:
                await pubsub.unsubscribe(channel)
                await pubsub.aclose()
            except Exception:
                pass

    task = asyncio.create_task(_bridge())
    _subscriptions[id(queue)] = (task, None)  # pubsub set inside _bridge

    logger.debug("EventBus: user=%s subscribed", user_id)
    return queue


def unsubscribe(user_id: uuid.UUID, queue: asyncio.Queue) -> None:
    """Remove an SSE listener. Cancels the background Redis subscriber task."""
    entry = _subscriptions.pop(id(queue), None)
    if entry:
        task, _ = entry
        if task and not task.done():
            task.cancel()
    logger.debug("EventBus: user=%s unsubscribed", user_id)


async def publish(user_id: uuid.UUID, event: dict) -> int:
    """Publish an event to all workers via Redis pub/sub.

    Returns the number of Redis subscribers that received the message
    (not the number of SSE connections — one worker may have multiple).
    """
    channel = _channel(user_id)
    data = json.dumps(event, ensure_ascii=False)
    receivers = await redis_client.publish(channel, data)
    return receivers
