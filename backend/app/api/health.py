from fastapi import APIRouter
from fastapi.responses import JSONResponse
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

    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(content=result, status_code=status_code)
