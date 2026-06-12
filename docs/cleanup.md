# 可删除文件清单

## 1. 构建/缓存产物（自动生成，可安全删除）

| 路径 | 说明 |
|------|------|
| `backend/alembic/versions/*.py` | Alembic 迁移文件，DB 将重建 |
| `backend/.pytest_cache/` | Pytest 缓存目录 |
| `backend/roleplay_chat_backend.egg-info/` | pip editable 安装元数据 |
| `backend/**/__pycache__/` | Python 字节码缓存（约 30 个 .pyc 文件） |

## 2. IDE 配置（开发者本地，不应入库）

| 路径 | 说明 |
|------|------|
| `.idea/` | JetBrains IDE 配置（8 个文件），已在 .gitignore |

## 3. 废弃/未使用的源文件

| 路径 | 说明 |
|------|------|
| `frontend/src/views/HomeView.vue` | 早期健康检查调试页，路由和组件中零引用，已完全孤立 |
| `backend/app/prompts/` | 计划中的提示词模板目录，仅含空 `.gitkeep`，从未使用 |

## 4. 旧规划文档

| 路径 | 说明 |
|------|------|
| `docs/superpowers/plans/2026-05-28-phase0-environment-setup.md` | Phase 0 环境搭建计划，已完成 |

## 5. 测试上传文件（DB 重建后将成为孤立数据）

| 路径 | 说明 |
|------|------|
| `uploads/avatars/` | 6 个示例角色头像（UUID 命名的 .jpg） |
| `uploads/covers/` | 7 个示例世界书封面（UUID 命名的 .png/.jpg） |

> 已在 .gitignore 中，删除可选。DB 重建后这些文件不再被任何记录引用。

## 清理命令

```bash
# 迁移文件
rm -f backend/alembic/versions/*.py

# 缓存/构建产物
rm -rf backend/.pytest_cache/
rm -rf backend/roleplay_chat_backend.egg-info/
find backend/ -type d -name __pycache__ -exec rm -rf {} +

# IDE 配置
rm -rf .idea/

# 废弃源文件
rm -f frontend/src/views/HomeView.vue
rm -rf backend/app/prompts/

# 旧规划文档
rm -f docs/superpowers/plans/2026-05-28-phase0-environment-setup.md

# 孤立上传文件（可选）
rm -rf uploads/avatars/ uploads/covers/
```
