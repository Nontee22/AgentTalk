# -*- coding: utf-8 -*-
"""Standalone embedding microservice — loads the model once, serves via HTTP.

Run: uvicorn main:app --host 0.0.0.0 --port 8001
"""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

model: SentenceTransformer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    print(f"Loading embedding model: {model_name} ...")
    model = SentenceTransformer(model_name)
    print("Embedding model loaded.")
    yield
    model = None


app = FastAPI(title="Embedding Service", lifespan=lifespan)


class EmbedRequest(BaseModel):
    texts: list[str]


class EmbedResponse(BaseModel):
    vectors: list[list[float]]


@app.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest):
    if not req.texts:
        return EmbedResponse(vectors=[])
    vectors = model.encode(req.texts, normalize_embeddings=True).tolist()
    return EmbedResponse(vectors=vectors)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}
