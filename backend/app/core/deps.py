import uuid

from fastapi import Depends, HTTPException, Header
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User


async def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的认证头")

    token = authorization[7:]
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="无效或过期的 token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="需要 access token")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="无效的 token")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return user
