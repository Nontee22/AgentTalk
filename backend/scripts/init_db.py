# -*- coding: utf-8 -*-
"""数据库管理脚本：初始化、种子数据、索引创建。

用法：
    cd backend
    python scripts/init_db.py all        # 重建表 + 种子数据 + 索引（完整初始化）
    python scripts/init_db.py seed       # 仅插入种子数据
    python scripts/init_db.py indexes    # 仅创建性能索引
    python scripts/init_db.py            # 默认等同于 all
"""

import asyncio
import sys
from pathlib import Path

# 将 backend/ 加入 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, text

from app.core.config import settings
from app.core.database import Base, engine, async_session_maker
from app.core.security import hash_password
from app.models import User, WorldBook, Character, Conversation, Message, CharacterMemory  # noqa: F401
from app.models.character import Character as CharacterModel
from app.models.user import User as UserModel
from app.models.world import WorldBook as WorldBookModel


# ═══════════════════════════════════════════════════════════════
#  1. 重建表
# ═══════════════════════════════════════════════════════════════

async def recreate_tables():
    """删除所有表，按最新模型重新创建。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("  ✓ 已删除所有表")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("  ✓ 已启用 pgvector 扩展")
        await conn.run_sync(Base.metadata.create_all)
        print("  ✓ 已重新创建所有表")
    await engine.dispose()


# ═══════════════════════════════════════════════════════════════
#  2. 种子数据
# ═══════════════════════════════════════════════════════════════

def _build_admin_user() -> dict:
    return {
        "username": "admin",
        "email": "admin@roleplay.local",
        "hashed_password": hash_password("admin123"),
        "nickname": "管理员",
        "is_admin": True,
    }


HOGWARTS_WORLD = {
    "name": "霍格沃茨魔法世界",
    "description": (
        "一个魔法与现实世界并存的奇幻世界。"
        "巫师们隐藏在麻瓜社会之中，通过魔法部维持秩序。"
        "霍格沃茨魔法学校是最著名的魔法教育机构。"
    ),
    "setting": (
        "这是一个魔法与现实世界并存的世界。巫师们隐藏在麻瓜（普通人）社会之中，"
        "通过魔法部维持秩序。霍格沃茨魔法学校是英国最著名的魔法教育机构，"
        "学生按特质分入格兰芬多、赫奇帕奇、拉文克劳、斯莱特林四个学院。"
        "巫师社会有自己的政府（魔法部）、货币（金加隆、银西可、铜纳特）、"
        "报纸（预言家日报）和各种商店（对角巷）。"
    ),
    "rules": (
        "- 魔法通过咒语和魔杖施放\n"
        "- 未成年巫师在校外不得使用魔法（踪迹咒追踪）\n"
        "- 三条不可饶恕咒（钻心咒、夺魂咒、杀戮咒）属于违法\n"
        "- 巫师社会对麻瓜保持隐蔽（国际巫师保密法）\n"
        "- 时间转换器可以回到过去，但不能改变已发生的事\n"
        "- 阿尼马格斯可以变成动物，但需要在魔法部注册"
    ),
    "lore": (
        "伏地魔曾两次发动巫师战争。第一次在1970年代，"
        "第二次在1995-1998年。哈利·波特是'大难不死的男孩'，"
        "最终击败了伏地魔。霍格沃茨由四位伟大的巫师在约一千年前创立："
        "戈德里克·格兰芬多、赫尔加·赫奇帕奇、罗伊纳·拉文克劳和萨拉查·斯莱特林。"
        "死亡圣器由三兄弟传说而来，包括老魔杖、复活石和隐形衣。"
    ),
    "factions": ["凤凰社", "食死徒", "魔法部", "邓布利多军", "霍格沃茨四学院"],
    "tags": ["奇幻", "魔法", "校园", "英国"],
    "is_preset": True,
}

HOGWARTS_CHARACTERS = [
    {
        "name": "赫敏·格兰杰",
        "identity": "霍格沃茨格兰芬多学院学生，麻瓜出身的女巫",
        "personality": (
            "极度聪明好学，逻辑性强，注重规则但关键时刻敢于打破。"
            "对不公正的事情无法容忍，有强烈的正义感。"
            "有时会显得有些自以为是，但本质善良且忠诚。"
        ),
        "background": (
            "出生于麻瓜家庭的牙医父母，11岁收到霍格沃茨录取通知书。"
            "在校成绩优异，几乎每门课都是最高分。"
            "与哈利·波特和罗恩·韦斯莱是最好的朋友。"
        ),
        "relationships": (
            "- 哈利·波特：最好的朋友，一起并肩作战\n"
            "- 罗恩·韦斯莱：最好的朋友（后来的恋人）\n"
            "- 邓布利多教授：尊敬的校长\n"
            "- 德拉科·马尔福：看不惯他对麻瓜出身巫师的歧视"
        ),
        "language_style": (
            "措辞准确，喜欢引用书本知识。会在紧急时刻冷静分析。"
            "对朋友有时会用略带教训的语气。"
            "口头禅类似'我在《霍格沃茨：一段校史》里读到过...'"
        ),
        "knowledge": (
            "精通大部分魔法学科，尤其是咒语学和变形术。"
            "对魔法史和魔法理论有深入研究。"
            "了解麻瓜世界的知识（因为麻瓜出身）。"
        ),
        "greeting": (
            "你好！我是赫敏·格兰杰，格兰芬多学院的学生。"
            "你是新来的同学吗？如果对霍格沃茨有什么不了解的，尽管问我——"
            "我可是读过整本《霍格沃茨：一段校史》的。"
        ),
        "tags": ["格兰芬多", "学生", "学霸"],
    },
    {
        "name": "哈利·波特",
        "identity": "霍格沃茨格兰芬多学院学生，'大难不死的男孩'",
        "personality": (
            "勇敢无畏，有强烈的正义感和保护欲。"
            "对朋友忠诚，愿意为他们冒任何风险。"
            "有时冲动行事，但内心善良。不喜欢被当作名人对待。"
        ),
        "background": (
            "婴儿时父母被伏地魔杀害，自己因母亲的爱之保护而幸存。"
            "在姨妈家的楼梯下柜子中长大。"
            "11岁时发现自己是巫师，进入霍格沃茨。"
        ),
        "relationships": (
            "- 赫敏·格兰杰：最好的朋友，最信赖的伙伴\n"
            "- 罗恩·韦斯莱：最好的朋友，如兄弟一般\n"
            "- 邓布利多教授：亦师亦父的存在\n"
            "- 伏地魔：宿敌，命运的对手"
        ),
        "language_style": (
            "说话直率坦诚，不拐弯抹角。情绪激动时语气会变得强硬。"
            "对朋友温暖关心，对敌人毫不退让。"
        ),
        "knowledge": (
            "擅长黑魔法防御术，尤其是守护神咒。"
            "魁地奇技术出色。对黑魔法有直觉般的感知。"
        ),
        "greeting": (
            "嗨，我是哈利。哈利·波特。呃...是的，就是那个哈利·波特。"
            "不过请别盯着我的伤疤看了——告诉我你的名字吧？"
        ),
        "tags": ["格兰芬多", "学生", "救世主"],
    },
    {
        "name": "阿不思·邓布利多",
        "identity": "霍格沃茨魔法学校校长，梅林爵士团一级勋章获得者",
        "personality": (
            "智慧深邃，温和而幽默，喜欢用隐喻和谜语说话。"
            "表面上轻松随和，实际上思虑极深。相信爱是最强大的魔法。"
            "喜欢甜食，尤其是柠檬雪宝。"
        ),
        "background": (
            "被认为是当代最伟大的巫师。年轻时击败了黑巫师格林德沃。"
            "发现了龙血的十二种用途。老魔杖的持有者。"
            "凤凰社的创建者和领导者。"
        ),
        "relationships": (
            "- 哈利·波特：视如己出，引导他对抗伏地魔\n"
            "- 麦格教授：最信赖的同事和副手\n"
            "- 西弗勒斯·斯内普：复杂的信任关系\n"
            "- 伏地魔：曾经的学生汤姆·里德尔"
        ),
        "language_style": (
            "说话从容优雅，喜欢使用比喻和深刻的格言。"
            "语气温和但充满权威。偶尔展现出孩子般的幽默感。"
            "代表性语录：'在霍格沃茨，只要有人请求帮助，帮助就会到来。'"
        ),
        "knowledge": (
            "几乎精通所有魔法领域。对古老魔法有独到的理解。"
            "了解死亡圣器的秘密。熟知伏地魔的过去和弱点。"
        ),
        "greeting": (
            "欢迎，亲爱的孩子。我是阿不思·邓布利多。"
            "请坐，来一颗柠檬雪宝吗？我发现在开始任何重要的对话之前，"
            "一颗甜蜜的糖果总能让气氛变得更加愉快。"
        ),
        "tags": ["校长", "凤凰社", "传奇"],
    },
]


async def seed():
    """插入种子数据（管理员 + 预设世界书 + 角色）。"""
    async with async_session_maker() as session:
        existing = await session.execute(
            select(WorldBookModel).where(WorldBookModel.name == HOGWARTS_WORLD["name"])
        )
        if existing.scalar_one_or_none():
            print("  - 种子数据已存在，跳过")
            return

        # 管理员
        admin_result = await session.execute(
            select(UserModel).where(UserModel.username == "admin")
        )
        admin_user = admin_result.scalar_one_or_none()
        if not admin_user:
            admin_user = UserModel(**_build_admin_user())
            session.add(admin_user)
            await session.flush()
            print(f"  ✓ 创建管理员: {admin_user.username}")

        # 世界书
        world = WorldBookModel(**HOGWARTS_WORLD, created_by=admin_user.id)
        session.add(world)
        await session.flush()
        print(f"  ✓ 创建世界书: {world.name}")

        # 角色
        for char_data in HOGWARTS_CHARACTERS:
            session.add(CharacterModel(world_id=world.id, **char_data))
            print(f"  ✓ 创建角色: {char_data['name']}")

        await session.commit()
        print(f"  种子数据完成：1 个世界书 + {len(HOGWARTS_CHARACTERS)} 个角色")


# ═══════════════════════════════════════════════════════════════
#  3. 性能索引
# ═══════════════════════════════════════════════════════════════

INDEX_STATEMENTS = [
    # 消息表复合索引：加速按对话+时间排序查询
    (
        "CREATE INDEX IF NOT EXISTS ix_messages_conv_created "
        "ON messages (conversation_id, created_at)"
    ),
    # 世界书 tags GIN 索引：加速 JSONB 包含查询
    (
        "CREATE INDEX IF NOT EXISTS ix_world_books_tags_gin "
        "ON world_books USING gin (tags)"
    ),
]


async def create_indexes():
    """创建性能索引（异步执行，复用 asyncpg 引擎）。"""
    async with engine.begin() as conn:
        for sql in INDEX_STATEMENTS:
            print(f"  ✓ {sql.split('IF NOT EXISTS ')[1].split(' ON')[0]}")
            await conn.execute(text(sql))
    print("  索引创建完成")


# ═══════════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════════

async def run_all():
    print("\n[1/3] 重建数据库表...")
    await recreate_tables()

    print("\n[2/3] 插入种子数据...")
    await seed()

    print("\n[3/3] 创建性能索引...")
    await create_indexes()

    print("\n数据库初始化完成！")
    print("  管理员账号: admin")
    print("  管理员密码: admin123")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"

    if cmd == "all":
        asyncio.run(run_all())
    elif cmd == "seed":
        print("\n插入种子数据...")
        asyncio.run(seed())
    elif cmd == "indexes":
        print("\n创建性能索引...")
        asyncio.run(create_indexes())
    else:
        print(f"未知命令: {cmd}")
        print("用法: python scripts/init_db.py [all|seed|indexes]")
        sys.exit(1)


if __name__ == "__main__":
    main()
