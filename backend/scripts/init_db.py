# -*- coding: utf-8 -*-
"""Drop all tables, recreate schema, and seed initial data."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import Base, engine
from app.models import User, WorldBook, Character, Conversation, Message  # noqa: F401


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Database recreated successfully.")

    from scripts.seed import seed
    await seed()


if __name__ == "__main__":
    asyncio.run(init())
