import uuid

from fastapi import Depends, HTTPException, Header
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User


# =====================================================================
# 依赖注入函数：get_current_user
# 功能：从请求头中解析 JWT token，找出当前登录的用户是谁
#
# 什么是"依赖注入"（Depends）？
#   FastAPI 有一个很方便的机制叫 Depends（依赖）
#   只要在接口的参数里写 current_user: User = Depends(get_current_user)，
#   FastAPI 就会在接口执行前，自动先调用 get_current_user 这个函数，
#   把它的返回值（User 对象）赋给 current_user。
#   如果 get_current_user 抛出了异常（比如 token 无效），接口就直接报错，不会继续执行。
#   这样每个需要登录的接口都不用重复写"解析 token → 查用户"的逻辑，写一次到处复用。
#
# 什么是 JWT？
#   JWT（JSON Web Token）就是一串加密后的字符串，里面存了用户的信息（比如用户 ID）
#   用户登录成功后，服务器会生成一个 JWT 返回给前端
#   之后前端每次请求都在请求头里带上这个 JWT，服务器就能知道"你是谁"
#   请求头格式：Authorization: Bearer eyJhbGciOiJIUz...
#                                  ^^^^^^  ^^^^^^^^^^^^^^^^
#                                  固定前缀  真正的 token 内容
#
# 这个函数的整体流程：
#   ┌───────────────────────────────────────────────┐
#   │ 1. 从请求头取出 Authorization 字段             │
#   │ 2. 检查格式是不是 "Bearer xxx"                │
#   │ 3. 截取 "Bearer " 后面的部分，拿到纯 token     │
#   │ 4. 解密 token，取出里面的用户 ID 等信息         │
#   │ 5. 检查 token 类型是不是 "access"（访问令牌）   │
#   │ 6. 用用户 ID 去数据库查，确认这个用户真的存在    │
#   │ 7. 全部通过 → 返回 User 对象                   │
#   └───────────────────────────────────────────────┘
# =====================================================================

async def get_current_user(
    # Header(...) 表示从 HTTP 请求头中自动提取 "Authorization" 字段
    # ... 表示这是必填项，前端不传就报错
    # 前端发的请求必须带上这个头：Authorization: Bearer <token>
    # 注意：HTTP 头名称是大小写不敏感的，FastAPI 会自动把 authorization 转成 Authorization
    authorization: str = Header(..., description="Bearer <token>"),
    # 数据库连接，和之前一样，由 FastAPI 自动注入
    db: AsyncSession = Depends(get_db),
) -> User:  # -> User 表示这个函数的返回值类型是 User 对象

    # ========== 第一步：检查 Authorization 头的格式 ==========
    # 正确的格式必须是 "Bearer " 开头，比如 "Bearer eyJhbGci..."
    # 如果前端传的是 "Basic xxx" 或者根本没带 "Bearer "，说明格式不对
    # startswith("Bearer ") 注意 Bearer 后面有个空格！
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="无效的认证头")
        # 401 是 HTTP 状态码，意思是"未授权"（Unauthorized）
        # 前端收到 401 通常会跳转到登录页

    # ========== 第二步：从 Authorization 头中截取出纯 token ==========
    # authorization 的值是 "Bearer eyJhbGci..."，前 7 个字符是 "Bearer "（包括空格）
    # authorization[7:] 就是从第 8 个字符开始截取，去掉 "Bearer " 前缀，只留下真正的 token
    # 举例："Bearer abc123"[7:] → "abc123"
    token = authorization[7:]

    # ========== 第三步：解密 token，取出里面存的信息 ==========
    # decode_token 会用密钥把 JWT 字符串解密回一个字典（payload）
    # payload 大概长这样：{"sub": "用户ID", "type": "access", "exp": 过期时间}
    #   - "sub"（subject）：代表这个 token 是属于谁的，存的是用户 ID
    #   - "type"：token 类型，我们规定了 access 类型才能用来访问接口
    #   - "exp"：过期时间，过了这个时间 token 就失效了，需要重新登录
    # 如果 token 被篡改、过期、或者格式不对，decode_token 会抛出 JWTError 异常
    try:
        payload = decode_token(token)
    except JWTError:
        # JWTError 包含：token 过期、签名不匹配、格式错误等所有 JWT 相关的错误
        raise HTTPException(status_code=401, detail="无效或过期的 token")

    # ========== 第四步：检查 token 类型 ==========
    # 我们系统里有两种 token：
    #   - "access" token：用来访问接口的，有效期较短（比如 2 小时）
    #   - "refresh" token：用来刷新 access token 的，有效期较长（比如 7 天）
    # 访问接口只允许用 access token，防止有人拿 refresh token 来冒充
    # payload.get("type") 用 .get() 而不是 ["type"]，是因为如果 key 不存在，
    #   .get() 会返回 None（不会崩溃），而 ["type"] 会直接报 KeyError
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="需要 access token")

    # ========== 第五步：从 payload 中取出用户 ID ==========
    # payload["sub"] 取出来的值是一个字符串，比如 "a1b2c3d4-..."
    # uuid.UUID(...) 把字符串转成 UUID 对象，因为数据库里的 user_id 是 UUID 类型
    # 这里可能出两种错：
    #   - KeyError：payload 里根本没有 "sub" 这个字段（token 内容不完整）
    #   - ValueError："sub" 的值不是合法的 UUID 格式（比如 "abc" 就不能转成 UUID）
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        # (KeyError, ValueError) 表示同时捕获这两种异常，任意一种出现都报错
        raise HTTPException(status_code=401, detail="无效的 token")

    # ========== 第六步：去数据库查用户，确认用户真实存在 ==========
    # 为什么还要查数据库？光有用户 ID 还不够，因为：
    #   - 用户可能已经被删除了（管理员封号）
    #   - token 还没过期，但用户已经注销了
    # db.get(User, user_id) 就是 SQL 里的 SELECT * FROM user WHERE id = ? 
    # 如果查不到就返回 None
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    # ========== 全部验证通过，返回用户对象 ==========
    # 这个 User 对象会被传给调用这个依赖的接口，接口里就可以用 current_user.id、current_user.username 等属性
    return user

