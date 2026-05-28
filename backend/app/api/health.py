from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import async_session_maker, redis_client

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    result = {"status": "healthy", "database": "connected", "redis": "connected"}

    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        result["database"] = "disconnected"
        result["status"] = "degraded"

    try:
        await redis_client.ping()
    except Exception:
        result["redis"] = "disconnected"
        result["status"] = "degraded"

    return result
