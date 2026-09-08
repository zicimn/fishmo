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
            # 修复：bindparam 名称不能与列名相同（'id' 是 SQLAlchemy 2.0 保留名），改用 'gal_id'
            params.append({"gal_id": gal_id, "delta": delta})

        try:
            # 使用 Core 层表对象（Galgame.__table__）而非 ORM 类（Galgame），
            # 绕开 SQLAlchemy 2.0 的 "ORM Bulk UPDATE by Primary Key" 模式——
            # ORM 模式要求 params dict 必须包含主键列名 'id' 作为 key，
            # 但 bindparam 名称又不能与列名相同（'id' 是保留名），两个约束互相矛盾。
            # Core 层 UPDATE 只按 WHERE 子句定位行，不要求 params 包含主键 key，彻底规避冲突。
            table = Galgame.__table__
            stmt = (
                update(table)
                .where(table.c.id == bindparam('gal_id'))
                .values(views=table.c.views + bindparam('delta'))
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
        # 修复：updates 变量不存在，应使用 params
        print(f"成功同步 {len(params)} 篇文章的浏览量到数据库")