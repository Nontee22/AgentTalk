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

# ─── Extraction ───────────────────────────────────────────────────

EXTRACTION_PROMPT = """你是一个记忆提取器。分析以下角色扮演对话，提取值得长期记住的关键信息。

角色: {character_name}
用户: {username}

对话内容:
{conversation_text}

提取规则:
1. 只提取明确陈述的事实，不要推测
2. 每条记忆必须是独立的、自包含的一句话
3. 分类: fact(事实) / relationship(关系变化) / preference(偏好) / event(重要事件)
4. importance: 0.0-1.0，越重要越高
5. 去重: 如果信息与已有记忆重复，不要提取

已有记忆(避免重复):
{existing_memories}

以JSON数组格式输出:
[{{"content": "...", "category": "...", "importance": 0.0-1.0}}]
如果没有值得记住的新信息，输出空数组 []"""


async def extract_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    character_id: uuid.UUID,
    conversation_id: uuid.UUID,
    character_name: str,
    username: str,
    messages: list[dict],
) -> list[CharacterMemory]:
    """Call LLM to extract memories from recent messages, embed, dedup, and store."""
    # 1. Format conversation text
    conversation_text = "\n".join(
        f"{'用户' if m['role'] == 'user' else character_name}: {m['content']}"
        for m in messages
    )

    # 2. Load existing memories for dedup context
    existing = await get_memories_for_pair(db, user_id, character_id, limit=20)
    existing_text = "\n".join(f"- {m.content}" for m in existing) or "无"

    # 3. Call LLM for extraction
    prompt = EXTRACTION_PROMPT.format(
        character_name=character_name,
        username=username,
        conversation_text=conversation_text,
        existing_memories=existing_text,
    )
    raw = await generate_completion(prompt)
    items = _parse_extraction_response(raw)

    if not items:
        logger.debug("No memories extracted for user=%s, character=%s", user_id, character_id)
        return []

    # 4. Embed all new memory contents
    texts = [item["content"] for item in items]
    vectors = await generate_embeddings(texts)

    # 5. Dedup and store
    new_memories: list[CharacterMemory] = []
    for item, vec in zip(items, vectors):
        if await _is_duplicate(db, user_id, character_id, vec, threshold=0.92):
            logger.debug("Duplicate memory skipped: %s", item["content"][:50])
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

    if new_memories:
        await db.commit()
        logger.info(
            "Extracted %d memories for user=%s, character=%s",
            len(new_memories), user_id, character_id,
        )

    return new_memories


def _parse_extraction_response(raw: str) -> list[dict]:
    """Extract JSON array from LLM response, tolerant of markdown fences."""
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return [
                    item for item in result
                    if isinstance(item, dict) and "content" in item
                ]
        except json.JSONDecodeError:
            logger.warning("Failed to parse memory extraction JSON: %s", raw[:200])
    return []


async def _is_duplicate(
    db: AsyncSession,
    user_id: uuid.UUID,
    character_id: uuid.UUID,
    embedding: list[float],
    threshold: float = 0.92,
) -> bool:
    """Check if a near-duplicate memory already exists via cosine similarity."""
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
