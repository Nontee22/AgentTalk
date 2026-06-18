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
from app.services import message_service, stream_service

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
        conversation, greeting = await message_service.start_conversation(
            db, data.character_id, data.world_id, user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ChatStartResponse(
        conversation_id=conversation.id,
        greeting_message=MessageOut.model_validate(greeting) if greeting else None,
    )


# =====================================================================
# 接口：POST /chat/{conversation_id}/send
# 功能：用户在聊天界面发送一条消息，后端调用大模型（LLM）生成回复，
#       并把回复「一个字一个字地」实时推送给前端（这就是"流式输出"）
#
# 为什么不一次性返回完整回复？
#   因为大模型生成一段完整文字可能需要好几秒，如果等全部生成完再返回，
#   用户会看到很长一段时间的空白等待。流式输出可以让用户立刻看到文字出现，
#   就像 ChatGPT 那样「逐字打印」的效果。
#
# 技术实现方式：SSE（Server-Sent Events，服务器推送事件）
#   - 普通的 HTTP 请求是「一问一答」：客户端发请求，服务器返回一次响应就结束了
#   - SSE 可以让服务器在一次请求中「持续不断地」向客户端推送多条数据
#   - 每推送一条数据，格式必须是 "data: 内容\n\n"（data: 开头，两个换行结尾）
#   - 前端用 EventSource 或 fetch+ReadableStream 来逐条接收这些数据
# =====================================================================

@router.post("/{conversation_id}/send")
async def send_message(
    conversation_id: uuid.UUID,   # URL 中的会话 ID，用来找到是哪个聊天记录
    data: MessageCreate,          # 用户发来的消息内容（request body），如 {"content": "你好"}
    current_user: User = Depends(get_current_user),  # 通过 JWT token 解析出的当前登录用户
    db: AsyncSession = Depends(get_db),               # 数据库连接（每次请求自动创建一个，用完自动关闭）
):
    """
    用户发送聊天消息，后端以 SSE 流式推送大模型的回复。

    整体流程（按顺序执行）：
    ┌─────────────────────────────────────────────────────────────┐
    │ 1. 前端发起 POST 请求，携带用户输入的消息内容              │
    │ 2. 后端先检查这个用户有没有权限操作这个会话（防止偷看别人聊天）│
    │ 3. 把用户消息和用户历史、角色设定等拼成 prompt 发给大模型     │
    │ 4. 大模型一个字一个字地返回（流式），后端每收到一个字就立刻推送给前端 │
    │ 5. 大模型回复完毕后，发送 [DONE] 标记告诉前端"我说完了"       │
    └─────────────────────────────────────────────────────────────┘
    """

    # ========== 第一步：权限校验 ==========
    # 检查当前登录的用户是不是这个会话的主人
    # 比如：张三不能去看李四的聊天记录
    # 如果不是主人，这里会直接抛出 HTTP 403（禁止访问）或 404（找不到会话），函数就此结束
    await _check_conversation_owner(db, conversation_id, current_user.id)

    # ========== 第二步：定义一个"生成器函数"，用来一条一条地产生 SSE 事件 ==========
    # 【新手重点】什么是 async generator（异步生成器）？
    #   - 普通函数用 return 返回一个值就结束了
    #   - 生成器函数用 yield 每次"吐出"一个值，然后暂停，等下次再来取下一个值
    #   - 就像挤牙膏：每次挤一点，不是一次性全挤出来
    #   - 这里用 async def + yield，就是异步版本的生成器，适合需要等待 IO 的场景（比如等大模型响应）
    async def event_stream():
        """
        这个内部函数是一个 SSE 事件流生成器。
        它会持续地从大模型服务获取输出，每拿到一小段文字（一个 token，通常是一个字或一个词），
        就立刻把它格式化成 SSE 协议要求的格式，然后 yield 出去给前端。
        """
        # ========== 第三步：开始调用大模型，进入 try-except 保护区域 ==========
        # 为什么要用 try-except？
        #   因为大模型调用可能出各种错（网络超时、API 额度用完、参数错误等等），
        #   我们要保证就算出错了，也能优雅地把错误信息告诉前端，而不是让程序直接崩溃。
        try:
            # 调用 stream_service.send_message_stream，这是一个异步生成器，
            # 它会：① 保存用户消息到数据库
            #       ② 拼接历史消息 + 角色设定 + 世界观 → 构造 prompt
            #       ③ 调用大模型 API，流式获取回复
            #       ④ 把完整的回复保存到数据库
            # async for 就是"异步版本的 for 循环"，每产生一个 token 就进来一次循环体
            async for token in stream_service.send_message_stream(
                db, conversation_id, data.content
            ):
                # ========== 第四步：把每个 token 包装成 SSE 格式推送出去 ==========
                # 【SSE 格式说明】
                #   每一条 SSE 消息必须以 "data: " 开头，以两个换行符 "\n\n" 结尾
                #   例如：data: {"token": "你"}
                #
                # json.dumps 把 Python 字典 {'token': token} 转成 JSON 字符串 '{"token": "你"}'
                # ensure_ascii=False 很重要！不加的话中文会被转成 \uXXXX 这种看不懂的编码
                #   比如 "你好" 会变成 "\u4f60\u597d"，前端显示就乱了
                yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"

            # ========== 第五步：发送结束标记 ==========
            # 大模型的所有回复内容都生成完了，没有更多 token 了
            # 发送一个特殊的 "[DONE]" 标记，前端收到后就知道"AI 说完了"，停止打字机动画
            # 这是借鉴 OpenAI 的 SSE 协议约定
            yield "data: [DONE]\n\n"

        # ========== 异常处理：出了问题怎么办？ ==========
        # 这里用了三层 except，像俄罗斯套娃一样，从最具体的错误到最笼统的错误依次捕获
        # 【原则】越具体的异常越先捕获，这样才能给出更精准的错误提示

        except ValueError as e:
            # ------ 第一层：业务逻辑错误 ------
            # 什么是 ValueError？就是我们代码里主动抛出的"合理性错误"
            # 比如：会话 ID 不存在、角色还没配置好、对话内容为空等等
            # 这些是"可预见的、正常的"错误，所以用 logger.warning（警告级别）记录就行
            # 然后把错误信息通过 SSE 推送给前端，让用户看到具体原因
            logger.warning("Chat value error: conv=%s, %s", conversation_id, e)
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

        except LLMError as e:
            # ------ 第二层：大模型调用错误 ------
            # LLMError 是我们自定义的异常类，专门用来表示调用大模型 API 时出的错
            # 比如：API Key 失效、请求频率超限（rate limit）、模型服务器宕机、响应超时等
            # 这些错误比较严重，用 logger.error（错误级别）记录
            # e.model 记录了是哪个模型出错（如 gpt-4、deepseek 等），方便排查
            # e.message 记录了具体的错误描述
            logger.error("LLM error: conv=%s, model=%s, %s", conversation_id, e.model, e.message)
            yield f"data: {json.dumps({'error': e.message}, ensure_ascii=False)}\n\n"

        except Exception as e:
            # ------ 第三层：兜底异常（最后的保险）------
            # 如果上面两层都没捕获到，说明出了我们没预料到的意外错误
            # 比如：数据库突然断连、内存不足、代码 bug 等等
            # 用 logger.exception 而不是 logger.error，区别在于：
            #   logger.exception 会自动把完整的错误堆栈（traceback）也打印出来，方便定位 bug
            #   logger.error 只打印错误消息，没有堆栈信息
            # 给用户一个友好的通用提示，不要暴露系统内部细节（安全考虑）
            logger.exception("Unexpected error in chat stream: conv=%s", conversation_id)
            yield f"data: {json.dumps({'error': 'LLM 调用失败，请稍后重试'}, ensure_ascii=False)}\n\n"

    # ========== 第六步：把生成器包装成 HTTP 响应返回给前端 ==========
    # StreamingResponse 是 FastAPI 提供的"流式响应"工具
    # 它的特点是：不会等所有数据生成完才返回，而是 yield 一条就立刻推送一条给前端
    # 这正是 SSE 所需要的——建立一条持久的 HTTP 连接，持续推送数据
    return StreamingResponse(
        event_stream(),          # 把上面定义的生成器传进去，FastAPI 会自动逐条调用 yield
        media_type="text/event-stream",  # 告诉浏览器：这不是普通的 JSON，是 SSE 流，请用 SSE 方式处理
        headers={
            # 以下三个 HTTP 响应头，都是为了让 SSE 能正常工作：
            "Cache-Control": "no-cache",    # 禁止浏览器缓存这个响应，每次都获取最新的流数据
            "Connection": "keep-alive",     # 保持 TCP 连接不断开，这样服务器才能持续推送数据
            "X-Accel-Buffering": "no",      # 如果服务器前面有 Nginx 反向代理，Nginx 默认会把响应攒到一起再转发
                                            # 这个头告诉 Nginx："不要攒！来一条转发一条！"，否则流式效果就失效了
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

    cancelled = await cancel_stream(conversation_id)
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
    items, total = await message_service.get_conversations(
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

    messages, total = await message_service.get_messages(
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

    deleted = await message_service.delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
