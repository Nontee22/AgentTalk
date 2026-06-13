# XM — 角色扮演对话系统

世界书驱动的 AI 角色扮演对话平台。创建世界观设定、定义角色性格，与 AI 角色展开沉浸式对话。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3.5 + TypeScript + Vite + Tailwind CSS + Pinia |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy (async) + Alembic |
| 数据库 | PostgreSQL 16 (pgvector) + Redis 7 |
| LLM | DeepSeek Chat（可替换任何 OpenAI 兼容 API） |
| 向量嵌入 | sentence-transformers (BAAI/bge-small-zh-v1.5, 512 维) |

## 项目结构

```
├── frontend/                  # Vue 3 SPA
│   └── src/
│       ├── api/               # API 请求封装（Axios + SSE fetch）
│       ├── components/        # 通用 & 业务组件
│       ├── composables/       # 组合式函数
│       │   ├── useToast.ts          # 消息通知
│       │   ├── useEventStream.ts    # SSE 事件流（自动重连）
│       │   ├── useTypewriter.ts     # 打字机效果（流式显示）
│       │   └── useUnsavedChanges.ts # 表单离开警告
│       ├── stores/            # Pinia 状态管理
│       │   ├── conversationStore.ts # 对话 & 消息（含分页）
│       │   ├── streamStore.ts       # 流式输出状态
│       │   ├── memoryStore.ts       # 角色记忆
│       │   ├── worldStore.ts        # 世界书
│       │   └── authStore.ts         # 认证
│       ├── views/             # 页面视图
│       ├── types/             # TypeScript 类型定义
│       └── utils/             # 工具函数（markdown、auth）
├── backend/
│   ├── app/
│   │   ├── api/               # FastAPI 路由
│   │   ├── core/              # 配置、数据库、安全、权限、限流
│   │   ├── models/            # SQLAlchemy ORM 模型
│   │   ├── schemas/           # Pydantic 请求/响应模型
│   │   └── services/          # 业务逻辑
│   │       ├── message_service.py   # 对话 & 消息 CRUD
│   │       ├── stream_service.py    # SSE 流式输出编排
│   │       ├── memory_trigger.py    # 后台记忆提取触发
│   │       ├── memory_service.py    # 记忆提取 & 检索
│   │       ├── embedding_service.py # 向量嵌入（本地模型）
│   │       ├── llm_service.py       # LLM 调用（重试 + 并发控制）
│   │       ├── task_tracker.py      # 后台任务追踪 & 优雅关闭
│   │       ├── stream_registry.py   # 流取消（Redis pub/sub）
│   │       ├── event_bus.py         # 事件总线（Redis pub/sub）
│   │       └── prompt_builder.py    # 系统提示词构建
│   ├── alembic/               # 数据库迁移
│   ├── scripts/               # 初始化脚本
│   └── requirements.txt
├── models/                    # 本地嵌入模型存储
├── docker-compose.yml         # PostgreSQL + Redis
└── .env                       # 环境变量配置
```

## 核心功能

- **世界书系统**：创建世界观（设定、规则、传说、势力），角色在世界观约束下对话
- **角色管理**：定义角色身份、性格、背景、说话风格、知识范围
- **AI 对话**：基于世界观+角色设定的流式 SSE 对话，支持消息编辑、重新生成、无限滚动
- **长期记忆**：自动提取对话中的事实/关系/偏好，向量检索后注入上下文
- **打字机效果**：流式响应逐字符平滑显示，throttle markdown 渲染
- **表单保护**：世界书/角色编辑页面离开时警告未保存更改
- **用户系统**：JWT 认证、角色权限（管理员/普通用户）
- **多 Worker 支持**：限流、流取消、事件总线均基于 Redis，支持多进程部署

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

## 架构设计

### 请求流程

```
浏览器 → Vite 代理 (/api) → FastAPI → Service 层 → SQLAlchemy → PostgreSQL
                                ↓
                          LLM (DeepSeek) ← SSE 流式 → 前端 (fetch + ReadableStream)
```

### 后台任务流

```
用户发送消息
  → stream_service: SSE 流式输出（阻塞）
  → task_tracker: 后台创建 title 生成任务（非阻塞）
  → task_tracker: 后台创建记忆提取任务（非阻塞）
       → memory_service: LLM 提取 → embedding → pgvector 存储
       → event_bus: Redis pub/sub 通知前端
```

### 多 Worker 架构

```
Worker 1 ─┐                    ┌─ Redis pub/sub（事件总线、流取消）
Worker 2 ─┼── Redis ───────────┤
Worker N ─┘                    └─ Redis sorted set（分布式限流）
```

## API 概览

| 模块 | 端点 | 说明 |
|------|------|------|
| 认证 | `POST /api/auth/register` | 注册 |
| | `POST /api/auth/login` | 登录（5次/5分钟限流） |
| | `POST /api/auth/refresh` | 刷新 token |
| 世界书 | `GET /api/worlds` | 列表（分页、标签筛选、搜索） |
| | `GET /api/worlds/tags` | 动态标签聚合（含计数） |
| | `POST /api/worlds` | 创建（管理员） |
| | `GET/PUT/DELETE /api/worlds/:id` | 详情/编辑/删除 |
| 角色 | `GET /api/worlds/:id/characters` | 列表 |
| | `POST /api/worlds/:id/characters` | 创建 |
| | `GET/PUT/DELETE /api/characters/:id` | 详情/编辑/删除 |
| 对话 | `POST /api/chat/start` | 创建对话 |
| | `POST /api/chat/:id/send` | 发送消息（SSE 流式） |
| | `POST /api/chat/:id/stop` | 中断生成 |
| | `GET /api/chat/conversations` | 对话列表（分页） |
| | `GET /api/chat/:id` | 消息历史（分页，降序） |
| 记忆 | `GET /api/memory/:characterId` | 查询角色记忆 |
| 事件 | `GET /api/events/stream` | SSE 事件流（记忆就绪通知） |
| 上传 | `POST /api/upload` | 图片上传（5MB、MIME 校验） |
| 健康 | `GET /api/health` | 健康检查 |

## 环境变量

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
| `LLM_API_KEY` | — | LLM API 密钥（必填） |
| `LLM_BASE_URL` | `https://api.deepseek.com` | LLM API 地址 |
| `LLM_MODEL` | `deepseek-chat` | 模型名称 |
| `LLM_MAX_TOKENS` | `2048` | 单次回复最大 token |
| `LLM_TEMPERATURE` | `0.85` | 生成温度 |
| `LLM_MAX_CONTEXT_TOKENS` | `6000` | 上下文窗口大小 |
| `CORS_ORIGINS` | `http://localhost:5173` | 允许的前端域名 |
| `MEMORY_ENABLED` | `true` | 是否启用长期记忆 |
| `MEMORY_EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | 嵌入模型名称或路径 |
| `MEMORY_EMBEDDING_DIMENSION` | `512` | 向量维度 |
| `MEMORY_MAX_PER_QUERY` | `5` | 每次对话检索的最大记忆数 |
| `MEMORY_TOKEN_BUDGET` | `1500` | 记忆注入的 token 上限 |
| `MEMORY_EXTRACTION_MIN_MESSAGES` | `4` | 触发记忆提取的最少新消息数 |
