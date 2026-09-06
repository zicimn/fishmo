from sqlalchemy import update, bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from config import redis_client
from model import Galgame


class ViewCounter:
    HASH_KEY = "gal_views"

    @classmethod
    async def incr(cls, gal_id: int) -> int:
        return await redis_client.hincrby(cls.HASH_KEY, str(gal_id), 1)

    @classmethod
    async def get(cls, gal_id: int) -> int:
        val = await redis_client.hget(cls.HASH_KEY, str(gal_id))
        return int(val) if val else 0

    @classmethod
    async def get_total(cls, gal_id: int, db_views: int) -> int:
        delta = await cls.get(gal_id)   # 必须加 await
        return db_views + delta

    @classmethod
    async def sync_to_db(cls, db: AsyncSession):
        all_delta = await redis_client.hgetall(cls.HASH_KEY)
        if not all_delta:
            return

        params = []
        for gal_id_bytes, delta_bytes in all_delta.items():
            gal_id = int(gal_id_bytes)
            delta = int(delta_bytes)
            params.append({"id": gal_id, "delta": delta})

        try:
            # params = [{"gal_id": u["gal_id"], "delta": u["delta"]} for u in updates]
            stmt = (
                update(Galgame)
                .values(views=Galgame.views + bindparam('delta'))
                # 必须显式指定目标行，否则不带 WHERE 的 UPDATE 在未命中 ORM 主键推断
                # 时会退化为逐条更新全表，污染所有游戏的浏览量
                .where(Galgame.id == bindparam('id'))
            )
            await db.execute(
                stmt, 
                params,
                execution_options={"synchronize_session": False}
                )
            await db.commit()
        except Exception as e:
            print(f"同步数据库失败: {e}")
            # 失败不删除 Redis，保留增量等待下次重试
            return

        await redis_client.delete(cls.HASH_KEY)
        print(f"成功同步 {len(updates)} 篇文章的浏览量到数据库")