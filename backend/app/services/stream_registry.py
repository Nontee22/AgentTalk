"""In-process stream cancellation registry.

NOTE: This is process-local — in a multi-worker deployment (e.g. gunicorn with
multiple workers), a cancel request may land on a different worker than the one
running the stream. For production multi-worker setups, migrate to Redis pub/sub.
"""

import asyncio
import uuid

_cancel_events: dict[uuid.UUID, asyncio.Event] = {}


def register_stream(conversation_id: uuid.UUID) -> asyncio.Event:
    event = asyncio.Event()
    _cancel_events[conversation_id] = event
    return event


def cancel_stream(conversation_id: uuid.UUID) -> bool:
    event = _cancel_events.get(conversation_id)
    if event is None:
        return False
    event.set()
    return True


def unregister_stream(conversation_id: uuid.UUID) -> None:
    _cancel_events.pop(conversation_id, None)


def is_cancelled(conversation_id: uuid.UUID) -> bool:
    event = _cancel_events.get(conversation_id)
    return event is not None and event.is_set()
