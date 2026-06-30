# -*- coding: utf-8 -*-
"""CharacterMemory model — stores long-term memories per user-character pair."""

# 记忆系统是 AgentTalk 的核心功能之一。
# 它让 AI 角色能够在多轮对话中「记住」用户说过的重要信息，
# 并在后续对话中自然地运用这些记忆，而不是每次对话都「失忆」。
#
# CharacterMemory 模型代表「一条」记忆。
# 比如：用户说"我养了一只猫叫小白" → 系统提取出一条记忆：
#   content="用户有一只叫小白的猫", category="fact", importance=0.7
#
# 每条记忆都关联到特定的 (用户, 角色) 对，
# 并且通过向量（embedding）做语义搜索，而非关键词匹配。

import uuid
from datetime import datetime

# Vector 是 pgvector 扩展提供的类型，用于存储「向量」。
# 简单理解：向量就是一串浮点数 [0.12, 0.87, ... , 0.33]，共 512 个，
# 它代表了文本的「语义位置」。语义相似的文本在向量空间中距离近。
# 这是实现「语义搜索」的关键：不是搜关键词，而是搜「意思相近」的内容。
from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.config import settings


class CharacterMemory(Base):
    """
    【角色记忆模型】
    
    存储一条「用户 × 角色」之间的长期记忆。
    相当于让 AI 角色拥有了一本「日记本」，
    每次和用户聊天后，都会把值得记住的事情写进这本日记里。
    """
    __tablename__ = "character_memories"
    # 数据库中的表名，PostgreSQL 会自动创建这张表。
    # 在 SQL 里可以用 SELECT * FROM character_memories 直接查询。

    # ── 主键 ──────────────────────────────────────────────
    # 每条记忆的唯一编号。用 UUID（通用唯一识别码），
    # 而不是自增整数（1,2,3...），好处是：
    # 1. 不怕并发冲突（不同服务器各自生成 ID 也不会重复）
    # 2. 别人猜不出你的数据有多少条
    # 3. 分布式系统友好
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── 外键：这条记忆属于哪个用户 ──────────────────────
    # 每个用户独立维护自己与各个角色之间的记忆，
    # 张三和爱丽丝聊天的记忆不会影响到李四。
    # ondelete="CASCADE"：如果这个用户账号被删除了，
    #   那么他所有的记忆也会自动被删掉，不会留下孤立的脏数据。
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── 外键：这条记忆是关于哪个角色的 ──────────────────
    # 同样是级联删除：角色被删除 → 对应的记忆也自动清除
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── 外键：这条记忆来自哪次对话（可选） ──────────────
    # 记录来源对话 ID，方便追踪记忆是从哪次聊天中提取出来的。
    # ondelete="SET NULL" 和上面的 CASCADE 不同：
    #   对话可以删除，但记忆要保留（记忆比对话更长期）
    #   如果你删了某次对话，这条记忆不会消失，
    #   只是 conversation_id 变成 NULL（记不清具体从哪来的了，但内容还在）
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── 记忆的文本内容 ──────────────────────────────────
    # 比如："用户是一名大学生，主修计算机科学"
    # 用 Text 类型而不是 String(长度)，
    # 因为记忆长度可能变化较大，Text 没有长度限制
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # ── 记忆分类 ─────────────────────────────────────────
    # 分为四类：
    #   fact（事实）       - 客观信息，如"用户有一只猫"
    #   relationship（关系）- 用户与角色之间的关系变化
    #   preference（偏好）  - 用户的喜好习惯，如"用户喜欢喝咖啡"
    #   event（事件）      - 发生过的事情，如"用户和角色一起去了海边"
    # 这个分类会在前端展示时用不同颜色的标签区分，
    # 也会在 prompt 中告诉 LLM"这条记忆属于什么类型"
    category: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="fact"
    )

    # ── 重要度评分（0.0 ~ 1.0） ─────────────────────────
    # 这是 LLM 在提取记忆时评估的分数：
    #   0.8-1.0：重大事件（关系转折、核心身份信息）
    #   0.5-0.7：有意义的信息（一般事实、日常事件）
    #   0.3-0.4：次要细节
    # 检索时会用这个分数加权，高重要度的记忆更容易被想起
    importance: Mapped[float] = mapped_column(
        Float, nullable=False, server_default="0.5"
    )

    # ── 语义向量（最关键的一列！） ──────────────────────
    # embedding 就是「向量化」后的文本内容。
    # 【类比】想象每个词在三维空间里是一个点：
    #   "猫" 和 "狗" 离得近（都是宠物）
    #   "猫" 和 "汽车" 离得远（完全不是一个概念）
    # embedding 就是把「一句话」也变成这样一个"点"，
    # 文本越相似，点在 512 维空间里就越靠近。
    #
    # 操作系统给 pgvector 提供一个「向量引擎」：
    #   可以根据用户的新问题，找出「语义最相似」的旧记忆，
    #   即使完全没提到同样的关键词也能找到。
    # 比如用户说"我家那位毛孩子"，向量搜索也能匹配到"用户养了一只猫"。
    #
    # Vector(512) 指存储 512 维的浮点数向量，
    # 维度由 memory_embedding_dimension 配置项控制。
    embedding = mapped_column(
        Vector(settings.memory_embedding_dimension), nullable=False
    )

    # ── 创建时间 ─────────────────────────────────────────
    # 记录这条记忆是什么时候从对话中提取出来的。
    # 用于时间衰减：越旧的记忆权重越低；
    # 也用于按时间排序展示。
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── 最后访问时间 ────────────────────────────────────
    # 记录这条记忆最后一次被检索到的时刻。
    # 目前主要用于缓存管理和统计，
    # 未来可用于实现「太久没被想起的记忆自动归档」功能。
    # server_default=func.now() 表示创建时自动设为当前时间
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # ── 表级约束 ─────────────────────────────────────────
    # 创建联合索引 (user_id, character_id)，
    # 因为绝大多数查询都是「查某个用户对某个角色的所有记忆」。
    # 索引相当于给数据库加了一个「目录」，
    # 不加索引的话就要全表扫描，几十万条数据时会很慢。
    __table_args__ = (
        Index("ix_cm_user_character", "user_id", "character_id"),
    )

    def __repr__(self) -> str:
        """让打印出来的对象更可读，调试时方便看内容"""
        preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<CharacterMemory [{self.category}] {preview!r} id={self.id}>"
