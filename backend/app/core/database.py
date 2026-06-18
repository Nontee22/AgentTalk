from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# =====================================================================
# 本文件功能：初始化数据库连接，是整个应用的"数据库基础设施"
#
# 用到的技术栈：
#   - SQLAlchemy：Python 最流行的 ORM（对象关系映射）
#     简单说：不用写 SQL，用 Python 对象来操作数据库
#     比如 session.get(User, 1) 等价于 SELECT * FROM user WHERE id = 1
#
#   - asyncpg：PostgreSQL 的异步驱动（让数据库操作不阻塞）
#     在 settings.database_url 里会指定，比如 postgresql+asyncpg://...
#     其中的 "+asyncpg" 就是告诉 SQLAlchemy 要用 asyncpg 作为底层驱动
#
#   - Redis：内存数据库，速度极快，这里用来做缓存和状态管理
#
# 整体结构：
#   ┌───────────────────────────────────────────┐
#   │ engine        ─ 连接池，管理和数据库的连接   │
#   │ session_maker ─ 会话工厂，每次创建一个会话   │
#   │ get_db()      ─ 依赖注入，接口里用它获取会话  │
#   │ Base          ─ 所有数据表模型的“父类”     │
#   │ redis_client  ─ Redis 客户端连接          │
#   └───────────────────────────────────────────┘
# =====================================================================

# ==================== 第一步：创建数据库引擎（连接池） ====================
# engine 可以理解为"连接池管理器"
# 为什么要用连接池？
#   - 每次连接数据库是一个很耗时的操作（要建立 TCP 连接、验证用户名密码等）
#   - 连接池会提前创建好一堆连接，用的时候直接拿，用完放回来，而不是每次都新建
#   - 就像共享单车：不用每次出门都买一辆新车，用完就丢
# settings.database_url 从 .env 文件读取，格式如：
#   postgresql+asyncpg://用户名:密码@数据库地址:端口/数据库名
# echo=False 表示不把执行的 SQL 语句打印到控制台（设为 True 可以看到生成的 SQL，调试时有用）
engine = create_async_engine(settings.database_url, echo=False)

# ==================== 第二步：创建会话工厂 ====================
# async_sessionmaker 是一个"工厂"，用来生产 AsyncSession（异步会话）对象
# 什么是 AsyncSession？
#   可以把它理解成"一次数据库对话"
#   在一次对话里，你可以查数据、改数据、插入数据，
#   最后统一 commit（提交） 或者 rollback（回滚）
#   就像一个购物车：你往里面加商品（增删改），最后结账（commit）才真正生效
#
# 参数解释：
#   - engine：告诉工厂用哪个连接池来创建会话
#   - class_=AsyncSession：创建的会话类型是异步的（支持 async/await）
#   - expire_on_commit=False：默认情况下，commit 后对象里的数据会"过期"，下次访问会重新查数据库
#     设为 False 表示 commit 后数据仍然可以用，不用再查一次，更方便
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ==================== 第三步：定义模型基类 ====================
# Base 是所有数据库表模型的"父类"（模板）
# 以后定义 User、Character 等表时，都要继承这个 Base：
#   class User(Base):
#       __tablename__ = "user"
#       id = Column(...)
#       name = Column(...)
# Base 会自动把这些子类收集起来，让 SQLAlchemy 知道有哪些表，
# 也方便后续做数据迁移（Alembic 会根据 Base 的所有子类来生成迁移脚本）
class Base(DeclarativeBase):
    pass


# ==================== 第四步：数据库会话依赖注入函数 ====================
# 这个函数会用在 FastAPI 接口的 Depends() 里，比如：
#   db: AsyncSession = Depends(get_db)
# 每次有请求来时，FastAPI 会自动调用 get_db，拿到一个 db 对象传给接口
# 请求结束后，会自动关闭这个 session（通过 async with 自动管理）
#
# 为什么用 yield 而不是 return？
#   - yield 前面（async with...）是"请求来时执行"：创建数据库会话
#   - yield 后面（async with 结束时）是"请求结束后执行"：自动关闭会话
#   - 这样就不用担心忘记关闭连接，导致连接池耗尽
#   - 这种写法叫"上下文管理器生成器"，FastAPI 专门为这种模式做了支持
#
# -> AsyncGenerator[AsyncSession, None] 是类型提示：
#   表示这是一个异步生成器，yield 出来的值是 AsyncSession 类型，没有返回值（None）
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # async with 会自动管理会话的生命周期：
    # - 进入 with：创建一个新的数据库会话（从连接池拿一个连接）
    # - 退出 with：自动关闭会话（把连接还给连接池）
    # 即使中途出了异常，也会保证连接被正确释放，不会泄漏
    async with async_session_maker() as session:
        yield session  # 把 session 交给接口使用


# ==================== 第五步：创建 Redis 客户端 ====================
# Redis 和 PostgreSQL 的区别：
#   - PostgreSQL：数据存在硬盘上，适合存持久化数据（用户信息、聊天记录等）
#   - Redis：数据存在内存里，速度极快（微秒级），适合存临时数据
#
# 本项目里 Redis 用来做什么？
#   - 健康检查：检查 Redis 服务是否正常运行
#   - 会话缓存：把频繁访问的数据缓存到内存，减少数据库查询
#   - 限流：限制用户请求频率（比如每分钟最多发 10 条消息），多 worker 时共享计数
#   - 流式取消：发布/订阅模式，多 worker 之间同步"取消生成"的信号
#
# 参数解释：
#   - settings.redis_url：从 .env 读取，格式如 redis://localhost:6379/0
#     最后的 /0 表示使用 Redis 的第 0 号数据库（Redis 默认有 16 个数据库，编号 0-15）
#   - decode_responses=True：Redis 返回的数据默认是 bytes 类型（如 b'hello'）
#     设为 True 后会自动解码成 Python 字符串（如 'hello'），用起来更方便
redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
