from fastapi import APIRouter, Depends, Query
from config.db import get_db
from config.cache import (
    get_search_version, get_cache_key, get_from_cache, set_to_cache,
    GAL_VERSION_KEY,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String, or_
from model.galgame import Galgame
from model.user import User
from schemas.galgame import GalItem, GalList
from typing import Optional

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("/", response_model=GalList)
async def search(
    keyword: str = Query(..., min_length=1),
    search_type: Optional[str] = "name",
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    db: AsyncSession = Depends(get_db),
):
    cache_key = get_cache_key(
        "Search", 
        keyword=keyword, search_type=search_type,
        page=page, size=size
    )

    cache_data = await get_from_cache(cache_key)
    if cache_data:
        return cache_data

    skip = (page - 1) * size

    escaped_kw = keyword.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    like_pattern = f"%{escaped_kw}%"

    # 过滤条件：仅返回已公开的作品
    filters = [Galgame.status == True]

    # 名称匹配统一用三语言列（cn/en/jp），而非派生的 name 字段
    name_filter = or_(
        Galgame.cn_name.ilike(like_pattern),
        Galgame.jp_name.ilike(like_pattern),
        Galgame.en_name.ilike(like_pattern),
    )

    if search_type == "tag":
        # JSON 列需 cast 到 String 才能使用 ilike
        filters.append(cast(Galgame.tag, String).ilike(like_pattern))
    elif search_type == "company":
        filters.append(cast(Galgame.company, String).ilike(like_pattern))
    elif search_type == "name":
        filters.append(name_filter)
    

    stmt = (
        select(
            Galgame.id, Galgame.author_id, Galgame.name, Galgame.cover,
            Galgame.views, User.username, User.avatar,
        )
        .join(Galgame.author)
        .where(*filters)
        .offset(skip)
        .limit(size)
        .order_by(Galgame.updated_at.desc())
    )

    result = await db.execute(stmt)

    # 总数统计复用同一组 WHERE
    cnt = await db.execute(
        select(func.count(Galgame.id)).select_from(Galgame).where(*filters)
    )
    rows = result.all()
    total = cnt.scalar() or 0

    items = []
    for id, author_id, name, cover, views, author, avatar in rows:
        items.append(
            GalItem(
                id=id,
                name=name,
                cover=cover,
                views=views,
                author=author,
                avatar=avatar,
                author_id=author_id,
            )
        )

    data = GalList(total=total, items=items)

    await set_to_cache(cache_key, data.model_dump())

    return data
