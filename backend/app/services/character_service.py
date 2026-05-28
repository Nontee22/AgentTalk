import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character
from app.models.world import WorldBook
from app.schemas.character import CharacterCreate, CharacterUpdate


async def get_characters(
    db: AsyncSession, world_id: uuid.UUID
) -> list[Character]:
    result = await db.execute(
        select(Character)
        .where(Character.world_id == world_id)
        .order_by(Character.created_at)
    )
    return list(result.scalars().all())


async def get_character(db: AsyncSession, character_id: uuid.UUID) -> Character | None:
    return await db.get(Character, character_id)


async def create_character(
    db: AsyncSession, world_id: uuid.UUID, data: CharacterCreate
) -> Character | None:
    world = await db.get(WorldBook, world_id)
    if not world:
        return None

    character = Character(world_id=world_id, **data.model_dump())
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


async def update_character(
    db: AsyncSession, character_id: uuid.UUID, data: CharacterUpdate
) -> Character | None:
    character = await db.get(Character, character_id)
    if not character:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(character, field, value)

    await db.commit()
    await db.refresh(character)
    return character


async def delete_character(db: AsyncSession, character_id: uuid.UUID) -> bool:
    character = await db.get(Character, character_id)
    if not character:
        return False

    await db.delete(character)
    await db.commit()
    return True
