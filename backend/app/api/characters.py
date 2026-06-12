import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import check_world_permission
from app.models.user import User
from app.models.world import WorldBook
from app.schemas.character import (
    CharacterCreate,
    CharacterDetail,
    CharacterSummary,
    CharacterUpdate,
)
from app.services import character_service

router = APIRouter(tags=["characters"])


@router.get(
    "/worlds/{world_id}/characters",
    response_model=list[CharacterSummary],
)
async def list_characters(
    world_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    characters = await character_service.get_characters(db, world_id)
    return [CharacterSummary.model_validate(c) for c in characters]


@router.get("/characters/{character_id}", response_model=CharacterDetail)
async def get_character(
    character_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    character = await character_service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return CharacterDetail.model_validate(character)


@router.post(
    "/worlds/{world_id}/characters",
    response_model=CharacterDetail,
    status_code=201,
)
async def create_character(
    world_id: uuid.UUID,
    data: CharacterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    world = await db.get(WorldBook, world_id)
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    check_world_permission(world, current_user, "创建角色")

    character = await character_service.create_character(db, world_id, data)
    return CharacterDetail.model_validate(character)


@router.put("/characters/{character_id}", response_model=CharacterDetail)
async def update_character(
    character_id: uuid.UUID,
    data: CharacterUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    character = await character_service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    world = await db.get(WorldBook, character.world_id)
    if world:
        check_world_permission(world, current_user, "编辑角色")

    character = await character_service.update_character(db, character_id, data)
    return CharacterDetail.model_validate(character)


@router.delete("/characters/{character_id}", status_code=204)
async def delete_character(
    character_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    character = await character_service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    world = await db.get(WorldBook, character.world_id)
    if world:
        check_world_permission(world, current_user, "删除角色")

    await character_service.delete_character(db, character_id)
