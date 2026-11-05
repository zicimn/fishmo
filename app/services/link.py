"""游戏资源链接。"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.cache import (
    LINK_VERSION_KEY,
    delete_cache_pattern,
    get_cache_key,
    get_from_cache,
    get_version,
    set_to_cache,
    update_version,
)
from models import Galgame, Link, SizeUnitEnum
from schemas.link import AddLink, EditLink, to_link_item
from utils.responsed import Forbidden, NotFound, info


class LinkService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def GetByGame(self, game_id: int, page: int, size: int) -> dict:
        game = await self.db.get(Galgame, game_id)
        if not game:
            raise NotFound("未找到该游戏")

        version = await get_version(LINK_VERSION_KEY)
        cache_key = get_cache_key(
            "links", game_id=game_id, page=page, size=size, version=version
        )
        cached = await get_from_cache(cache_key)
        if cached:
            return info("查询成功", data=cached)

        filters = [Link.game_id == game_id, Link.status.is_(True)]
        rows = (
            await self.db.execute(
                select(Link)
                .where(*filters)
                .order_by(Link.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()
        total = (
            await self.db.execute(
                select(func.count(Link.id)).select_from(Link).where(*filters)
            )
        ).scalar() or 0

        data = {
            "total": int(total),
            "items": [to_link_item(link, author=link.author) for link in rows],
        }
        await set_to_cache(cache_key, data)
        return info("查询成功", data=data)

    async def GetByUser(self, user_id: int, page: int, size: int) -> dict:
        version = await get_version(LINK_VERSION_KEY)
        cache_key = get_cache_key(
            "links_user", user_id=user_id, page=page, size=size, version=version
        )
        cached = await get_from_cache(cache_key)
        if cached:
            return info("查询成功", data=cached)

        filters = [Link.author_id == user_id, Link.status.is_(True)]
        rows = (
            await self.db.execute(
                select(Link)
                .where(*filters)
                .order_by(Link.updated_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()
        total = (
            await self.db.execute(
                select(func.count(Link.id)).select_from(Link).where(*filters)
            )
        ).scalar() or 0

        data = {
            "total": int(total),
            "items": [to_link_item(link, author=link.author) for link in rows],
        }
        await set_to_cache(cache_key, data)
        return info("查询成功", data=data)

    async def Add(self, user_id: int, game_id: int, data: AddLink) -> dict:
        game = await self.db.get(Galgame, game_id)
        if not game:
            raise NotFound("未找到该游戏")

        link = Link(
            url=data.url,
            content=(data.content or "").strip() or None,
            code=(data.code or "").strip() or None,
            author_id=user_id,
            game_id=game_id,
            category=(data.category or "").strip() or None,
            size=data.size,
            size_unit=SizeUnitEnum(data.size_unit) if data.size_unit else None,
            status=True,  # 新增即公开
        )
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        await self._invalidate()
        return info("链接已添加", data={"id": link.id})

    async def Update(self, user_id: int, link_id: int, data: EditLink) -> dict:
        link = await self._get_owned(user_id, link_id)
        fields = data.model_fields_set

        if "content" in fields:
            link.content = (data.content or "").strip() or None
        if "code" in fields:
            link.code = (data.code or "").strip() or None
        if "category" in fields:
            link.category = (data.category or "").strip() or None
        if "size" in fields:
            link.size = data.size
        if "size_unit" in fields:
            link.size_unit = SizeUnitEnum(data.size_unit) if data.size_unit else None

        await self.db.commit()
        await self._invalidate()
        return info("链接已更新", data={"id": link_id})

    async def Delete(self, user_id: int, link_id: int) -> dict:
        link = await self._get_owned(user_id, link_id)
        await self.db.delete(link)
        await self.db.commit()
        await self._invalidate()
        return info("链接已删除", data={"id": link_id})

    async def _get_owned(self, user_id: int, link_id: int) -> Link:
        link = (
            await self.db.execute(
                select(Link).where(Link.id == link_id, Link.author_id == user_id)
            )
        ).scalar_one_or_none()
        if not link:
            raise Forbidden("没有该链接，或您不是发布者")
        return link

    async def _invalidate(self) -> None:
        await delete_cache_pattern("links:*")
        await delete_cache_pattern("links_user:*")
        await update_version(LINK_VERSION_KEY)