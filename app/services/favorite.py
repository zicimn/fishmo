"""游戏收藏。"""

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.cache import (
    GAL_VERSION_KEY,
    delete_cache_pattern,
    update_version,
)
from models import Favorite, Galgame, User
from utils.responsed import Conflict, NotFound, info


class FavoriteService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def Add(self, user_id: int, gal_id: int) -> dict:
        game = await self.db.get(Galgame, gal_id)
        if not game:
            raise NotFound("游戏不存在")

        favorite = Favorite(user_id=user_id, gal_id=gal_id)
        self.db.add(favorite)
        try:
            await self.db.flush()
            await self.db.execute(
                update(Galgame)
                .where(Galgame.id == gal_id)
                .values(favorite=Galgame.favorite + 1)
            )
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise Conflict("已收藏该游戏")

        await self.db.refresh(favorite)
        await self._invalidate(gal_id)
        return info("收藏成功", data={"favorite_id": favorite.id})

    async def Remove(self, user_id: int, gal_id: int) -> dict:
        favorite = (
            await self.db.execute(
                select(Favorite).where(
                    Favorite.user_id == user_id, Favorite.gal_id == gal_id
                )
            )
        ).scalar_one_or_none()
        if not favorite:
            raise NotFound("尚未收藏该游戏")

        await self.db.delete(favorite)
        await self.db.execute(
            update(Galgame)
            .where(Galgame.id == gal_id, Galgame.favorite > 0)
            .values(favorite=Galgame.favorite - 1)
        )
        await self.db.commit()
        await self._invalidate(gal_id)
        return info("已取消收藏", data={"gal_id": gal_id})

    async def Status(self, gal_id: int, viewer: User | None) -> dict:
        game = await self.db.get(Galgame, gal_id)
        if not game:
            raise NotFound("游戏不存在")

        favorite_id = None
        if viewer:
            favorite_id = (
                await self.db.execute(
                    select(Favorite.id).where(
                        Favorite.user_id == viewer.id, Favorite.gal_id == gal_id
                    )
                )
            ).scalar_one_or_none()

        return info(
            "查询成功",
            data={
                "gal_id": gal_id,
                "favorited": favorite_id is not None,
                "favorite_id": favorite_id,
                "count": game.favorite or 0,
            },
        )

    async def GetList(self, user_id: int, page: int, size: int) -> dict:
        filters = [Favorite.user_id == user_id]
        rows = (
            await self.db.execute(
                select(
                    Galgame.id,
                    Galgame.name,
                    Galgame.cover,
                    Galgame.views,
                    Galgame.category,
                    Favorite.created_at,
                )
                .join(Favorite, Favorite.gal_id == Galgame.id)
                .where(*filters)
                .order_by(Favorite.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).all()
        total = (
            await self.db.execute(
                select(func.count(Favorite.id)).select_from(Favorite).where(*filters)
            )
        ).scalar() or 0

        items = [
            {
                "id": row.id,
                "name": row.name,
                "cover": row.cover,
                "views": row.views or 0,
                "category": row.category,
                "favorited_at": row.created_at,
            }
            for row in rows
        ]
        return info("查询成功", data={"total": int(total), "items": items})

    async def DeleteByGal(self, gal_id: int) -> None:
        await self.db.execute(delete(Favorite).where(Favorite.gal_id == gal_id))

    async def _invalidate(self, gal_id: int) -> None:
        await delete_cache_pattern("Galgame:*")
        await delete_cache_pattern(f"Gal_visit:*id={gal_id}")
        await update_version(GAL_VERSION_KEY)