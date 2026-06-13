# -*- coding: utf-8 -*-
"""Embedding service — loads SentenceTransformer locally.

Provides generate_embedding / generate_embeddings for memory_service.py.
Model is lazy-loaded on first call.
"""

import logging
from pathlib import Path

from app.core.config import PROJECT_ROOT, settings

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        model_path = settings.memory_embedding_model
        # Resolve relative paths against project root (not cwd)
        if not Path(model_path).is_absolute() and not model_path.startswith("/"):
            resolved = PROJECT_ROOT / model_path
            if resolved.exists():
                model_path = str(resolved)

        logger.info("Loading embedding model: %s ...", model_path)
        _model = SentenceTransformer(model_path)
        logger.info("Embedding model loaded.")
    return _model


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding vector for a single text string."""
    vectors = await generate_embeddings([text])
    return vectors[0]


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Batch embed multiple texts."""
    if not texts:
        return []

    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()
