# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

角色扮演对话系统 (AI Roleplay Chat) — a world-book-driven platform where users create world settings, define character personalities, and have immersive conversations with AI characters. Chinese-first UI.

## Tech Stack

- **Frontend**: Vue 3.5 + TypeScript + Vite + Tailwind CSS + Pinia (Composition API, `<script setup>`)
- **Backend**: Python 3.12 + FastAPI + SQLAlchemy (async) + Alembic
- **Database**: PostgreSQL 16 with pgvector extension (via `docker-compose.yml`)
- **Cache**: Redis 7 (docker-compose, currently minimal usage)
- **LLM**: DeepSeek Chat via OpenAI-compatible SDK
- **Embeddings**: BAAI/bge-small-zh-v1.5 (512-dim, local sentence-transformers model)

## Commands

```bash
# Infrastructure
docker compose up -d                          # Start PostgreSQL + Redis

# Backend (from backend/)
pip install -r requirements.txt
python scripts/init_db.py                     # Create tables + seed data + indexes (admin/admin123)
python scripts/init_db.py seed                # Seed data only
python scripts/init_db.py indexes             # Performance indexes only
uvicorn app.main:app --reload --port 8000     # Start dev server

# Frontend (from frontend/)
npm install
npm run dev                                   # Vite dev server on :5173 (proxies /api → :8000)
npm run build                                 # vue-tsc && vite build

# Tests (from backend/)
pytest                                        # All tests (asyncio_mode = auto)
pytest tests/test_health.py                   # Single test file
pytest tests/test_health.py -k test_name      # Single test
```

## Architecture

### Request Flow

```
Browser → Vite proxy (/api) → FastAPI → Service layer → SQLAlchemy (async) → PostgreSQL
                                  ↓
                            LLM (DeepSeek) ← SSE streaming → Frontend (fetch + ReadableStream)
```

### Backend Layers

- **`app/api/`** — FastAPI routers. Thin handlers that validate input and delegate to services.
- **`app/services/`** — Business logic. All DB queries and LLM calls happen here, not in routers.
- **`app/models/`** — SQLAlchemy ORM models (async, UUID primary keys).
- **`app/schemas/`** — Pydantic v2 request/response models with field validation.
- **`app/core/`** — Infrastructure: config (pydantic-settings), database engine, JWT/bcrypt security, FastAPI deps, rate limiting.

### Key Cross-Cutting Patterns

**SSE Streaming**: Chat responses stream via `StreamingResponse`. Frontend uses raw `fetch` + `ReadableStream` (not `EventSource`) to support `Authorization` headers. Both chat streaming (`app/api/chat.py`) and the event side-channel (`app/api/events.py`) use this pattern.

**Memory Pipeline**: `chat_service._maybe_extract_memories` → fires as `asyncio.create_task` after each assistant response → LLM extracts structured memories → embeds with sentence-transformers → dedup via pgvector cosine similarity → stores in `character_memories` table → publishes `memory_ready` SSE event via `event_bus.publish()`. On next user message, `retrieve_relevant_memories` fetches top-K by time-decayed semantic similarity and injects into system prompt.

**Event Bus** (`app/services/event_bus.py`): In-process asyncio.Queue-based pub/sub keyed by user_id. Powers the SSE side-channel at `GET /api/events/stream`. Process-local only — not multi-worker safe.

**Permission Checks**: `app/core/permissions.py` provides `check_world_permission(world, user, action)` used by worlds and characters routers.

### Frontend Patterns

- **API layer** (`src/api/`): Axios instance with JWT interceptor (auto-refresh on 401). SSE endpoints use raw fetch instead.
- **Stores** (`src/stores/`): Pinia composition stores. `chatStore` manages conversations, messages, and streaming state. `memoryStore` tracks character memories.
- **Composables**: `useToast` for notifications, `useEventStream` for SSE side-channel (auto-reconnect, JWT pre-check).
- **Styling**: Dark theme with gold accent (#c9a855). Noto Serif SC for character names, Noto Sans SC for body. All custom colors defined in `tailwind.config.js`.

### Token Auth

JWT access (30min) + refresh (7d) tokens stored in `localStorage`. Frontend axios interceptor handles 401 → refresh flow. For SSE connections (which can't use axios), `useEventStream.ts` and `chat.ts` manually check token expiry and refresh before connecting.

## Important Conventions

- All backend async — use `async def` for route handlers and service functions, `AsyncSession` for DB
- UUID primary keys on all models
- Chinese UI text throughout (error messages, labels, prompts)
- Backend schemas enforce `max_length` on all text fields
- LLM prompts are in Chinese (system prompts, memory extraction prompts)
- Vite `@` alias maps to `frontend/src/`
