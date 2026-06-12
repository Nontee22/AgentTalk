import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import get_client_ip, login_limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
    UserUpdate,
)
from app.services import auth_service

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await auth_service.register(db, data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = get_client_ip(request)
    login_limiter.check(client_ip)

    try:
        user = await auth_service.login(db, data.username, data.password)
    except ValueError as e:
        login_limiter.record(client_ip)
        raise HTTPException(status_code=401, detail=str(e))

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = decode_token(data.refresh_token)
    except JWTError:
        raise HTTPException(status_code=401, detail="无效或过期的 refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="需要 refresh token")

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="无效的 token")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/user/profile", response_model=UserOut)
async def get_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.put("/user/profile", response_model=UserOut)
async def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user
