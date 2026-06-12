# -*- coding: utf-8 -*-
"""Reusable permission checks for world/character ownership."""

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.world import WorldBook


def check_world_permission(
    world: WorldBook,
    user: User,
    action: str = "操作",
) -> None:
    """Raise 403 if user has no permission to modify the world."""
    if user.is_admin:
        return
    if world.is_preset:
        raise HTTPException(status_code=403, detail=f"预设世界书仅管理员可{action}")
    if world.created_by != user.id:
        raise HTTPException(status_code=403, detail=f"无权{action}此世界书")
