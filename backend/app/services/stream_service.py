import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.character import Character
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.world import WorldBook
from app.services.llm_service import chat_stream, generate_title
from app.services.prompt_builder import build_messages, build_system_prompt, format_memories_block
from app.services.stream_registry import (
    register_stream,
    unregister_stream,
)
from app.services.task_tracker import create_background_task
from app.services.token_counter import estimate_tokens

logger = logging.getLogger(__name__)


async def send_message_stream(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_content: str,
) -> AsyncGenerator[str, None]:
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise ValueError("Conversation not found")

    character = await db.get(Character, conversation.character_id)
    world = await db.get(WorldBook, conversation.world_id)
    if not character or not world:
        raise ValueError("Character or world not found")

    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=user_content,
        token_count=estimate_tokens(user_content),
    )
    db.add(user_msg)
    conversation.message_count += 1
    await db.commit()

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    history = list(reversed(list(result.scalars().all())))

    system_prompt = build_system_prompt(world, character)

    # Retrieve relevant long-term memories
    memory_block = ""
    if settings.memory_enabled and conversation.user_id:
        try:
            from app.services.memory_service import retrieve_relevant_memories

            memories = await retrieve_relevant_memories(
                db=db,
                user_id=conversation.user_id,
                character_id=conversation.character_id,
                query_text=user_content,
            )
            memory_block = format_memories_block(memories)
        except Exception:
            logger.warning("Memory retrieval failed, continuing without memories", exc_info=True)

    messages = build_messages(system_prompt, history[:-1], user_content, memory_block=memory_block)

    cancel_event = register_stream(conversation_id)
    response_parts: list[str] = []
    try:
        async for token in chat_stream(messages):
            if cancel_event.is_set():
                logger.info("Stream cancelled: conv=%s", conversation_id)
                break
            response_parts.append(token)
            yield token
    finally:
        await unregister_stream(conversation_id)

        # Save assistant response even if client disconnected mid-stream
        full_response = "".join(response_parts)
        if full_response:
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                token_count=estimate_tokens(full_response),
            )
            db.add(assistant_msg)
            conversation.message_count += 1
            await db.commit()

            if conversation.message_count <= 3:
                create_background_task(
                    _generate_title_background(conversation_id, user_content, full_response),
                    name=f"title-{conversation_id}",
                )

            # Trigger async memory extraction (non-blocking)
            if settings.memory_enabled:
                from app.services.memory_trigger import maybe_extract_memories

                create_background_task(
                    maybe_extract_memories(
                        user_id=conversation.user_id,
                        character_id=conversation.character_id,
                        conversation_id=conversation.id,
                    ),
                    name=f"memory-{conversation_id}",
                )


async def _generate_title_background(
    conversation_id: uuid.UUID, user_content: str, full_response: str,
) -> None:
    """Generate conversation title in background with its own DB session."""
    try:
        title = await generate_title(user_content, full_response)
        if title:
            async with async_session_maker() as db:
                conv = await db.get(Conversation, conversation_id)
                if conv:
                    conv.title = title
                    await db.commit()
    except Exception:
        logger.exception("Background title generation failed: conv=%s", conversation_id)
