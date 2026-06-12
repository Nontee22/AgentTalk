import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.character import Character
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.models.world import WorldBook
from app.services.llm_service import chat_stream, generate_title
from app.services.prompt_builder import build_messages, build_system_prompt, format_memories_block
from app.services.stream_registry import (
    is_cancelled,
    register_stream,
    unregister_stream,
)
from app.services.token_counter import estimate_tokens

logger = logging.getLogger(__name__)


async def start_conversation(
    db: AsyncSession,
    character_id: uuid.UUID,
    world_id: uuid.UUID,
    *,
    user_id: uuid.UUID | None = None,
) -> tuple[Conversation, Message | None]:
    character = await db.get(Character, character_id)
    if not character:
        raise ValueError("Character not found")

    world = await db.get(WorldBook, world_id)
    if not world:
        raise ValueError("World not found")
    if character.world_id != world_id:
        raise ValueError("角色不属于该世界书")

    conversation = Conversation(
        character_id=character_id,
        world_id=world_id,
        user_id=user_id,
        title=f"与{character.name}的对话",
    )
    db.add(conversation)
    await db.flush()

    greeting_msg = None
    if character.greeting:
        greeting_msg = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=character.greeting,
            token_count=estimate_tokens(character.greeting),
        )
        db.add(greeting_msg)
        conversation.message_count = 1

    await db.commit()
    await db.refresh(conversation)
    if greeting_msg:
        await db.refresh(greeting_msg)

    return conversation, greeting_msg


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
        unregister_stream(conversation_id)

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
            title = await generate_title(user_content, full_response)
            if title:
                conversation.title = title
                await db.commit()

        # Trigger async memory extraction (non-blocking)
        if settings.memory_enabled:
            asyncio.create_task(
                _maybe_extract_memories(
                    user_id=conversation.user_id,
                    character_id=conversation.character_id,
                    conversation_id=conversation.id,
                )
            )


async def get_conversations(
    db: AsyncSession, *, user_id: uuid.UUID | None = None,
    page: int = 1, page_size: int = 20,
) -> tuple[list[dict], int]:
    last_msg_subq = (
        select(Message.content)
        .where(Message.conversation_id == Conversation.id)
        .order_by(Message.created_at.desc())
        .limit(1)
        .correlate(Conversation)
        .scalar_subquery()
    )

    base = select(Conversation)
    if user_id is not None:
        base = base.where(Conversation.user_id == user_id)

    total = await db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id
        ) if user_id else select(func.count(Conversation.id))
    ) or 0

    query = select(Conversation, last_msg_subq.label("last_message_content")).options(
        joinedload(Conversation.character)
    )
    if user_id is not None:
        query = query.where(Conversation.user_id == user_id)
    query = query.order_by(Conversation.updated_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    rows = result.unique().all()

    items = []
    for conv, last_msg_content in rows:
        items.append({
            "id": conv.id,
            "character_id": conv.character_id,
            "world_id": conv.world_id,
            "title": conv.title,
            "message_count": conv.message_count,
            "character_name": conv.character.name if conv.character else None,
            "character_avatar": conv.character.avatar if conv.character else None,
            "last_message": last_msg_content[:100] if last_msg_content else None,
            "updated_at": conv.updated_at,
        })

    return items, total


async def get_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Message], int]:
    total = await db.scalar(
        select(func.count(Message.id)).where(
            Message.conversation_id == conversation_id
        )
    ) or 0

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    messages = list(result.scalars().all())
    return messages, total


async def delete_conversation(db: AsyncSession, conversation_id: uuid.UUID) -> bool:
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        return False
    await db.delete(conversation)
    await db.commit()
    return True


async def _maybe_extract_memories(
    user_id: uuid.UUID | None,
    character_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> None:
    """Background task: extract memories if enough new messages since last extraction."""
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
