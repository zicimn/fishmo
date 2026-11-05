"""游戏全文搜索（名称 / 标签 / 公司）。"""

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.cache import (
    GAL_VERSION_KEY,
    get_cache_key,
    get_from_cache,
    get_version,
    set_to_cache,
)
from models import Galgame, User
from schemas.galgame import to_gal_item
from utils.responsed import info

SEARCH_TYPES = {"name", "tag", "company"}


def _like_pattern(keyword: str) -> str:
    escaped = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def Search(
        self,
        keyword: str,
        search_type: str,
        page: int,
        size: int,
    ) -> dict:
        if search_type not in SEARCH_TYPES:
            search_type = "name"

        version = await get_version(GAL_VERSION_KEY)
        cache_key = get_cache_key(
            "Search",
            keyword=keyword,
            search_type=search_type,
            page=page,
            size=size,
            version=version,
        )
        cached = await get_from_cache(cache_key)
        if cached:
            return info("查询成功", data=cached)

        pattern = _like_pattern(keyword.strip())
        filters = [Galgame.status.is_(True)]

        if search_type == "tag":
            filters.append(cast(Galgame.tag, String).ilike(pattern))
        elif search_type == "company":
            filters.append(cast(Galgame.company, String).ilike(pattern))
        else:
            filters.append(
                or_(
                    Galgame.cn_name.ilike(pattern),
                    Galgame.jp_name.ilike(pattern),
                    Galgame.en_name.ilike(pattern),
                )
            )

        rows = (
            await self.db.execute(
                select(
                    Galgame.id,
                    Galgame.author_id,
                    Galgame.name,
                    Galgame.cover,
                    Galgame.views,
                    Galgame.category,
                    Galgame.updated_at,
                    Galgame.status,
                    User.username,
                    User.avatar,
                )
                .join(User, User.id == Galgame.author_id)
                .where(*filters)
                .order_by(Galgame.updated_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).all()
        total = (
            await self.db.execute(
                select(func.count(Galgame.id)).select_from(Galgame).where(*filters)
            )
        ).scalar() or 0

        items = [
            to_gal_item(
                gal_id=row.id,
                name=row.name,
                cover=row.cover,
                views=row.views,
                category=row.category,
                updated_at=row.updated_at,
                status=row.status,
                author_id=row.author_id,
                author_name=row.username,
                author_avatar=row.avatar,
            )
            for row in rows
        ]
        data = {"total": int(total), "items": items}
        await set_to_cache(cache_key, data)
        return info("查询成功", data=data)