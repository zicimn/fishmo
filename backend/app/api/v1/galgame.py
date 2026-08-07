from fastapi import APIRouter,Depends,HTTPException
from config.db import get_db
from config.cache import get_search_version,get_cache_key,get_from_cache,set_to_cache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from model.galgame import Galgame
from schemas.galgame import GalItem,GalList,PlatformEnum
from typing import Optional


router = APIRouter("/api/v1/galgame")


@router.get("/",response_model=GalList)
async def index(
    category:Optional[str],
    platform:Optional[PlatformEnum],
    page:int = 1,
    size:int = 10,
    db:AsyncSession = Depends(get_db),
):
    version = get_search_version()
    cache_key = get_cache_key("Galgame",page = page,size = size,category = category,platform = platform,version = version)

    cache_data = get_from_cache(cache_key)
    if cache_data:
        return cache_data

    skip = (page - 1) * size
    stmt =  (
        select(Galgame.cn_name,Galgame.jp_name,Galgame.en_name,Galgame.cover)
        .offset(skip)
        .limit(size)
    )

    if category:#有作品类型选择
        stmt.where(Galgame.category == category)

    if platform:#有选择平台
        stmt.where(Galgame.platfrom.contains([platform]))

    result = await db.execute(stmt)

    cnt = await db.execute(select(func.count(Galgame.id)).select_from(Galgame))
    rows = result.all()
    total = cnt.scalar() or 0

    items = []

    for cn,jp,en,cover in rows:
        name = cn or jp or en or "undefind"
        items.append(
            GalItem(
                name = name,
                cover = cover
            )
        )

    data = GalList(
        total = (total + size - 1) // size,
        items=items
    )

    await set_to_cache(cache_key,data.model_dump())

    return data

