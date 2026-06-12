# Phase 5：体验打磨 — 详细实施计划

## 概述

Phase 1-4 完成了核心功能（世界书/角色管理、对话引擎、用户系统、长期记忆）。Phase 5 聚焦于用户体验提升，让系统从"能用"变为"好用"。

---

## 现状评估

| 功能 | 当前状态 | Phase 5 目标 |
|------|----------|-------------|
| 世界书搜索 | 有关键词搜索 + 硬编码标签筛选（4个） | 动态标签 + 多标签组合筛选 + 搜索联动 |
| 角色搜索与推荐 | 无 | 热门角色推荐 + 最近对话角色快捷入口 |
| 对话中情绪变化 | 无 | LLM 输出情绪标签，前端动态展示 |
| 角色切换过渡 | "新对话"按钮跳转到 /worlds | 同世界书内角色选择器 |
| 输入框增强 | 支持 Shift+Enter | 重新生成、消息编辑、textarea 自动增高 |
| 页面过渡动画 | 无 | 路由切换淡入淡出 + 列表进场动画 |

---

## 5.1 世界书搜索增强

### 现状
- `AppHeader.vue` 有全局搜索框，传 `search` query 到 `/worlds`
- `WorldListView.vue` 硬编码 4 个标签：奇幻、科幻、历史、现实
- 后端 `GET /api/worlds` 已支持 `search` 和 `tag` 参数

### 改动

#### 后端
- `GET /api/worlds` 新增返回 `available_tags` 字段 — 从所有世界书的 tags JSONB 列聚合去重
- 支持多标签筛选：`?tags=奇幻,魔法`（逗号分隔，取交集）

**文件**：`backend/app/api/worlds.py`、`backend/app/services/world_service.py`（如果有）

#### 前端
- `WorldListView.vue`：标签栏改为动态加载（从 API 获取），支持多选（高亮 = 已选）
- 搜索框与标签筛选联动：选标签后搜索范围缩窄，搜索时保留已选标签
- 空结果状态：显示"没有找到匹配的世界书"

**文件**：`frontend/src/views/WorldListView.vue`、`frontend/src/stores/worldStore.ts`

---

## 5.2 角色推荐与快捷入口

### 改动

#### 后端
- 新增 `GET /api/characters/recent` — 返回当前用户最近对话过的角色列表（按 conversation.updated_at 降序，去重，limit 6）
- 新增 `GET /api/characters/popular` — 按对话数排序的热门角色（全局统计）

**文件**：`backend/app/api/characters.py`

#### 前端
- `WorldListView.vue` 顶部新增"最近对话"横向滚动条：显示用户最近聊过的角色卡片（头像 + 名字 + 世界名），点击直接开始对话
- 首页新增"热门角色"区域（世界书列表之上）

**文件**：`frontend/src/views/WorldListView.vue`、`frontend/src/api/characters.ts`、`frontend/src/types/world.ts`

---

## 5.3 对话中角色情绪变化

### 设计方案

在 AI 回复时，通过 Prompt 让 LLM 在回复开头输出一个隐藏的情绪标签，前端解析后展示在角色面板。

#### Prompt 注入
在 `build_system_prompt` 的行为准则中追加：
```
- 在每次回复的最开头，用 [emotion:情绪] 标注当前情绪状态，然后换行写正文
- 可用情绪：平静、开心、悲伤、愤怒、惊讶、困惑、紧张、温柔、傲慢、害羞
- 示例：[emotion:开心]\n（正文内容）
```

#### 后端
- `chat_service.py`：流式回复完成后，解析 `[emotion:xxx]` 前缀，提取情绪标签
- SSE 事件中增加一个 `emotion` 事件类型，在流式结束时发送
- 或者：前端自行从回复文本解析并移除前缀

#### 前端
- `ChatMessage.vue`：解析并隐藏 `[emotion:xxx]` 前缀，不展示给用户
- `CharacterPanel.vue`：显示当前情绪状态（带对应表情/颜色指示）
- 情绪指示器：角色头像旁的小标签，如 "😊 开心"，颜色映射：
  - 开心 → 暖金色
  - 悲伤 → 蓝灰
  - 愤怒 → 暗红
  - 平静 → 默认灰

**文件**：
- `backend/app/services/prompt_builder.py`
- `frontend/src/components/chat/ChatMessage.vue`
- `frontend/src/components/layout/CharacterPanel.vue`
- `frontend/src/stores/chatStore.ts`（存储当前情绪）

---

## 5.4 同世界书内角色切换

### 现状
对话页侧边栏的"+ 新对话"按钮直接跳转到 `/worlds`，用户体验割裂。

### 改动

#### 后端
无需改动，已有 `GET /api/worlds/{world_id}/characters` 接口。

#### 前端
- 新建 `CharacterPickerModal.vue`：弹窗组件，展示当前世界书下的所有角色卡片
- `ConversationList.vue`："+ 新对话"按钮点击后弹出 CharacterPickerModal
- 弹窗中选择角色 → 调用 `chatStore.createConversation()` → 进入新对话
- 弹窗底部保留"浏览其他世界"链接，跳转到 `/worlds`

**文件**：
- 新建 `frontend/src/components/chat/CharacterPickerModal.vue`
- `frontend/src/components/layout/ConversationList.vue`
- `frontend/src/views/ChatView.vue`

---

## 5.5 输入框增强

### 5.5a 重新生成上一条回复

- `ChatMessage.vue`：最后一条 assistant 消息（非流式中）底部显示"🔄 重新生成"按钮
- 点击后：删除最后一条 assistant 消息，重新发送上一条 user 消息
- `chatStore.ts` 新增 `regenerateLastMessage()` 方法

**文件**：`frontend/src/components/chat/ChatMessage.vue`、`frontend/src/stores/chatStore.ts`

### 5.5b 消息编辑

- `ChatMessage.vue`：用户消息悬停时显示"✏️ 编辑"按钮
- 点击后消息变为可编辑 textarea，修改后按回车重新发送
- 编辑后的消息之后的所有消息删除，从编辑点重新生成

**文件**：`frontend/src/components/chat/ChatMessage.vue`、`frontend/src/stores/chatStore.ts`

### 5.5c Textarea 自动增高

- `ChatInput.vue`：输入内容增多时 textarea 自动变高，最多 5 行
- 使用 `scrollHeight` 动态设置高度

**文件**：`frontend/src/components/chat/ChatInput.vue`

---

## 5.6 页面过渡动画

### 路由切换动画
- `App.vue`：`<router-view>` 包裹 `<Transition>` 组件
- 淡入淡出效果：`opacity 0→1`，时长 200ms
- 使用 Vue 内置 `<Transition>` 的 CSS 类名

### 列表进场动画
- 世界书卡片网格：依次进场动画（staggered fade-in-up）
- 使用 `<TransitionGroup>` + CSS `transition-delay` 递增
- 对话消息列表：新消息滑入动画

### 其他微动画
- 角色面板展开/收起：宽度过渡 300ms
- 抽屉侧边弹出：已有（保持不变）
- 弹窗出现：scale 0.95→1 + fade

**文件**：
- `frontend/src/App.vue`
- `frontend/src/styles/transitions.css`（新建）
- `frontend/src/views/WorldListView.vue`
- `frontend/src/components/chat/ChatMessage.vue`

---

## 实施顺序

按优先级和依赖关系排列：

| 阶段 | 任务 | 预计工作量 | 优先级 |
|------|------|-----------|--------|
| A | 5.5c textarea 自动增高 | 小 | P0 |
| A | 5.5a 重新生成回复 | 小 | P0 |
| B | 5.6 页面过渡动画 | 中 | P1 |
| B | 5.1 世界书搜索增强 | 中 | P1 |
| C | 5.4 角色切换弹窗 | 中 | P1 |
| C | 5.5b 消息编辑 | 中 | P1 |
| D | 5.2 角色推荐与快捷入口 | 中 | P2 |
| D | 5.3 角色情绪变化 | 大 | P2 |

**阶段 A**（快速见效）：输入框增强，改动小但体验提升明显
**阶段 B**（视觉提升）：动画 + 搜索，让系统更精致
**阶段 C**（流程优化）：角色切换 + 消息编辑，减少操作步骤
**阶段 D**（锦上添花）：推荐 + 情绪系统，提升沉浸感

---

## 验证清单

- [ ] 世界书标签动态加载，多标签筛选正常
- [ ] 搜索 + 标签联动，空结果有提示
- [ ] "最近对话"角色列表正确显示
- [ ] 热门角色按对话数排序
- [ ] AI 回复包含情绪标签，前端正确解析并隐藏
- [ ] 角色面板显示当前情绪
- [ ] "+ 新对话"弹出角色选择器，选中后直接开始对话
- [ ] 重新生成按钮工作正常
- [ ] 编辑用户消息后重新生成
- [ ] textarea 随内容自动增高（最多 5 行）
- [ ] 路由切换有淡入淡出动画
- [ ] 世界书卡片有进场动画
- [ ] 角色面板展开/收起有过渡动画
