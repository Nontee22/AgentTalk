# -*- coding: utf-8 -*-
"""Memory schemas for API request/response models."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class MemoryOut(BaseModel):
    id: uuid.UUID
    content: str
    category: str
    importance: float
    created_at: datetime
    last_accessed_at: datetime

    model_config = {"from_attributes": True}


class MemoryListResponse(BaseModel):
    memories: list[MemoryOut]
    total: int
