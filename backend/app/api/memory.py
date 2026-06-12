# -*- coding: utf-8 -*-
"""Memory API — list and delete character memories."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.memory import MemoryListResponse, MemoryOut
from app.services.memory_service import delete_memory, get_memories_for_pair

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("/character/{character_id}", response_model=MemoryListResponse)
async def list_memories(
    character_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all memories for current user + character pair."""
    memories = await get_memories_for_pair(db, current_user.id, character_id, limit=100)
    return MemoryListResponse(
        memories=[MemoryOut.model_validate(m) for m in memories],
        total=len(memories),
    )


@router.delete("/{memory_id}", status_code=204)
async def remove_memory(
    memory_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a specific memory."""
    deleted = await delete_memory(db, memory_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
