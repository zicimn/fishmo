from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from config.security import ASYNC_DATABASE_URL, DB_ECHO

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=DB_ECHO,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # 1 小时回收，避免 MySQL 主动断开空闲连接
    pool_timeout=30,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


async def get_db():
    """请求级会话。

    只读请求不产生写操作时不会提交；服务层对增删改显式 ``commit()``，
    这里再做一次兜底提交（防止个别服务漏写 commit 导致静默丢失）。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            if session.new or session.dirty or session.deleted:
                await session.commit()
        except Exception:
            await session.rollback()
            raise