import uuid
from datetime import datetime

from pydantic import BaseModel


class ConversationCreate(BaseModel):
    character_id: uuid.UUID
    world_id: uuid.UUID


class ConversationSummary(BaseModel):
    id: uuid.UUID
    character_id: uuid.UUID
    world_id: uuid.UUID
    title: str | None
    message_count: int
    character_name: str | None = None
    character_avatar: str | None = None
    last_message: str | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatStartResponse(BaseModel):
    conversation_id: uuid.UUID
    greeting_message: MessageOut | None = None
