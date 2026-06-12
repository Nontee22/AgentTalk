# -*- coding: utf-8 -*-
"""Memory service — extraction, storage, retrieval of long-term character memories."""

import json
import logging
import math
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.character_memory import CharacterMemory
from app.services.embedding_service import generate_embedding, generate_embeddings
from app.services.llm_service import generate_completion
from app.services.token_counter import estimate_tokens

logger = logging.getLogger(__name__)

VALID_CATEGORIES = {"fact", "relationship", "preference", "event"}

# ─── Extraction ───────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """\
你是角色扮演对话的记忆提取专家。你的任务是从对话中提取值得长期记住的关键信息。

## 输出格式
严格输出 JSON 数组，不要添加任何解释文字：
[{"content": "...", "category": "...", "importance": 0.0-1.0}]
如果没有值得记住的新信息，输出空数组 []

## 分类定义与示例
- **fact**: 关于用户或世界的客观事实
  示例: "用户是一名大学生，主修计算机科学"、"用户有一只叫小白的猫"
- **relationship**: 用户与角色之间的关系变化
  示例: "用户向角色表白并被接受"、"用户和角色因误会发生争吵"
- **preference**: 用户的喜好、习惯、观点
  示例: "用户喜欢喝咖啡，不喝茶"、"用户讨厌被人叫小名"
- **event**: 对话中发生的重要事件
  示例: "用户和角色一起去了海边旅行"、"角色送给用户一条项链作为生日礼物"

## importance 评分标准
- 0.8-1.0: 重大事件、关系转折、核心身份信息
- 0.5-0.7: 有意义的偏好、一般事实、日常事件
- 0.3-0.4: 次要细节，但可能在未来有用

## 不要提取
- 打招呼、寒暄、无实质内容的客套话
- 角色设定本身已包含的信息（角色的名字、身份、性格等）
- 与已有记忆重复或高度相似的信息
- 纯粹的角色扮演动作描写（如"角色微笑了一下"）
- 过于模糊或无法脱离上下文理解的信息

## 质量要求
- 每条记忆必须是独立的、自包含的一句话（不依赖上下文即可理解）
- 使用第三人称描述（"用户喜欢..."而非"你喜欢..."）
- 保持简洁，每条 10-80 字"""

EXTRACTION_USER_TEMPLATE = """\
## 角色信息
角色名: {character_name}
{character_context}

## 用户信息
用户名: {username}

## 最近对话
{conversation_text}

## 已有记忆（避免重复提取）
{existing_memories}

请提取对话中值得长期记忆的新信息。"""


async def extract_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    character_id: uuid.UUID,
    conversation_id: uuid.UUID,
    character_name: str,
    username: str,
    messages: list[dict],
    character_identity: str = "",
    character_personality: str = "",
) -> list[CharacterMemory]:
    """Call LLM to extract memories from recent messages, embed, dedup, and store."""
    # 1. Format conversation text
    conversation_text = "\n".join(
        f"{'用户' if m['role'] == 'user' else character_name}: {m['content']}"
        for m in messages
    )

    # 2. Build character context summary
    context_parts = []
    if character_identity:
        context_parts.append(f"身份: {character_identity[:200]}")
    if character_personality:
        context_parts.append(f"性格: {character_personality[:200]}")
    character_context = "\n".join(context_parts) if context_parts else "（无额外信息）"

    # 3. Load existing memories for dedup context
    existing = await get_memories_for_pair(db, user_id, character_id, limit=20)
    existing_text = "\n".join(f"- [{m.category}] {m.content}" for m in existing) or "无"

    # 4. Call LLM for extraction
    user_prompt = EXTRACTION_USER_TEMPLATE.format(
        character_name=character_name,
        character_context=character_context,
        username=username,
        conversation_text=conversation_text,
        existing_memories=existing_text,
    )
    raw = await generate_completion(
        user_prompt,
        max_tokens=1024,
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
    )
    items = _parse_extraction_response(raw)

    if not items:
        logger.debug("No memories extracted for user=%s, character=%s", user_id, character_id)
        return []

    # 5. Embed all new memory contents
    texts = [item["content"] for item in items]
    vectors = await generate_embeddings(texts)

    # 6. Dedup against existing DB memories AND within this batch, then store
    new_memories: list[CharacterMemory] = []
    batch_vectors: list[list[float]] = []

    for item, vec in zip(items, vectors):
        # Check against DB
        if await _is_duplicate(db, user_id, character_id, vec, threshold=0.85):
            logger.debug("Duplicate memory skipped (DB): %s", item["content"][:50])
            continue

        # Check against already-accepted items in this batch
        if _is_duplicate_in_batch(vec, batch_vectors, threshold=0.85):
            logger.debug("Duplicate memory skipped (batch): %s", item["content"][:50])
            continue

        memory = CharacterMemory(
            user_id=user_id,
            character_id=character_id,
            conversation_id=conversation_id,
            content=item["content"],
            category=item.get("category", "fact"),
            importance=max(0.0, min(1.0, float(item.get("importance", 0.5)))),
            embedding=vec,
        )
        db.add(memory)
        new_memories.append(memory)
        batch_vectors.append(vec)

    if new_memories:
        await db.commit()
        logger.info(
            "Extracted %d memories for user=%s, character=%s",
            len(new_memories), user_id, character_id,
        )

    return new_memories


def _parse_extraction_response(raw: str) -> list[dict]:
    """Extract JSON array from LLM response with strict validation."""
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        logger.warning("No JSON array found in extraction response: %s", raw[:200])
        return []

    try:
        result = json.loads(match.group())
    except json.JSONDecodeError:
        logger.warning("Failed to parse memory extraction JSON: %s", raw[:200])
        return []

    if not isinstance(result, list):
        return []

    validated = []
    for item in result:
        if not isinstance(item, dict) or "content" not in item:
            continue

        content = str(item["content"]).strip()
        # Length check: 4-200 chars
        if len(content) < 4 or len(content) > 200:
            logger.debug("Memory skipped (length=%d): %s", len(content), content[:50])
            continue

        # Normalize category
        category = str(item.get("category", "fact")).strip().lower()
        if category not in VALID_CATEGORIES:
            category = "fact"

        # Clamp importance
        try:
            importance = max(0.0, min(1.0, float(item.get("importance", 0.5))))
        except (ValueError, TypeError):
            importance = 0.5

        validated.append({
            "content": content,
            "category": category,
            "importance": importance,
        })

    return validated


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _is_duplicate_in_batch(
    embedding: list[float],
    batch_vectors: list[list[float]],
    threshold: float = 0.85,
) -> bool:
    """Check if a new memory is a near-duplicate of any already-accepted item in this batch."""
    for existing_vec in batch_vectors:
        if _cosine_similarity(embedding, existing_vec) >= threshold:
            return True
    return False


async def _is_duplicate(
    db: AsyncSession,
    user_id: uuid.UUID,
    character_id: uuid.UUID,
    embedding: list[float],
    threshold: float = 0.85,
) -> bool:
    """Check if a near-duplicate memory already exists in DB via cosine similarity."""
    result = await db.execute(
        select(
            CharacterMemory.id,
            (1 - CharacterMemory.embedding.cosine_distance(embedding)).label("similarity"),
        )
        .where(
            CharacterMemory.user_id == user_id,
            CharacterMemory.character_id == character_id,
        )
        .order_by(CharacterMemory.embedding.cosine_distance(embedding))
        .limit(1)
    )
    row = result.first()
    if row is None:
        return False
    return row.similarity >= threshold


# ─── Retrieval ────────────────────────────────────────────────────

async def retrieve_relevant_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    character_id: uuid.UUID,
    query_text: str,
    top_k: int | None = None,
    token_budget: int | None = None,
) -> list[dict]:
    """
    Retrieve top-K memories by time-decayed semantic similarity,
    fitted within token_budget.
    """
    top_k = top_k or settings.memory_max_per_query
    token_budget = token_budget or settings.memory_token_budget

    query_vec = await generate_embedding(query_text)
    now = datetime.now(timezone.utc)

    # Retrieve more candidates than needed, then re-rank with decay
    candidates_limit = top_k * 3
    result = await db.execute(
        select(
            CharacterMemory,
            (1 - CharacterMemory.embedding.cosine_distance(query_vec)).label("raw_similarity"),
        )
        .where(
            CharacterMemory.user_id == user_id,
            CharacterMemory.character_id == character_id,
        )
        .order_by(CharacterMemory.embedding.cosine_distance(query_vec))
        .limit(candidates_limit)
    )
    rows = result.all()

    if not rows:
        return []

    # Apply time decay and importance weighting
    halflife = settings.memory_decay_halflife_days
    scored = []
    for memory, raw_sim in rows:
        age_days = (now - memory.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 86400
        decay = math.exp(-0.693 * age_days / halflife)
        score = 0.60 * raw_sim + 0.25 * memory.importance + 0.15 * decay
        scored.append((memory, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    # Take top-K within token budget
    selected: list[dict] = []
    used_tokens = 0
    for memory, score in scored[:top_k]:
        mem_tokens = estimate_tokens(memory.content)
        if used_tokens + mem_tokens > token_budget:
            break
        selected.append({
            "content": memory.content,
            "category": memory.category,
            "importance": memory.importance,
            "score": round(score, 3),
        })
        used_tokens += mem_tokens
        memory.last_accessed_at = now

    if selected:
        await db.commit()

    return selected


# ─── Management ───────────────────────────────────────────────────

async def get_memories_for_pair(
    db: AsyncSession,
    user_id: uuid.UUID,
    character_id: uuid.UUID,
    limit: int = 50,
) -> list[CharacterMemory]:
    """Get all memories for a user-character pair, newest first."""
    result = await db.execute(
        select(CharacterMemory)
        .where(
            CharacterMemory.user_id == user_id,
            CharacterMemory.character_id == character_id,
        )
        .order_by(CharacterMemory.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def delete_memory(
    db: AsyncSession, memory_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    """Delete a memory, scoped to user for safety."""
    result = await db.execute(
        delete(CharacterMemory).where(
            CharacterMemory.id == memory_id,
            CharacterMemory.user_id == user_id,
        )
    )
    await db.commit()
    return result.rowcount > 0
