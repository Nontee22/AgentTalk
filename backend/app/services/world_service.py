import uuid

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.character import Character
from app.models.world import WorldBook
from app.schemas.world import WorldBookCreate, WorldBookUpdate


async def get_all_tags(db: AsyncSession) -> list[dict]:
    """Aggregate all tags from world_books with usage count, sorted by popularity."""
    result = await db.execute(
        text(
            "SELECT tag, COUNT(*) AS count "
            "FROM world_books, jsonb_array_elements_text(tags) AS tag "
            "GROUP BY tag "
            "ORDER BY count DESC, tag"
        )
    )
    return [{"name": row.tag, "count": row.count} for row in result.all()]


async def get_worlds(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 12,
    tag: str | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    # Subquery for character count — avoids N+1
    char_count_subq = (
        select(Character.world_id, func.count(Character.id).label("char_count"))
        .group_by(Character.world_id)
        .subquery()
    )

    base_filter = select(WorldBook)
    count_query = select(func.count(WorldBook.id))

    if tag:
        base_filter = base_filter.where(WorldBook.tags.contains([tag]))
        count_query = count_query.where(WorldBook.tags.contains([tag]))

    if search:
        pattern = f"%{search}%"
        cond = WorldBook.name.ilike(pattern) | WorldBook.description.ilike(pattern)
        base_filter = base_filter.where(cond)
        count_query = count_query.where(cond)

    total = await db.scalar(count_query) or 0

    query = (
        select(WorldBook, func.coalesce(char_count_subq.c.char_count, 0).label("character_count"))
        .outerjoin(char_count_subq, WorldBook.id == char_count_subq.c.world_id)
        .where(WorldBook.id.in_(
            base_filter.with_only_columns(WorldBook.id)
            .order_by(WorldBook.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ))
        .order_by(WorldBook.created_at.desc())
    )

    result = await db.execute(query)
    rows = result.all()

    items = []
    for w, char_count in rows:
        items.append({
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "tags": w.tags,
            "cover_image": w.cover_image,
            "is_preset": w.is_preset,
            "created_by": w.created_by,
            "character_count": char_count,
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


async def create_world(
    db: AsyncSession, data: WorldBookCreate, *, user_id: uuid.UUID | None = None
) -> WorldBook:
    world = WorldBook(**data.model_dump(), created_by=user_id)
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
