import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import LLMError
from app.models.conversation import Conversation
from app.models.user import User
from app.schemas.chat import (
    ChatStartResponse,
    ConversationCreate,
    ConversationSummary,
    MessageCreate,
    MessageOut,
)
from app.schemas.common import PaginatedResponse
from app.services import chat_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


async def _check_conversation_owner(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> Conversation:
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    return conversation


@router.post("/start", response_model=ChatStartResponse, status_code=201)
async def start_chat(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        conversation, greeting = await chat_service.start_conversation(
            db, data.character_id, data.world_id, user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ChatStartResponse(
        conversation_id=conversation.id,
        greeting_message=MessageOut.model_validate(greeting) if greeting else None,
    )


@router.post("/{conversation_id}/send")
async def send_message(
    conversation_id: uuid.UUID,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_conversation_owner(db, conversation_id, current_user.id)

    async def event_stream():
        try:
            async for token in chat_service.send_message_stream(
                db, conversation_id, data.content
            ):
                yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except ValueError as e:
            logger.warning("Chat value error: conv=%s, %s", conversation_id, e)
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        except LLMError as e:
            logger.error("LLM error: conv=%s, model=%s, %s", conversation_id, e.model, e.message)
            yield f"data: {json.dumps({'error': e.message}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.exception("Unexpected error in chat stream: conv=%s", conversation_id)
            yield f"data: {json.dumps({'error': 'LLM 调用失败，请稍后重试'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{conversation_id}/stop")
async def stop_generation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_conversation_owner(db, conversation_id, current_user.id)

    from app.services.stream_registry import cancel_stream

    cancelled = cancel_stream(conversation_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="No active stream found")
    return {"status": "stopped"}


@router.get("/conversations", response_model=PaginatedResponse[ConversationSummary])
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await chat_service.get_conversations(
        db, user_id=current_user.id, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[ConversationSummary(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{conversation_id}", response_model=PaginatedResponse[MessageOut])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_conversation_owner(db, conversation_id, current_user.id)

    messages, total = await chat_service.get_messages(
        db, conversation_id, page, page_size
    )
    return PaginatedResponse(
        items=[MessageOut.model_validate(m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _check_conversation_owner(db, conversation_id, current_user.id)

    deleted = await chat_service.delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
