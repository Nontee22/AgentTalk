from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.characters import router as characters_router
from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.worlds import router as worlds_router
from app.core.config import PROJECT_ROOT
from app.core.database import engine, redis_client

UPLOAD_DIR = PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


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

app.mount("/api/static", StaticFiles(directory=str(UPLOAD_DIR)), name="static")

app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(worlds_router, prefix="/api")
app.include_router(characters_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
