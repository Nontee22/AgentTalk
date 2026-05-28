import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character
from app.models.world import WorldBook
from app.schemas.world import WorldBookCreate, WorldBookUpdate


async def get_worlds(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 12,
    tag: str | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    query = select(WorldBook)
    count_query = select(func.count(WorldBook.id))

    if tag:
        query = query.where(WorldBook.tags.contains([tag]))
        count_query = count_query.where(WorldBook.tags.contains([tag]))

    if search:
        pattern = f"%{search}%"
        query = query.where(
            WorldBook.name.ilike(pattern) | WorldBook.description.ilike(pattern)
        )
        count_query = count_query.where(
            WorldBook.name.ilike(pattern) | WorldBook.description.ilike(pattern)
        )

    total = await db.scalar(count_query) or 0

    query = query.order_by(WorldBook.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    worlds = result.scalars().all()

    items = []
    for w in worlds:
        char_count = await db.scalar(
            select(func.count(Character.id)).where(Character.world_id == w.id)
        )
        items.append({
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "tags": w.tags,
            "cover_image": w.cover_image,
            "is_preset": w.is_preset,
            "character_count": char_count or 0,
            "created_at": w.created_at,
        })

    return items, total


async def get_world(db: AsyncSession, world_id: uuid.UUID) -> dict | None:
    world = await db.get(WorldBook, world_id)
    if not world:
        return None

    char_count = await db.scalar(
        select(func.count(Character.id)).where(Character.world_id == world.id)
    )
    return {
        "id": world.id,
        "name": world.name,
        "description": world.description,
        "setting": world.setting,
        "rules": world.rules,
        "lore": world.lore,
        "factions": world.factions,
        "tags": world.tags,
        "cover_image": world.cover_image,
        "is_preset": world.is_preset,
        "character_count": char_count or 0,
        "created_at": world.created_at,
        "updated_at": world.updated_at,
    }


async def create_world(db: AsyncSession, data: WorldBookCreate) -> WorldBook:
    world = WorldBook(**data.model_dump())
    db.add(world)
    await db.commit()
    await db.refresh(world)
    return world


async def update_world(
    db: AsyncSession, world_id: uuid.UUID, data: WorldBookUpdate
) -> WorldBook | None:
    world = await db.get(WorldBook, world_id)
    if not world:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(world, field, value)

    await db.commit()
    await db.refresh(world)
    return world


async def delete_world(db: AsyncSession, world_id: uuid.UUID) -> bool:
    world = await db.get(WorldBook, world_id)
    if not world:
        return False

    await db.delete(world)
    await db.commit()
    return True
