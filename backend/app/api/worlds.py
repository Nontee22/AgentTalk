import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.world import (
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


@router.get("/{world_id}", response_model=WorldBookDetail)
async def get_world(
    world_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    world = await world_service.get_world(db, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return WorldBookDetail(**world)


@router.post("", response_model=WorldBookDetail, status_code=201)
async def create_world(
    data: WorldBookCreate,
    db: AsyncSession = Depends(get_db),
):
    world = await world_service.create_world(db, data)
    detail = await world_service.get_world(db, world.id)
    return WorldBookDetail(**detail)


@router.put("/{world_id}", response_model=WorldBookDetail)
async def update_world(
    world_id: uuid.UUID,
    data: WorldBookUpdate,
    db: AsyncSession = Depends(get_db),
):
    world = await world_service.update_world(db, world_id, data)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    detail = await world_service.get_world(db, world.id)
    return WorldBookDetail(**detail)


@router.delete("/{world_id}", status_code=204)
async def delete_world(
    world_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    deleted = await world_service.delete_world(db, world_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="World not found")
