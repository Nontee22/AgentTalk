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
