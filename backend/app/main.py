from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core.database import engine, redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title="角色扮演对话系统",
    description="世界书驱动的角色扮演对话平台",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
