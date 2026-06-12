import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RegisterRequest


async def register(db: AsyncSession, data: RegisterRequest) -> User:
    existing = await db.execute(
        select(User).where(
            or_(User.username == data.username, User.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        conflict = await db.execute(
            select(User).where(User.username == data.username)
        )
        if conflict.scalar_one_or_none():
            raise ValueError("用户名已存在")
        raise ValueError("邮箱已被注册")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        nickname=data.username,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def login(db: AsyncSession, username: str, password: str) -> User:
    result = await db.execute(
        select(User).where(
            or_(User.username == username, User.email == username)
        )
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise ValueError("用户名或密码错误")
    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)
