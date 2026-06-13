import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import check_world_permission
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.world import (
    TagCount,
    WorldBookCreate,
    WorldBookDetail,
    WorldBookSummary,
    WorldBookUpdate,
)
from app.services import world_service

router = APIRouter(prefix="/worlds", tags=["worlds"])


@router.get("", response_model=PaginatedResponse[WorldBookSummary])
async def list_worlds(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    tag: str | None = None,
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await world_service.get_worlds(
        db, page=page, page_size=page_size, tag=tag, search=search
    )
    return PaginatedResponse(
        items=[WorldBookSummary(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/tags", response_model=list[TagCount])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return [TagCount(**t) for t in await world_service.get_all_tags(db)]


@router.get("/{world_id}", response_model=WorldBookDetail)
async def get_world(
    world_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    world = await world_service.get_world(db, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return WorldBookDetail(**world)


@router.post("", response_model=WorldBookDetail, status_code=201)
async def create_world(
    data: WorldBookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="仅管理员可创建世界书")
    world = await world_service.create_world(db, data, user_id=current_user.id)
    detail = await world_service.get_world(db, world.id)
    return WorldBookDetail(**detail)


@router.put("/{world_id}", response_model=WorldBookDetail)
async def update_world(
    world_id: uuid.UUID,
    data: WorldBookUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.get(world_service.WorldBook, world_id)
    if not existing:
        raise HTTPException(status_code=404, detail="World not found")
    check_world_permission(existing, current_user, "编辑")

    world = await world_service.update_world(db, world_id, data)
    detail = await world_service.get_world(db, world.id)
    return WorldBookDetail(**detail)


@router.delete("/{world_id}", status_code=204)
async def delete_world(
    world_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.get(world_service.WorldBook, world_id)
    if not existing:
        raise HTTPException(status_code=404, detail="World not found")
    check_world_permission(existing, current_user, "删除")

    await world_service.delete_world(db, world_id)
