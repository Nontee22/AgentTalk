# -*- coding: utf-8 -*-
"""Drop all tables, recreate schema, and seed initial data.

Usage:
    cd backend
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# 将 backend/ 加入 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, engine
from sqlalchemy import text
from app.models import User, WorldBook, Character, Conversation, Message, CharacterMemory  # noqa: F401


async def recreate_tables():
    """删除所有表，然后按最新模型重新创建。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("已删除所有表。")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("已启用 pgvector 扩展。")
        await conn.run_sync(Base.metadata.create_all)
        print("已重新创建所有表：users, world_books, characters, conversations, messages, character_memories")
    await engine.dispose()


async def main():
    # 第一步：重建表
    await recreate_tables()

    # 第二步：插入种子数据
    from seed import seed  # seed.py 和 init_db.py 在同一目录
    await seed()

    print("\n数据库初始化完成！")
    print("  管理员账号: admin")
    print("  管理员密码: admin123")


if __name__ == "__main__":
    asyncio.run(main())
