# Phase 0: Environment Setup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up the full project skeleton so both frontend and backend can start, databases are reachable, and CORS works end-to-end.

**Architecture:** Monorepo with `backend/` (FastAPI + async SQLAlchemy) and `frontend/` (Vue 3 + Vite + Tailwind). PostgreSQL and Redis run in Docker Compose. The backend serves REST + SSE; the frontend proxies `/api` to the backend via Vite dev server.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, asyncpg, redis-py (async), Vue 3, TypeScript, Vite 5, Tailwind CSS 3, Pinia, Vue Router 4, Axios, Docker Compose

---

## File Structure

### Root

```
.gitignore
.env                         # Shared env vars (Docker Compose + backend)
.env.example                 # Checked-in template
docker-compose.yml           # PostgreSQL 16 + Redis 7
```

### Backend (`backend/`)

```
backend/
├── requirements.txt          # pip dependencies
├── pyproject.toml             # Project metadata + tool config (pytest)
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI entry point, CORS, lifespan
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Pydantic Settings (reads .env)
│   │   └── database.py        # Async engine, session maker, Redis client, Base
│   ├── api/
│   │   ├── __init__.py
│   │   └── health.py          # GET /api/health
│   ├── models/
│   │   └── __init__.py        # Empty (Phase 1)
│   ├── schemas/
│   │   └── __init__.py        # Empty (Phase 1)
│   ├── services/
│   │   └── __init__.py        # Empty (Phase 2)
│   └── prompts/               # Empty dir (Phase 2)
├── alembic.ini
├── alembic/
│   ├── env.py                 # Async migration runner
│   ├── script.py.mako         # Migration template
│   └── versions/              # Empty (Phase 1 creates first migration)
└── tests/
    ├── __init__.py
    ├── conftest.py             # TestClient fixture
    └── test_health.py          # Health endpoint tests
```

### Frontend (`frontend/`)

```
frontend/
├── package.json
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.ts                # App entry point
    ├── App.vue                # Root component
    ├── vite-env.d.ts          # Type declarations
    ├── styles/
    │   └── main.css           # Tailwind directives
    ├── router/
    │   └── index.ts           # Vue Router config
    ├── api/
    │   └── index.ts           # Axios instance
    ├── stores/                # Empty (Phase 1)
    ├── views/
    │   └── HomeView.vue       # Placeholder with health check display
    ├── components/            # Empty (Phase 1)
    ├── composables/           # Empty (Phase 2)
    ├── types/                 # Empty (Phase 1)
    └── assets/                # Empty (Phase 1)
```

---

### Task 1: Project Infrastructure

**Files:**
- Create: `.gitignore`
- Create: `.env`
- Create: `.env.example`
- Create: `docker-compose.yml`

- [ ] **Step 1: Initialize git repository**

Run:
```powershell
git init
```

Expected: `Initialized empty Git repository`

- [ ] **Step 2: Create `.gitignore`**

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.venv/
*.egg
.pytest_cache/

# Node
node_modules/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project
uploads/
*.log
```

- [ ] **Step 3: Create `.env.example` (checked-in template)**

```dotenv
# Database
POSTGRES_USER=roleplay
POSTGRES_PASSWORD=roleplay_dev
POSTGRES_DB=roleplay_chat
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Auth
JWT_SECRET=dev-secret-change-me-in-production
```

- [ ] **Step 4: Create `.env` by copying `.env.example`**

Run:
```powershell
Copy-Item .env.example .env
```

- [ ] **Step 5: Create `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-roleplay}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-roleplay_dev}
      POSTGRES_DB: ${POSTGRES_DB:-roleplay_chat}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-roleplay}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
  redisdata:
```

- [ ] **Step 6: Start Docker containers and verify**

Run:
```powershell
docker compose up -d
```

Wait 10 seconds, then:
```powershell
docker compose ps
```

Expected: Both `postgres` and `redis` services show `healthy` status.

- [ ] **Step 7: Commit**

```powershell
git add .gitignore .env.example docker-compose.yml
git commit -m "chore: add docker-compose, gitignore, and env template"
```

---

### Task 2: Backend Project Structure + Dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/tests/__init__.py`

- [ ] **Step 1: Create backend directory structure**

Run:
```powershell
New-Item -ItemType Directory -Force backend/app/core, backend/app/api, backend/app/models, backend/app/schemas, backend/app/services, backend/app/prompts, backend/alembic/versions, backend/tests
```

- [ ] **Step 2: Create `backend/requirements.txt`**

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy[asyncio]>=2.0.30
asyncpg>=0.30.0
alembic>=1.13.0
pydantic-settings>=2.3.0
python-dotenv>=1.0.0
redis>=5.0.0
python-multipart>=0.0.9
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

- [ ] **Step 3: Create `backend/pyproject.toml`**

```toml
[project]
name = "roleplay-chat-backend"
version = "0.1.0"
description = "角色扮演对话系统后端"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 4: Create empty `__init__.py` files**

Create empty files at:
- `backend/app/__init__.py`
- `backend/app/core/__init__.py`
- `backend/app/api/__init__.py`
- `backend/app/models/__init__.py`
- `backend/app/schemas/__init__.py`
- `backend/app/services/__init__.py`
- `backend/tests/__init__.py`

- [ ] **Step 5: Create virtual environment and install dependencies**

Run:
```powershell
cd backend; python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 6: Commit**

```powershell
git add backend/requirements.txt backend/pyproject.toml backend/app/ backend/tests/__init__.py
git commit -m "chore: scaffold backend project with dependencies"
```

---

### Task 3: Backend Core Config

**Files:**
- Create: `backend/app/core/config.py`

- [ ] **Step 1: Create `backend/app/core/config.py`**

```python
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    postgres_user: str = "roleplay"
    postgres_password: str = "roleplay_dev"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "roleplay_chat"

    redis_host: str = "localhost"
    redis_port: int = 6379

    jwt_secret: str = "dev-secret-change-me-in-production"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"


settings = Settings()
```

- [ ] **Step 2: Verify config loads**

Run:
```powershell
cd backend; .venv\Scripts\python.exe -c "from app.core.config import settings; print(settings.database_url)"
```

Expected: `postgresql+asyncpg://roleplay:roleplay_dev@localhost:5432/roleplay_chat`

- [ ] **Step 3: Commit**

```powershell
git add backend/app/core/config.py
git commit -m "feat: add pydantic settings config module"
```

---

### Task 4: Database Module

**Files:**
- Create: `backend/app/core/database.py`

- [ ] **Step 1: Create `backend/app/core/database.py`**

```python
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
```

- [ ] **Step 2: Verify module imports**

Run:
```powershell
cd backend; .venv\Scripts\python.exe -c "from app.core.database import engine, Base, redis_client; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```powershell
git add backend/app/core/database.py
git commit -m "feat: add async SQLAlchemy engine and Redis client"
```

---

### Task 5: Alembic Migration Setup

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`

- [ ] **Step 1: Create `backend/alembic.ini`**

```ini
[alembic]
script_location = alembic
# URL is set programmatically in env.py
sqlalchemy.url =

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Create `backend/alembic/env.py`**

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings
from app.core.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Create `backend/alembic/script.py.mako`**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 4: Verify Alembic can read config**

Run (from `backend/` with venv active and Docker containers up):
```powershell
cd backend; .venv\Scripts\Activate.ps1; alembic current
```

Expected: No errors. Output like `(head)` or empty (no migrations yet).

- [ ] **Step 5: Commit**

```powershell
git add backend/alembic.ini backend/alembic/
git commit -m "feat: configure alembic for async migrations"
```

---

### Task 6: FastAPI Application + Health Endpoint + Tests

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/app/api/health.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: Write the test file `backend/tests/conftest.py`**

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
```

- [ ] **Step 2: Write the test file `backend/tests/test_health.py`**

```python
def test_health_endpoint_responds(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_response_has_required_fields(client):
    response = client.get("/api/health")
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data


def test_health_status_is_valid_value(client):
    response = client.get("/api/health")
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
```

- [ ] **Step 3: Create `backend/app/api/health.py`**

```python
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
```

- [ ] **Step 4: Create `backend/app/main.py`**

```python
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
```

- [ ] **Step 5: Run tests**

Run (from `backend/` with venv active):
```powershell
cd backend; .venv\Scripts\Activate.ps1; python -m pytest tests/ -v
```

Expected: All 3 tests pass. The health endpoint gracefully handles missing DB/Redis — `status` will be `"degraded"` if Docker isn't running, but the endpoint still returns 200.

Note: if tests fail due to `redis_client.aclose()` not existing, use `redis_client.close()` instead (depends on redis-py version).

- [ ] **Step 6: Start the backend server manually and verify**

Run (with Docker containers up):
```powershell
cd backend; .venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000
```

In another terminal:
```powershell
Invoke-RestMethod http://localhost:8000/api/health | ConvertTo-Json
```

Expected:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

Also verify the auto-generated docs at `http://localhost:8000/docs`.

- [ ] **Step 7: Commit**

```powershell
git add backend/app/main.py backend/app/api/health.py backend/tests/
git commit -m "feat: add FastAPI app with /health endpoint and tests"
```

---

### Task 7: Frontend Scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/styles/main.css`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/api/index.ts`
- Create: `frontend/src/views/HomeView.vue`

- [ ] **Step 1: Create frontend directories**

Run:
```powershell
New-Item -ItemType Directory -Force frontend/src/styles, frontend/src/router, frontend/src/api, frontend/src/views, frontend/src/components, frontend/src/composables, frontend/src/stores, frontend/src/types, frontend/src/assets
```

- [ ] **Step 2: Create `frontend/package.json`**

```json
{
  "name": "roleplay-chat-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.7.0",
    "lucide-vue-next": "^0.400.0",
    "pinia": "^2.2.0",
    "vue": "^3.5.0",
    "vue-router": "^4.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.1.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "~5.6.0",
    "vite": "^5.4.0",
    "vue-tsc": "^2.1.0"
  }
}
```

- [ ] **Step 3: Create `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>角色世界 — 角色扮演对话系统</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 4: Create `frontend/vite.config.ts`**

```typescript
import { resolve } from 'path'

import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 5: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 6: Create `frontend/tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 7: Create `frontend/tailwind.config.js`**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: {
          deep: '#0a0a0f',
          base: '#0f0f14',
          surface: '#16161d',
          hover: '#1e1e28',
        },
        text: {
          primary: '#e8e6e3',
          secondary: '#8b8994',
          muted: '#4a4853',
        },
        accent: {
          DEFAULT: '#c9a855',
          hover: '#dbb960',
          dim: '#2a2418',
        },
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', 'serif'],
        sans: ['"Noto Sans SC"', 'sans-serif'],
      },
      borderRadius: {
        card: '12px',
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 8: Create `frontend/postcss.config.js`**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 9: Create `frontend/src/vite-env.d.ts`**

```typescript
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}
```

- [ ] **Step 10: Create `frontend/src/styles/main.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 11: Create `frontend/src/main.ts`**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import './styles/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

- [ ] **Step 12: Create `frontend/src/App.vue`**

```vue
<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <RouterView />
</template>
```

- [ ] **Step 13: Create `frontend/src/router/index.ts`**

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/worlds',
    },
    {
      path: '/worlds',
      name: 'worlds',
      component: () => import('@/views/HomeView.vue'),
    },
  ],
})

export default router
```

- [ ] **Step 14: Create `frontend/src/api/index.ts`**

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export default api
```

- [ ] **Step 15: Create `frontend/src/views/HomeView.vue`**

```vue
<script setup lang="ts">
import { onMounted, ref } from 'vue'

import api from '@/api'

const healthStatus = ref('checking...')
const dbStatus = ref('')
const redisStatus = ref('')

onMounted(async () => {
  try {
    const response = await api.get('/health')
    healthStatus.value = response.data.status
    dbStatus.value = response.data.database
    redisStatus.value = response.data.redis
  } catch {
    healthStatus.value = 'unreachable'
  }
})
</script>

<template>
  <div class="min-h-screen bg-bg-base flex items-center justify-center">
    <div class="text-center">
      <h1 class="text-4xl font-serif text-accent mb-2">
        &#10022; 角色世界
      </h1>
      <p class="text-text-secondary mb-8">角色扮演对话系统</p>
      <div class="bg-bg-surface rounded-card p-6 border border-white/[0.08] inline-block text-left">
        <h2 class="text-text-primary text-sm font-semibold mb-3">系统状态</h2>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between gap-8">
            <span class="text-text-secondary">API</span>
            <span :class="healthStatus === 'healthy' ? 'text-green-400' : 'text-red-400'">
              {{ healthStatus }}
            </span>
          </div>
          <div class="flex justify-between gap-8">
            <span class="text-text-secondary">Database</span>
            <span :class="dbStatus === 'connected' ? 'text-green-400' : 'text-red-400'">
              {{ dbStatus || '—' }}
            </span>
          </div>
          <div class="flex justify-between gap-8">
            <span class="text-text-secondary">Redis</span>
            <span :class="redisStatus === 'connected' ? 'text-green-400' : 'text-red-400'">
              {{ redisStatus || '—' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 16: Install dependencies and verify dev server starts**

Run:
```powershell
cd frontend; npm install
```

Expected: `node_modules/` created, no errors.

Then:
```powershell
cd frontend; npm run dev
```

Expected: Vite dev server starts on `http://localhost:5173/`.

- [ ] **Step 17: Commit**

```powershell
git add frontend/
git commit -m "feat: scaffold Vue 3 frontend with Vite, TypeScript, and Tailwind"
```

---

### Task 8: End-to-End Integration Verification

No new files — this task verifies everything works together.

- [ ] **Step 1: Ensure Docker containers are running**

Run:
```powershell
docker compose up -d
```

Verify:
```powershell
docker compose ps
```

Expected: `postgres` and `redis` both running and healthy.

- [ ] **Step 2: Start the backend**

Run (in a terminal):
```powershell
cd backend; .venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8000
```

Expected: `Uvicorn running on http://127.0.0.1:8000`

Verify health endpoint directly:
```powershell
Invoke-RestMethod http://localhost:8000/api/health
```

Expected: `status=healthy`, `database=connected`, `redis=connected`

- [ ] **Step 3: Start the frontend**

Run (in another terminal):
```powershell
cd frontend; npm run dev
```

Expected: `VITE v5.x.x  ready in XXms` on `http://localhost:5173/`

- [ ] **Step 4: Verify CORS and proxy in browser**

Open `http://localhost:5173/` in a browser. The page should display:
- Title: "✦ 角色世界"
- Subtitle: "角色扮演对话系统"
- System status panel showing:
  - API: healthy (green)
  - Database: connected (green)
  - Redis: connected (green)

Open browser DevTools → Network tab. The `/api/health` request should:
- Go to `localhost:5173/api/health` (proxied by Vite to `localhost:8000`)
- Return `200 OK`
- Have no CORS errors in the console

- [ ] **Step 5: Run backend tests one final time**

Run:
```powershell
cd backend; .venv\Scripts\Activate.ps1; python -m pytest tests/ -v
```

Expected: All 3 tests pass.

- [ ] **Step 6: Final commit**

If any adjustments were needed during verification, commit them:
```powershell
git add -A
git commit -m "chore: complete Phase 0 environment setup and integration verification"
```

---

## Completion Criteria

Phase 0 is complete when:

1. `docker compose up -d` starts PostgreSQL 16 and Redis 7
2. `cd backend && python -m pytest tests/ -v` — all tests pass
3. Backend `uvicorn app.main:app --reload` starts on port 8000
4. `GET /api/health` returns `{"status": "healthy", "database": "connected", "redis": "connected"}`
5. Frontend `npm run dev` starts on port 5173
6. Browser at `http://localhost:5173/` shows the status page with all green indicators
7. No CORS errors in the browser console
