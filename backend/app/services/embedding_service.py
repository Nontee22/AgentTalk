# -*- coding: utf-8 -*-
"""Embedding service — calls the standalone embedding microservice via HTTP.

The microservice handles model loading and inference. This module is a thin
HTTP client that preserves the original interface (generate_embedding /
generate_embeddings) so callers (memory_service.py) need no changes.
"""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.embedding_service_url,
            timeout=30.0,
        )
    return _client


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector for a single text string."""
    vectors = await generate_embeddings([text])
    return vectors[0]


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Batch embed multiple texts via the embedding microservice."""
    if not texts:
        return []

    client = _get_client()
    response = await client.post("/embed", json={"texts": texts})
    response.raise_for_status()
    data = response.json()
    return data["vectors"]
