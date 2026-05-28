import logging
import uuid
from collections.abc import AsyncGenerator

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.character import Character
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.world import WorldBook
from app.services.llm_service import chat_stream
from app.services.prompt_builder import build_messages, build_system_prompt
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
) -> tuple[Conversation, Message | None]:
    character = await db.get(Character, character_id)
    if not character:
        raise ValueError("Character not found")

    conversation = Conversation(
        character_id=character_id,
        world_id=world_id,
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
        .order_by(Message.created_at)
    )
    history = list(result.scalars().all())

    system_prompt = build_system_prompt(world, character)
    messages = build_messages(system_prompt, history[:-1], user_content)

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


async def get_conversations(db: AsyncSession) -> list[dict]:
    last_msg_subq = (
        select(Message.content)
        .where(Message.conversation_id == Conversation.id)
        .order_by(Message.created_at.desc())
        .limit(1)
        .correlate(Conversation)
        .scalar_subquery()
    )

    result = await db.execute(
        select(Conversation, last_msg_subq.label("last_message_content"))
        .options(joinedload(Conversation.character))
        .order_by(Conversation.updated_at.desc())
    )
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

    return items


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
