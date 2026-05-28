# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

角色扮演对话系统 — 用户在「世界书」的背景下与其中的角色进行对话式互动。核心关系：**世界书 → 角色 → 对话**，对话必须同时遵守世界观规则和角色个性设定。

## Tech Stack

- **Frontend**: Vue 3 + TypeScript + Tailwind CSS + Vite + Pinia
- **Backend**: Python 3.12 + FastAPI + SQLAlchemy + Alembic
- **Database**: PostgreSQL 16 + PGVector (长期记忆)
- **Cache**: Redis 7
- **LLM**: 国内模型 API (DeepSeek / 通义千问 / ChatGLM)，通过 OpenAI 兼容接口调用

## Architecture

单后端架构：FastAPI 同时处理业务逻辑和 LLM 调用，无微服务拆分。

```
frontend/ (Vue 3)  →  REST + SSE  →  backend/ (FastAPI)  →  LLM API
                                         ↕
                                    PostgreSQL + Redis
```

关键数据流：用户选世界书 → 选角色 → 开始对话 → Prompt Builder 将世界书设定 + 角色设定 + 记忆动态注入 System Prompt → 调用 LLM → SSE 流式返回。

## Key Data Models

- **WorldBook**: 世界观设定(setting)、规则(rules)、传说(lore)、势力(factions)
- **Character**: 隶属于某个 WorldBook，包含 personality、background、relationships、language_style、greeting
- **Conversation**: 绑定 user + character + world
- **Message**: 属于某个 conversation，role 为 user/assistant

## Frontend Design

- PC 端优先 (1280px+)，暗色主题 (`#0f0f14` 底色 + `#c9a855` 金色点缀)
- 对话页三栏布局：左 240px 会话列表 / 中间对话区 / 右 300px 角色信息（可折叠）
- 衬线体(思源宋体)用于标题/角色名，无衬线体(思源黑体)用于正文
- 图标库：Lucide Icons

## Prompt Assembly

每次 LLM 调用按固定结构组装：System Prompt（世界观 + 角色设定 + 行为准则）→ 长期记忆（PGVector 语义检索）→ 短期记忆（最近 N 轮）→ 用户输入。Token 超限时按优先级裁剪短期记忆。

## File Storage

图片（封面/头像）本地存储在 `/uploads/` 下，数据库存相对路径，前端通过 `/api/static/{path}` 访问。

## Permissions

- `is_preset=true` 的世界书/角色：所有用户可查看和对话，仅管理员可编辑删除
- 用户创建的内容：创建者可编辑删除，其他用户可查看和对话
