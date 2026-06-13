import uuid
import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.character import Character
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.world import WorldBook
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
