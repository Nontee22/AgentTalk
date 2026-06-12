# -*- coding: utf-8 -*-
"""Server-Sent Events endpoint for real-time client notifications."""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.deps import get_current_user
from app.models.user import User
from app.services.event_bus import subscribe, unsubscribe

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])

HEARTBEAT_INTERVAL = 30  # seconds


@router.get("/stream")
async def event_stream(
    current_user: User = Depends(get_current_user),
):
    """SSE endpoint — pushes real-time events to the authenticated user.

    Events are JSON objects: {"event": "...", "data": {...}}
    A heartbeat comment is sent every 30s to keep the connection alive.
    """
    queue = subscribe(current_user.id)

    async def generate():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_INTERVAL)
                    event_type = event.get("event", "message")
                    event_data = json.dumps(event.get("data", {}), ensure_ascii=False)
                    yield f"event: {event_type}\ndata: {event_data}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat to keep connection alive
                    yield ": keepalive\n\n"
                except asyncio.CancelledError:
                    break
        finally:
            unsubscribe(current_user.id, queue)
            logger.debug("SSE stream closed for user=%s", current_user.id)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
