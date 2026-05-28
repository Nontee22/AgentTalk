from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.core.config import settings

client = AsyncOpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_base_url,
)


async def chat_stream(
    messages: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        max_tokens=settings.llm_max_tokens,
        temperature=settings.llm_temperature,
        stream=True,
    )
    async for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
