"""Background task: extract memories from conversations when enough new messages accumulate."""

import logging
import uuid

from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.character import Character
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User

logger = logging.getLogger(__name__)


async def maybe_extract_memories(
    user_id: uuid.UUID | None,
    character_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> None:
    """Extract memories if enough new messages since last extraction.

    Runs as a detached background task with its own DB session.
    """
    if not user_id:
        return

    try:
        async with async_session_maker() as db:
            conversation = await db.get(Conversation, conversation_id)
            if not conversation:
                return

            delta = conversation.message_count - conversation.last_memory_extraction_at_count
            if delta < settings.memory_extraction_min_messages:
                return

            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(settings.memory_extraction_context_messages)
            )
            messages = [
                {"role": m.role, "content": m.content}
                for m in reversed(list(result.scalars()))
            ]

            character = await db.get(Character, character_id)
            user = await db.get(User, user_id)
            if not character or not user:
                return

            from app.services.memory_service import extract_memories

            await extract_memories(
                db=db,
                user_id=user_id,
                character_id=character_id,
                conversation_id=conversation_id,
                character_name=character.name,
                username=user.nickname or user.username,
                messages=messages,
                character_identity=character.identity or "",
                character_personality=character.personality or "",
            )

            conversation.last_memory_extraction_at_count = conversation.message_count
            await db.commit()

            # Notify connected clients that new memories are available
            from app.services.event_bus import publish

            await publish(user_id, {
                "event": "memory_ready",
                "data": {
                    "character_id": str(character_id),
                },
            })

    except Exception:
        logger.exception("Memory extraction failed for conv=%s", conversation_id)
