# XM — 角色扮演对话系统

世界书驱动的 AI 角色扮演对话平台。创建世界观设定、定义角色性格，与 AI 角色展开沉浸式对话。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + TypeScript + Tailwind CSS + Pinia |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy (async) |
| 数据库 | PostgreSQL 16 (pgvector) + Redis 7 |
| LLM | DeepSeek Chat（可替换任何 OpenAI 兼容 API） |
| 向量嵌入 | sentence-transformers (BAAI/bge-small-zh-v1.5) |

## 项目结构

```
XM/
├── frontend/                # Vue 3 SPA
│   ├── src/
│   │   ├── api/             # API 请求封装
│   │   ├── components/      # 通用 & 业务组件
│   │   ├── composables/     # 组合式函数 (useToast 等)
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── views/           # 页面视图
│   │   ├── types/           # TypeScript 类型定义
│   │   └── utils/           # 工具函数 (markdown 等)
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI 路由 (auth, worlds, characters, chat, memory, upload)
│   │   ├── core/            # 配置、数据库、安全、权限、限流
│   │   ├── models/          # SQLAlchemy ORM 模型
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   └── services/        # 业务逻辑 (chat, llm, memory, embedding, prompt)
│   ├── alembic/             # 数据库迁移
│   ├── scripts/             # 数据库管理脚本
│   └── requirements.txt
├── models/                  # 本地嵌入模型存储
├── docker-compose.yml       # PostgreSQL + Redis
├── .env                     # 环境变量配置
└── .env.example             # 配置模板
```

## 核心功能

- **世界书系统**：创建世界观（设定、规则、传说、势力），角色在世界观约束下对话
- **角色管理**：定义角色身份、性格、背景、说话风格、知识范围
- **AI 对话**：基于世界观+角色设定的流式 SSE 对话，支持消息编辑、重新生成
- **长期记忆**：自动提取对话中的事实/关系/偏好，向量检索后注入上下文
- **用户系统**：JWT 认证、角色权限（管理员/普通用户）

## 快速开始

### 1. 环境准备

```bash
# 启动数据库
docker compose up -d

# 后端
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 配置

复制 `.env.example` 为 `.env`，填写必要配置：

```ini
# 必填：LLM API 密钥
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 生产环境务必修改
JWT_SECRET=your-random-secret-here

# 可选：调整 LLM 上下文窗口（默认 6000 tokens）
# LLM_MAX_CONTEXT_TOKENS=16000

# 可选：CORS（多个用逗号分隔）
# CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# 可选：本地嵌入模型路径（中国网络建议下载到本地）
# MEMORY_EMBEDDING_MODEL=./models/bge-small-zh-v1.5
```

### 3. 下载嵌入模型（中国网络）

```bash
cd models
python download_model.py      # 使用 hf-mirror.com 镜像下载 ~100MB
```

### 4. 初始化数据库

```bash
cd backend
python scripts/init_db.py             # 完整初始化：建表 + 种子数据 + 索引
python scripts/init_db.py seed        # 仅种子数据
python scripts/init_db.py indexes     # 仅性能索引
```

默认管理员账号：`admin` / `admin123`

### 5. 启动开发服务器

```bash
# 后端（终端 1）
cd backend
uvicorn app.main:app --reload --port 8000

# 前端（终端 2）
cd frontend
npm run dev
```

访问 http://localhost:5173

## API 概览

| 模块 | 端点 | 说明 |
|------|------|------|
| 认证 | `POST /api/auth/register` | 注册 |
| | `POST /api/auth/login` | 登录（5次/5分钟限流） |
| | `POST /api/auth/refresh` | 刷新 token |
| 世界书 | `GET /api/worlds` | 列表（分页、标签筛选、搜索） |
| | `POST /api/worlds` | 创建（管理员） |
| | `GET/PUT/DELETE /api/worlds/:id` | 详情/编辑/删除 |
| 角色 | `GET /api/worlds/:id/characters` | 列表 |
| | `POST /api/worlds/:id/characters` | 创建 |
| | `GET/PUT/DELETE /api/characters/:id` | 详情/编辑/删除 |
| 对话 | `POST /api/chat/start` | 创建对话 |
| | `POST /api/chat/:id/send` | 发送消息（SSE 流式） |
| | `POST /api/chat/:id/stop` | 中断生成 |
| | `GET /api/chat/conversations` | 对话列表（分页） |
| | `GET /api/chat/:id` | 消息历史（分页） |
| 记忆 | `GET /api/memory/:characterId` | 查询角色记忆 |
| 上传 | `POST /api/upload` | 图片上传（5MB、MIME 校验） |
| 健康 | `GET /api/health` | 健康检查（降级返回 503） |

## 环境变量一览

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POSTGRES_USER` | `roleplay` | 数据库用户 |
| `POSTGRES_PASSWORD` | `roleplay_dev` | 数据库密码 |
| `POSTGRES_HOST` | `localhost` | 数据库地址 |
| `POSTGRES_PORT` | `5432` | 数据库端口 |
| `POSTGRES_DB` | `roleplay_chat` | 数据库名 |
| `REDIS_HOST` | `localhost` | Redis 地址 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `JWT_SECRET` | `dev-secret-...` | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token 有效期 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token 有效期 |
| `LLM_API_KEY` | — | LLM API 密钥 |
| `LLM_BASE_URL` | `https://api.deepseek.com` | LLM API 地址 |
| `LLM_MODEL` | `deepseek-chat` | 模型名称 |
| `LLM_MAX_TOKENS` | `2048` | 单次回复最大 token |
| `LLM_TEMPERATURE` | `0.85` | 生成温度 |
| `LLM_MAX_CONTEXT_TOKENS` | `6000` | 上下文窗口大小 |
| `CORS_ORIGINS` | `http://localhost:5173` | 允许的前端域名 |
| `MEMORY_ENABLED` | `true` | 是否启用长期记忆 |
| `MEMORY_EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | 嵌入模型 |
| `MEMORY_EMBEDDING_DIMENSION` | `512` | 向量维度 |
| `MEMORY_EXTRACTION_MIN_MESSAGES` | `6` | 触发记忆提取的最少消息数 |
