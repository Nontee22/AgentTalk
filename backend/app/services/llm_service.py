import asyncio
import logging
from collections.abc import AsyncGenerator

from openai import APIConnectionError, APIStatusError, AsyncOpenAI, RateLimitError

from app.core.config import settings
from app.core.exceptions import LLMError, LLMStreamError

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
    timeout=60.0,
)

# Limit concurrent background LLM calls (title gen, memory extraction)
# to avoid overwhelming the API. chat_stream is NOT gated by this.
_background_semaphore = asyncio.Semaphore(3)


async def _retry_completion(create_kwargs: dict, max_retries: int = 2) -> str:
    """Call chat.completions.create with simple exponential backoff retry."""
    for attempt in range(max_retries + 1):
        try:
            response = await client.chat.completions.create(**create_kwargs)
            return response.choices[0].message.content or ""
        except (RateLimitError, APIConnectionError, APIStatusError) as e:
            if attempt == max_retries:
                logger.warning("LLM call failed after %d retries: %s", max_retries, e)
                return ""
            wait = 2 ** attempt  # 1s, 2s
            logger.info("LLM call retry %d/%d after %ds: %s", attempt + 1, max_retries, wait, e)
            await asyncio.sleep(wait)
        except Exception as e:
            logger.warning("LLM call unexpected error: %s", e)
            return ""
    return ""


async def chat_stream(
    messages: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    model = settings.llm_model
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            stream=True,
        )
    except RateLimitError as e:
        logger.error("LLM rate limited: model=%s, %s", model, e)
        raise LLMError("模型调用频率超限，请稍后重试", model=model, status_code=429) from e
    except APIConnectionError as e:
        logger.error("LLM connection failed: model=%s, %s", model, e)
        raise LLMError("无法连接到模型服务", model=model) from e
    except APIStatusError as e:
        logger.error("LLM API error: model=%s, status=%d, %s", model, e.status_code, e)
        raise LLMError(
            f"模型服务返回错误 ({e.status_code})", model=model, status_code=e.status_code
        ) from e

    try:
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        logger.error("LLM stream interrupted: model=%s, %s", model, e)
        raise LLMStreamError("模型生成中断", model=model) from e


async def generate_completion(
    prompt: str,
    max_tokens: int = 1024,
    system_prompt: str | None = None,
) -> str:
    """Non-streaming completion for internal use (memory extraction, etc.)."""
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    async with _background_semaphore:
        return await _retry_completion({
            "model": settings.llm_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        })


async def generate_title(user_msg: str, assistant_msg: str) -> str:
    async with _background_semaphore:
        title = await _retry_completion({
            "model": settings.llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": "根据以下对话生成一个简短的中文标题（不超过15个字），只输出标题文本，不要加引号或其他标点。",
                },
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg[:200]},
                {"role": "user", "content": "请为这段对话生成一个简短标题。"},
            ],
            "max_tokens": 30,
            "temperature": 0.3,
        })
    title = title.strip().strip("\"'""''《》")
    return title[:50] if title else "新对话"
