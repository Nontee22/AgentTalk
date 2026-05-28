# Phase 1: 世界书与角色管理 — 设计文档

## 概述

在 Phase 0 环境搭建的基础上，实现世界书(WorldBook)和角色(Character)的完整 CRUD 管理功能，包含后端 API、文件上传、前端浏览/创建/编辑页面。

### 范围

- 世界书和角色的数据模型 + 数据库迁移
- 世界书和角色的 CRUD API
- 图片上传（封面/头像）+ 静态文件服务
- 种子数据（霍格沃茨 + 2-3 个角色）
- 前端 5 个页面：世界书大厅、世界书详情、角色详情抽屉、世界书表单、角色表单
- 前端通用组件：标签徽章、可折叠区域、图片上传、标签输入、空状态

### 不在范围

- 用户认证（Phase 3）— 所有接口无需登录
- 对话功能（Phase 2）— 角色抽屉的"开始对话"按钮显示为 disabled
- 权限控制 — `created_by` 字段留空
- 前端单元测试

---

## 1. 数据模型

### WorldBook 表 (`world_books`)

| 列 | 类型 | 约束 |
|---|---|---|
| id | UUID | PK, default uuid4 |
| name | VARCHAR(100) | NOT NULL |
| description | TEXT | 简要介绍 |
| setting | TEXT | 世界观设定 |
| rules | TEXT | 世界规则 |
| lore | TEXT | 历史与传说 |
| factions | JSONB | 势力/阵营列表，如 `["凤凰社", "食死徒"]` |
| tags | JSONB | 标签数组，如 `["奇幻", "魔法"]` |
| cover_image | VARCHAR(500) | 封面图相对路径，如 `"covers/hogwarts.jpg"` |
| is_preset | BOOLEAN | DEFAULT FALSE，系统预设标记 |
| created_by | UUID | NULLABLE，Phase 1 暂留空 |
| created_at | TIMESTAMP | DEFAULT NOW |
| updated_at | TIMESTAMP | DEFAULT NOW, ON UPDATE |

### Character 表 (`characters`)

| 列 | 类型 | 约束 |
|---|---|---|
| id | UUID | PK, default uuid4 |
| world_id | UUID | FK → world_books.id, ON DELETE CASCADE, NOT NULL |
| name | VARCHAR(100) | NOT NULL |
| avatar | VARCHAR(500) | 头像相对路径 |
| identity | TEXT | 身份描述 |
| personality | TEXT | 性格特征 |
| background | TEXT | 个人经历 |
| relationships | TEXT | 与其他角色的关系 |
| language_style | TEXT | 说话风格 |
| knowledge | TEXT | 角色知识范围 |
| greeting | TEXT | 开场白 |
| tags | JSONB | 标签数组 |
| created_at | TIMESTAMP | DEFAULT NOW |
| updated_at | TIMESTAMP | DEFAULT NOW, ON UPDATE |

### 索引

- `characters.world_id` — 加速按世界书查询角色列表
- `world_books.tags` — GIN 索引，加速标签筛选

---

## 2. 后端 API

### 2.1 世界书 CRUD

**GET /api/worlds** — 列表（分页 + 标签筛选 + 搜索）

Query params:
- `page` (int, default 1)
- `page_size` (int, default 12, max 50)
- `tag` (str, optional) — 按标签筛选
- `search` (str, optional) — 按 name/description 模糊搜索

Response:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "霍格沃茨魔法世界",
      "description": "魔法与现实世界并存...",
      "tags": ["奇幻", "魔法"],
      "cover_image": "covers/hogwarts.jpg",
      "is_preset": true,
      "character_count": 3,
      "created_at": "2026-05-28T..."
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 12
}
```

**GET /api/worlds/{id}** — 详情

Response: WorldBook 全部字段 + `character_count`

**POST /api/worlds** — 创建

Body: `{ name, description?, setting?, rules?, lore?, factions?, tags?, cover_image?, is_preset? }`

Response: 创建后的完整 WorldBook

**PUT /api/worlds/{id}** — 更新

Body: 同创建，所有字段可选（partial update）

**DELETE /api/worlds/{id}** — 删除（级联删除所有角色）

### 2.2 角色 CRUD

**GET /api/worlds/{world_id}/characters** — 某世界书下的角色列表

Response: `[{ id, name, avatar, identity, tags }]`（不返回完整的 personality 等大文本字段）

**GET /api/characters/{id}** — 角色详情（全部字段）

**POST /api/worlds/{world_id}/characters** — 创建角色

Body: `{ name, avatar?, identity?, personality?, background?, relationships?, language_style?, knowledge?, greeting?, tags? }`

**PUT /api/characters/{id}** — 更新角色

**DELETE /api/characters/{id}** — 删除角色

### 2.3 文件上传

**POST /api/upload** — 上传图片

- 接受 multipart/form-data
- 限制文件类型：jpg, jpeg, png, gif, webp
- 限制文件大小：5MB
- 按类别存储到 `uploads/covers/` 或 `uploads/avatars/`
- 文件名: `{uuid}.{ext}` 避免冲突
- Query param: `category=covers|avatars`

Response: `{ "path": "covers/abc123.jpg" }`

**静态文件服务**: FastAPI `StaticFiles` 挂载 `uploads/` 到 `/api/static/`

### 2.4 分层架构

```
api/worlds.py       → 路由 + 参数校验
api/characters.py   → 路由 + 参数校验
api/upload.py       → 文件上传路由
services/world_service.py     → 世界书业务逻辑
services/character_service.py → 角色业务逻辑
models/world.py     → WorldBook ORM
models/character.py → Character ORM
schemas/world.py    → WorldBook Pydantic schemas
schemas/character.py→ Character Pydantic schemas
```

### 2.5 错误处理

- 404: 世界书/角色不存在
- 422: 参数校验失败（Pydantic 自动处理）
- 400: 文件类型不支持 / 文件过大

---

## 3. 前端

### 3.1 页面

| 路由 | 视图 | 说明 |
|---|---|---|
| `/worlds` | WorldListView.vue | 世界书大厅首页 |
| `/worlds/create` | WorldFormView.vue | 创建世界书 |
| `/worlds/:id` | WorldDetailView.vue | 世界书详情 + 角色列表 |
| `/worlds/:id/edit` | WorldFormView.vue | 编辑世界书（复用创建表单） |
| `/worlds/:id/characters/create` | CharacterFormView.vue | 创建角色 |
| `/characters/:id/edit` | CharacterFormView.vue | 编辑角色 |

### 3.2 组件

**layout/**
- `AppHeader.vue` — 顶部导航栏：logo + 站点名 + 搜索框 + 创建按钮

**world/**
- `WorldCard.vue` — 世界书卡片：封面图(3:4) + 标题 + 描述 + 标签 + 角色数。悬停时封面微放大 + 金色边框
- `WorldHero.vue` — 详情页顶部横幅：大图 + 渐变遮罩 + 标题叠加
- `WorldLore.vue` — 世界观可折叠区：setting / rules / lore / factions 分节展示

**character/**
- `CharacterCard.vue` — 角色卡片：头像 + 名字 + 身份 + 开始对话按钮
- `CharacterDrawer.vue` — 右侧 400px 滑出抽屉：角色完整信息 + 半透明遮罩

**common/**
- `TagBadge.vue` — 标签徽章
- `FoldableSection.vue` — 可折叠段落（标题 + 展开/收起）
- `ImageUpload.vue` — 图片上传：拖拽 + 点击 + 预览
- `TagInput.vue` — 标签输入：输入框 + 已添加标签列表 + 删除
- `EmptyState.vue` — 空状态占位：插图 + 文字 + 可选按钮

### 3.3 Pinia Store

`stores/worldStore.ts`:
- `worlds` — 世界书列表
- `currentWorld` — 当前选中的世界书详情
- `loading` — 加载状态
- `fetchWorlds(params)` — 获取世界书列表
- `fetchWorldDetail(id)` — 获取世界书详情
- `createWorld(data)` / `updateWorld(id, data)` / `deleteWorld(id)`

### 3.4 API 层

`api/worlds.ts` — getWorlds, getWorld, createWorld, updateWorld, deleteWorld
`api/characters.ts` — getCharacters, getCharacter, createCharacter, updateCharacter, deleteCharacter
`api/upload.ts` — uploadImage

### 3.5 TypeScript 类型

```typescript
// types/world.ts
interface WorldBook {
  id: string
  name: string
  description: string
  setting: string
  rules: string
  lore: string
  factions: string[]
  tags: string[]
  cover_image: string | null
  is_preset: boolean
  character_count: number
  created_at: string
  updated_at: string
}

interface Character {
  id: string
  world_id: string
  name: string
  avatar: string | null
  identity: string
  personality: string
  background: string
  relationships: string
  language_style: string
  knowledge: string
  greeting: string
  tags: string[]
  created_at: string
  updated_at: string
}

// types/common.ts
interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
```

### 3.6 视觉设计要点

- 暗色主题：`bg-base (#0f0f14)` 底色 + `accent (#c9a855)` 金色点缀
- 卡片：`bg-surface (#16161d)`，圆角 12px，悬停时金色边框 + translate-y -2px
- 字体：标题/角色名用 `font-serif`（思源宋体），正文用 `font-sans`（思源黑体）
- 图标：Lucide Icons

---

## 4. 种子数据

使用 Python 脚本 `backend/scripts/seed.py` 插入:

- 1 个世界书：「霍格沃茨魔法世界」（`is_preset=true`），内容取自 `开发计划.md` 示例
- 3 个角色：赫敏·格兰杰、哈利·波特、邓布利多（各含完整设定）

---

## 5. 测试

后端 pytest 测试:
- 世界书 CRUD 全覆盖（创建、读取列表、读取详情、更新、删除）
- 角色 CRUD 全覆盖
- 分页和标签筛选
- 文件上传（格式校验、大小校验）
- 级联删除（删世界书时角色一并删除）

---

## 6. 实现顺序

采用**后端先行**策略：

1. 后端：数据模型 + 迁移
2. 后端：Pydantic schemas
3. 后端：Services 层
4. 后端：API 路由 + 文件上传
5. 后端：测试
6. 后端：种子数据脚本
7. 前端：TypeScript 类型 + API 层
8. 前端：通用组件（TagBadge, FoldableSection, ImageUpload, TagInput, EmptyState）
9. 前端：AppHeader 布局
10. 前端：WorldListView + WorldCard
11. 前端：WorldDetailView + WorldHero + WorldLore + CharacterCard
12. 前端：CharacterDrawer
13. 前端：WorldFormView（创建+编辑）
14. 前端：CharacterFormView（创建+编辑）
15. 前端：Pinia store + 路由配置
16. 浏览器验证全流程
