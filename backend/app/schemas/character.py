import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CharacterCreate(BaseModel):
    name: str = Field(..., max_length=100)
    avatar: str | None = None
    identity: str | None = Field(None, max_length=500)
    personality: str | None = Field(None, max_length=5000)
    background: str | None = Field(None, max_length=5000)
    relationships: str | None = Field(None, max_length=3000)
    language_style: str | None = Field(None, max_length=3000)
    knowledge: str | None = Field(None, max_length=5000)
    greeting: str | None = Field(None, max_length=2000)
    tags: list[str] | None = Field(None, max_length=20)


class CharacterUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    avatar: str | None = None
    identity: str | None = Field(None, max_length=500)
    personality: str | None = Field(None, max_length=5000)
    background: str | None = Field(None, max_length=5000)
    relationships: str | None = Field(None, max_length=3000)
    language_style: str | None = Field(None, max_length=3000)
    knowledge: str | None = Field(None, max_length=5000)
    greeting: str | None = Field(None, max_length=2000)
    tags: list[str] | None = Field(None, max_length=20)


class CharacterSummary(BaseModel):
    id: uuid.UUID
    name: str
    avatar: str | None
    identity: str | None
    tags: list[str] | None

    model_config = {"from_attributes": True}


class CharacterDetail(BaseModel):
    id: uuid.UUID
    world_id: uuid.UUID
    name: str
    avatar: str | None
    identity: str | None
    personality: str | None
    background: str | None
    relationships: str | None
    language_style: str | None
    knowledge: str | None
    greeting: str | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
