"""浏览量计数器：Redis 累积增量，定时任务批量回写数据库。"""

import logging

from sqlalchemy import bindparam, update
from sqlalchemy.ext.asyncio import AsyncSession

from config.cache import redis_client, redis_guard
from models import Article, Galgame

logger = logging.getLogger(__name__)


class _HashCounter:
    HASH_KEY = ""

    @classmethod
    async def incr(cls, target_id: int) -> int:
        value = await redis_guard(
            lambda: redis_client.hincrby(cls.HASH_KEY, str(target_id), 1),
            fallback=0,
            action=f"浏览量计数（{cls.HASH_KEY}）",
        )
        return int(value or 0)

    @classmethod
    async def get(cls, target_id: int) -> int:
        value = await redis_guard(
            lambda: redis_client.hget(cls.HASH_KEY, str(target_id)),
            fallback=None,
            action=f"读取浏览量（{cls.HASH_KEY}）",
        )
        try:
            return int(value) if value else 0
        except (TypeError, ValueError):
            return 0

    @classmethod
    async def get_total(cls, target_id: int, db_views: int) -> int:
        return (db_views or 0) + await cls.get(target_id)

    @classmethod
    async def remove(cls, target_id: int) -> None:
        await redis_guard(
            lambda: redis_client.hdel(cls.HASH_KEY, str(target_id)),
            action=f"清理浏览量（{cls.HASH_KEY}）",
        )

    @classmethod
    async def _pending(cls) -> dict[str, int]:
        raw = await redis_guard(
            lambda: redis_client.hgetall(cls.HASH_KEY),
            fallback={},
            action=f"读取浏览量增量（{cls.HASH_KEY}）",
        )
        return {key: int(value) for key, value in (raw or {}).items() if int(value) > 0}

    @classmethod
    async def _sync(cls, db: AsyncSession, table, id_param: str, label: str) -> None:
        pending = await cls._pending()
        if not pending:
            return

        params = [{"target_id": int(key), "delta": delta} for key, delta in pending.items()]
        try:
            stmt = (
                update(table)
                .where(table.c.id == bindparam("target_id"))
                .values(views=table.c.views + bindparam("delta"))
            )
            await db.execute(stmt, params, execution_options={"synchronize_session": False})
            await db.commit()
        except Exception:  # noqa: BLE001
            logger.exception("同步%s浏览量到数据库失败", label)
            return  # 失败保留 Redis 增量，等待下次重试

        # 只删除已同步的字段，避免同步期间新增的计数被误删
        await redis_guard(
            lambda: redis_client.hdel(cls.HASH_KEY, *pending.keys()),
            action=f"清理已同步浏览量（{cls.HASH_KEY}）",
        )
        logger.info("成功同步 %d 个%s的浏览量", len(params), label)


class ViewCounter(_HashCounter):
    HASH_KEY = "gal_views"

    @classmethod
    async def sync_to_db(cls, db: AsyncSession) -> None:
        await cls._sync(db, Galgame.__table__, "target_id", "游戏")


class ArticleViewCounter(_HashCounter):
    HASH_KEY = "article_views"

    @classmethod
    async def sync_to_db(cls, db: AsyncSession) -> None:
        await cls._sync(db, Article.__table__, "target_id", "文章")