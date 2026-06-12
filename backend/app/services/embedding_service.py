# -*- coding: utf-8 -*-
"""Embedding service — lazy-loads sentence-transformers model for vector generation.

NOTE: The model loads in the web process on first request (~2-5s, ~200MB RAM).
For production, consider pre-loading in lifespan or offloading to a worker process.
"""

import asyncio
import logging

from sentence_transformers import SentenceTransformer

from app.core.config import settings, PROJECT_ROOT

logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None
_lock = asyncio.Lock()


def _resolve_model_path(model_name: str) -> str:
    """If model_name is a relative path (starts with ./ or ..), resolve from PROJECT_ROOT."""
    if model_name.startswith("./") or model_name.startswith(".."):
        resolved = (PROJECT_ROOT / model_name).resolve()
        return str(resolved)
    return model_name


async def _get_model() -> SentenceTransformer:
    """Lazy load with async lock. First call downloads ~100MB model."""
    global _model
    if _model is None:
        async with _lock:
            if _model is None:
                model_path = _resolve_model_path(settings.memory_embedding_model)
                logger.info(
                    "Loading embedding model: %s ...",
                    model_path,
                )
                loop = asyncio.get_running_loop()
                _model = await loop.run_in_executor(
                    None,
                    lambda: SentenceTransformer(model_path),
                )
                logger.info("Embedding model loaded successfully.")
    return _model


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector for a single text string."""
    model = await _get_model()
    loop = asyncio.get_running_loop()
    vector = await loop.run_in_executor(
        None,
        lambda: model.encode(text, normalize_embeddings=True).tolist(),
    )
    return vector


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Batch embed multiple texts."""
    if not texts:
        return []
    model = await _get_model()
    loop = asyncio.get_running_loop()
    vectors = await loop.run_in_executor(
        None,
        lambda: model.encode(texts, normalize_embeddings=True).tolist(),
    )
    return vectors
