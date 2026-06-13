import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WorldBookCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)
    setting: str | None = Field(None, max_length=10000)
    rules: str | None = Field(None, max_length=10000)
    lore: str | None = Field(None, max_length=10000)
    factions: list[str] | None = Field(None, max_length=50)
    tags: list[str] | None = Field(None, max_length=20)
    cover_image: str | None = None
    is_preset: bool = False


class WorldBookUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    setting: str | None = Field(None, max_length=10000)
    rules: str | None = Field(None, max_length=10000)
    lore: str | None = Field(None, max_length=10000)
    factions: list[str] | None = Field(None, max_length=50)
    tags: list[str] | None = Field(None, max_length=20)
    cover_image: str | None = None
    is_preset: bool | None = None


class TagCount(BaseModel):
    name: str
    count: int


class WorldBookSummary(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    tags: list[str] | None
    cover_image: str | None
    is_preset: bool
    created_by: uuid.UUID | None = None
    character_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class WorldBookDetail(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    setting: str | None
    rules: str | None
    lore: str | None
    factions: list[str] | None
    tags: list[str] | None
    cover_image: str | None
    is_preset: bool
    created_by: uuid.UUID | None = None
    character_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
