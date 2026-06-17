# AgentTalk — AI 角色扮演对话平台

> 世界书驱动的 AI 角色扮演对话平台。创建世界观设定、定义角色性格，与 AI 角色展开沉浸式对话。
> 支持流式 SSE 对话、RAG 长期记忆、多 Worker 部署，前后端全栈独立实现。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3.5 + TypeScript 5.6 + Vite 5 + Tailwind CSS 3 + Pinia 2 |
| 后端 | Python 3.12 + FastAPI 0.115 + SQLAlchemy 2.0 (async) + Alembic 1.13 |
| 数据库 | PostgreSQL 16 (pgvector 向量扩展) + Redis 7 |
| LLM | DeepSeek Chat（兼容任何 OpenAI API 协议） |
| 向量嵌入 | sentence-transformers 3.0 (BAAI/bge-small-zh-v1.5, 512 维) |
| 认证 | JWT HS256 (python-jose) + bcrypt 密码哈希 |
| 协议 | SSE (Server-Sent Events) 流式传输 + Redis Pub/Sub 跨进程通信 |

## 技术亮点

1. **基于 RAG 的角色长期记忆系统**
   - LLM 自动提取 fact / relationship / preference / event 四类结构化记忆
   - sentence-transformers 本地生成 512 维 embedding，存入 PostgreSQL pgvector
   - 检索采用多因子加权排序：`60% 语义相似度 + 25% 重要度 + 15% 指数时间衰减`
   - 向量去重采用批内 + 数据库双重 cosine similarity 阈值过滤 (≥0.85)
   - 记忆以独立 prompt block 注入 system prompt，token 预算硬约束

2. **生产级 SSE 流式对话引擎**
   - 后端 AsyncGenerator 逐 chunk yield LLM 响应
   - 前端 fetch + ReadableStream 解析 SSE（支持 Authorization Header）
   - useTypewriter composable：2 字符/30ms 节拍平滑释放 + throttled markdown 渲染 (~12fps)
   - 中途停止生成：AbortController 断开 + Redis Pub/Sub 广播 cancel，跨 Worker 精确中断

3. **Redis 驱动的多 Worker 实时架构**
   - 流取消注册表：Redis TTL 键标记活跃流 + Pub/Sub 广播 cancel 信号
   - 事件总线：Redis Pub/Sub → bridge 协程 → asyncio.Queue → SSE 下发前端
   - 滑动窗口限流：Redis sorted set + pipeline 批量操作
   - 后台任务追踪器：fire-and-forget 强引用 + graceful shutdown (10s 超时)

4. **上下文窗口动态管理**
   - 自研中英混合 Token 估算器（CJK ×1.5 + English ×1.3，无需加载 tokenizer）
   - build_messages 在固定 token 预算内从最新消息向前贪心选取历史
   - LLM 调用隔离：流式对话无限制，后台任务 Semaphore(3) 限流 + 指数退避重试

5. **前端工程化**
   - Pinia 5 store 按职责拆分（auth / conversation / stream / memory / world）
   - streamStore 封装 send / regenerate / editAndResend / retry / stop 五种交互
   - 自定义 SSE 客户端：Bearer Token 认证 + 3s 自动断线重连
   - JWT 双 Token：access 30min + refresh 7天，拦截器自动续期

6. **安全与运维**
   - 登录防爆破：5 次/5 分钟 Redis 滑动窗口限流
   - 资源级权限：会话归属校验 + 世界书所有权 + 管理员预设保护
   - 图片上传：Magic bytes 内容校验 + 5MB 限制 + 扩展名白名单
   - CORS 白名单 + X-Forwarded-For 代理 IP 提取

## 核心功能

### 世界书系统
- 创建世界观：设定 (setting)、规则 (rules)、传说 (lore)、势力 (factions)
- JSONB tags 支持动态标签聚合 + GIN 索引加速筛选
- 预设世界书保护（仅管理员可编辑/删除），普通世界书支持创建者权限控制
- 世界书列表支持分页、标签筛选、关键词搜索

### 角色管理
- 7 个角色维度：身份 (identity)、性格 (personality)、背景 (background)、人际关系 (relationships)、语言风格 (language_style)、知识范围 (knowledge)、开场白 (greeting)
- 角色归属世界书，级联删除
- 角色信息参与 System Prompt 拼接，直接影响 AI 对话表现

### AI 对话
- 基于世界观 + 角色设定的流式 SSE 对话
- 支持消息编辑重发、重新生成、中途停止、错误重试
- 消息列表无限滚动（向上加载历史消息）
- 打字机效果：2 字符/30ms 平滑输出 + throttled markdown 渲染 (~12fps)
- 对话自动标题生成（前 3 条消息后由 LLM 后台生成）

### 长期记忆 (RAG)
- **自动提取**：对话中由 LLM 提取 fact / relationship / preference / event 四类记忆
- **向量存储**：sentence-transformers 本地生成 512 维 embedding → pgvector
- **智能检索**：多因子加权排序 = `0.60 × 语义相似度 + 0.25 × 重要度 + 0.15 × 时间衰减`
- **去重机制**：批内 + 数据库双重 cosine similarity ≥ 0.85 过滤
- **Token 预算**：记忆注入上限 1500 tokens，不超出上下文窗口
- **实时通知**：记忆提取完成后通过 Redis Pub/Sub → SSE 推送前端

### 用户系统
- JWT 双 Token 认证：access_token (30min) + refresh_token (7天)
- 登录防爆破：5 次/5 分钟 Redis 滑动窗口限流
- 资源级权限：会话归属校验、世界书所有权校验、管理员预设保护
- 用户资料查看与编辑（昵称、头像）

## 快速开始

### 1. 环境准备

**前置要求**：Docker、Python 3.12+、Node.js 18+

```bash
# 启动数据库（PostgreSQL 16 + Redis 7）
docker compose up -d

# 后端
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填写必要配置：

```ini
# 必填：LLM API 密钥
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

# 生产环境务必修改
JWT_SECRET=your-random-secret-here

# 可选：本地嵌入模型路径（中国网络建议下载到本地）
MEMORY_EMBEDDING_MODEL=./models/bge-small-zh-v1.5
```

### 3. 下载嵌入模型（可选，中国网络推荐）

```bash
cd models
python download_model.py      # 使用 hf-mirror.com 镜像下载 ~100MB
```

### 4. 初始化数据库

```bash
cd backend
python scripts/init_db.py             # 完整初始化：建表 + 种子数据 + 索引
python scripts/init_db.py seed        # 仅插入种子数据
python scripts/init_db.py indexes     # 仅创建性能索引
```

预设种子数据：霍格沃茨魔法世界 + 3 个角色（赫敏、哈利、邓布利多）
默认管理员账号：`admin` / `admin123`

### 5. 启动开发服务器

```bash
# 终端 1：后端
cd backend
uvicorn app.main:app --reload --port 8000

# 终端 2：前端
cd frontend
npm run dev
```

访问 http://localhost:5173

## 架构设计

### 整体请求流程

```
浏览器 → Vite 代理 (/api) → FastAPI → Service 层 → SQLAlchemy → PostgreSQL
                                │
                                ├─→ LLM (DeepSeek) ── SSE 流式 ──→ 前端 (fetch + ReadableStream)
                                │
                                └─→ Redis ── Pub/Sub ──→ SSE 事件流 ──→ 前端 (useEventStream)
```

### 对话消息完整处理链

```
用户发送消息 → chat.py send_message()
  │
  ▼
stream_service.send_message_stream()
  │
  ├── 1. 保存用户消息到 DB
  │
  ├── 2. 加载最近 20 条历史消息
  │
  ├── 3. build_system_prompt(world, character)
  │       └── 分块拼接：世界观 → 规则 → 势力 → 传说 → 角色身份 → 性格 → 经历 → 关系 → 语言风格 → 知识 → 行为准则
  │
  ├── 4. retrieve_relevant_memories(user_content)       [memory_enabled=true]
  │       ├── pgvector cosine similarity 检索 top-K 候选
  │       ├── 多因子加权重排 (语义60% + 重要度25% + 时间衰减15%)
  │       └── token_budget 内截取最终记忆列表
  │
  ├── 5. format_memories_block(memories)
  │       └── 格式化为 "【长期记忆】" 文本块，追加到 system prompt
  │
  ├── 6. build_messages(system_prompt, history, user_input)
  │       ├── system + memory 合并为 system 消息
  │       ├── Token 预算裁剪历史消息（从最新向前贪心选取）
  │       └── 追加当前 user 消息
  │
  ├── 7. chat_stream(messages) → AsyncGenerator 逐 chunk yield
  │       └── stream_registry: 注册流 + 监听 cancel 信号
  │
  └── 8. 后台任务（非阻塞）
          ├── generate_title()           ← 消息数 ≤ 3 时触发
          └── maybe_extract_memories()   ← 消息增量 ≥ 4 时触发
              → LLM 提取 → embedding 向量化 → 去重 → pgvector 存储
              → event_bus: Redis Pub/Sub → SSE 通知前端
```

### System Prompt 拼接结构

```
┌──────────────────────────────────────────────────┐
│ 【世界观】你所处的世界是「{world.name}」...        │
│ 【世界规则】{world.rules}                         │
│ 【势力与阵营】- {faction_1}  - {faction_2} ...    │
│ 【历史与传说】{world.lore}                        │
├──────────────────────────────────────────────────┤
│ 【你的身份】你是{character.name}，{identity}。     │
│ 【你的性格】{personality}                         │
│ 【你的经历】{background}                          │
│ 【你的人际关系】{relationships}                   │
│ 【说话风格】{language_style}                      │
│ 【你知道的事情】{knowledge}                       │
│ 【行为准则】始终以角色身份回应...（固定）           │
├──────────────────────────────────────────────────┤
│ 【长期记忆】(memory_block, 可选)                  │
│ - [事实] ...  - [关系] ...  - [偏好] ...          │
└──────────────────────────────────────────────────┘
```

### 多 Worker 架构

```
Worker 1 ─┐                    ┌─ Redis Pub/Sub（事件总线、流取消信号）
Worker 2 ─┼── Redis ───────────┤
Worker N ─┘                    ├─ Redis Sorted Set（分布式滑动窗口限流）
                               └─ Redis Key-Value（流活跃状态标记，TTL 5min）
```

### 数据模型关系

```
User (1) ──→ (N) Conversation ←── (1) Character ←── (1) WorldBook
 │                    │                                    │
 │               (N) Message                         (N) Character
 │
 └──→ (N) CharacterMemory ←── Character
```

| 模型 | 表名 | 关键字段 |
|------|------|---------|
| User | `users` | UUID PK, username, email, hashed_password, is_admin |
| WorldBook | `world_books` | UUID PK, name, setting, rules, lore, factions (JSONB), tags (JSONB + GIN) |
| Character | `characters` | UUID PK, world_id FK, identity, personality, language_style, knowledge, greeting |
| Conversation | `conversations` | UUID PK, user_id FK, character_id FK, world_id FK, message_count, last_memory_extraction_at_count |
| Message | `messages` | UUID PK, conversation_id FK, role, content, token_count |
| CharacterMemory | `character_memories` | UUID PK, user_id FK, character_id FK, content, category, importance, embedding (pgvector 512) |

## API 概览

### 认证

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/auth/register` | 注册（用户名+邮箱+密码） | - |
| POST | `/api/auth/login` | 登录（5次/5分钟限流） | - |
| POST | `/api/auth/refresh` | 刷新 token | - |
| GET | `/api/user/profile` | 获取当前用户信息 | Bearer |
| PUT | `/api/user/profile` | 更新用户资料（昵称、头像） | Bearer |

### 世界书

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/worlds` | 世界书列表（分页、标签筛选、关键词搜索） | Bearer |
| GET | `/api/worlds/tags` | 动态标签聚合（含使用计数） | Bearer |
| POST | `/api/worlds` | 创建世界书（仅管理员） | Bearer |
| GET | `/api/worlds/:id` | 世界书详情 | Bearer |
| PUT | `/api/worlds/:id` | 编辑世界书（权限校验） | Bearer |
| DELETE | `/api/worlds/:id` | 删除世界书（权限校验） | Bearer |

### 角色

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/worlds/:id/characters` | 世界书下的角色列表 | Bearer |
| POST | `/api/worlds/:id/characters` | 创建角色（权限校验） | Bearer |
| GET | `/api/characters/:id` | 角色详情 | Bearer |
| PUT | `/api/characters/:id` | 编辑角色（权限校验） | Bearer |
| DELETE | `/api/characters/:id` | 删除角色（权限校验） | Bearer |

### 对话

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/chat/start` | 创建对话（含角色开场白） | Bearer |
| POST | `/api/chat/:id/send` | 发送消息（SSE 流式响应） | Bearer |
| POST | `/api/chat/:id/stop` | 中断生成（Redis Pub/Sub 跨 Worker） | Bearer |
| GET | `/api/chat/conversations` | 对话列表（分页） | Bearer |
| GET | `/api/chat/:id` | 消息历史（分页，降序） | Bearer |
| DELETE | `/api/chat/:id` | 删除对话（归属校验） | Bearer |

### 记忆

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/memories/character/:id` | 查询角色记忆列表 | Bearer |
| DELETE | `/api/memories/:id` | 删除指定记忆 | Bearer |

### 其他

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/events/stream` | SSE 事件流（记忆就绪通知，30s 心跳） | Bearer |
| POST | `/api/upload` | 图片上传（5MB 限制、Magic bytes 校验） | Bearer |
| GET | `/api/health` | 健康检查（DB + Redis 状态） | - |

### 统一响应格式

分页接口统一返回：

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

SSE 流式响应格式：

```
data: {"token": "你"}
data: {"token": "好"}
data: {"token": "，冒险者"}
data: [DONE]
```

错误响应：

```
data: {"error": "模型调用频率超限，请稍后重试"}
```

## 环境变量

### 数据库

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POSTGRES_USER` | `roleplay` | 数据库用户 |
| `POSTGRES_PASSWORD` | `roleplay_dev` | 数据库密码 |
| `POSTGRES_HOST` | `localhost` | 数据库地址 |
| `POSTGRES_PORT` | `5432` | 数据库端口 |
| `POSTGRES_DB` | `roleplay_chat` | 数据库名 |
| `REDIS_HOST` | `localhost` | Redis 地址 |
| `REDIS_PORT` | `6379` | Redis 端口 |

### 认证与安全

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `JWT_SECRET` | `dev-secret-...` | JWT 签名密钥（生产环境务必修改） |
| `JWT_ALGORITHM` | `HS256` | JWT 签名算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token 有效期（分钟） |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token 有效期（天） |
| `CORS_ORIGINS` | `http://localhost:5173` | 允许的前端域名（逗号分隔） |

### LLM 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_KEY` | — | LLM API 密钥（必填） |
| `LLM_BASE_URL` | `https://api.deepseek.com` | LLM API 地址（兼容 OpenAI 协议） |
| `LLM_MODEL` | `deepseek-chat` | 模型名称 |
| `LLM_MAX_TOKENS` | `2048` | 单次回复最大 token 数 |
| `LLM_TEMPERATURE` | `0.85` | 生成温度（0.0~2.0） |
| `LLM_MAX_CONTEXT_TOKENS` | `6000` | 上下文窗口总 token 预算 |

### 记忆系统

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MEMORY_ENABLED` | `true` | 是否启用长期记忆 |
| `MEMORY_EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | 嵌入模型名称或本地路径 |
| `MEMORY_EMBEDDING_DIMENSION` | `512` | 向量维度 |
| `MEMORY_MAX_PER_QUERY` | `5` | 每次对话检索的最大记忆条数 |
| `MEMORY_TOKEN_BUDGET` | `1500` | 记忆注入的 token 上限 |
| `MEMORY_DECAY_HALFLIFE_DAYS` | `30.0` | 记忆时间衰减半衰期（天） |
| `MEMORY_EXTRACTION_MIN_MESSAGES` | `4` | 触发记忆提取的最少新消息增量 |
| `MEMORY_EXTRACTION_CONTEXT_MESSAGES` | `10` | 记忆提取时使用的上下文消息数 |

