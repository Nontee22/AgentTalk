"""Redis-backed stream cancellation registry for multi-worker deployments.

Uses Redis keys to track active streams and pub/sub channels to broadcast
cancel signals across all workers. The worker hosting the stream receives
the cancel message and sets the local asyncio.Event.
"""

import asyncio
import logging
import uuid

from app.core.database import redis_client

logger = logging.getLogger(__name__)

# Local events — only the worker hosting the stream has an entry
_local_events: dict[uuid.UUID, asyncio.Event] = {}
_subscriber_tasks: dict[uuid.UUID, asyncio.Task] = {}


def _stream_key(conversation_id: uuid.UUID) -> str:
    return f"stream:{conversation_id}"


def _cancel_channel(conversation_id: uuid.UUID) -> str:
    return f"stream_cancel:{conversation_id}"


async def _listen_for_cancel(conversation_id: uuid.UUID) -> None:
    """Background task: subscribe to Redis cancel channel and set local event on message."""
    channel = _cancel_channel(conversation_id)
    pubsub = redis_client.pubsub()
    try:
        await pubsub.subscribe(channel)
        async for message in pubsub.listen():
            if message["type"] == "message":
                event = _local_events.get(conversation_id)
                if event:
                    event.set()
                break
    except asyncio.CancelledError:
        pass
    except Exception:
        logger.warning("stream_registry listener error for conv=%s", conversation_id, exc_info=True)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()


def register_stream(conversation_id: uuid.UUID) -> asyncio.Event:
    """Register a new active stream. Returns an Event that is set on cancellation."""
    event = asyncio.Event()
    _local_events[conversation_id] = event

    # Mark stream as active in Redis (TTL 5min as safety net)
    asyncio.create_task(redis_client.set(_stream_key(conversation_id), "active", ex=300))

    # Start listening for cancel signal
    task = asyncio.create_task(_listen_for_cancel(conversation_id))
    _subscriber_tasks[conversation_id] = task

    return event


async def cancel_stream(conversation_id: uuid.UUID) -> bool:
    """Broadcast cancel signal via Redis pub/sub. Works across workers."""
    key = _stream_key(conversation_id)
    exists = await redis_client.exists(key)
    if not exists:
        return False

    await redis_client.publish(_cancel_channel(conversation_id), "cancel")
    await redis_client.delete(key)
    return True


async def unregister_stream(conversation_id: uuid.UUID) -> None:
    """Clean up after stream ends."""
    _local_events.pop(conversation_id, None)

    task = _subscriber_tasks.pop(conversation_id, None)
    if task and not task.done():
        task.cancel()

    await redis_client.delete(_stream_key(conversation_id))


def is_cancelled(conversation_id: uuid.UUID) -> bool:
    """Check if the stream has been cancelled (local check only)."""
    event = _local_events.get(conversation_id)
    return event is not None and event.is_set()
