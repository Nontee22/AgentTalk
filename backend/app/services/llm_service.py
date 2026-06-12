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


async def generate_completion(prompt: str, max_tokens: int = 1024) -> str:
    """Non-streaming completion for internal use (memory extraction, etc.)."""
    model = settings.llm_model
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        logger.warning("generate_completion failed: %s", e)
        return ""


async def generate_title(user_msg: str, assistant_msg: str) -> str:
    model = settings.llm_model
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "根据以下对话生成一个简短的中文标题（不超过15个字），只输出标题文本，不要加引号或其他标点。",
                },
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg[:200]},
                {"role": "user", "content": "请为这段对话生成一个简短标题。"},
            ],
            max_tokens=30,
            temperature=0.3,
        )
        title = response.choices[0].message.content.strip().strip("\"'""''《》")
        return title[:50] if title else "新对话"
    except Exception as e:
        logger.warning("Title generation failed: %s", e)
        return ""
