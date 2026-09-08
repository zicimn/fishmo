from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from model.favorite import Favorite
from config.db import get_db
from config.cache import update_version, GAL_VERSION_KEY
from model.user import User
from model.galgame import Galgame
from utils.verify_user import verify_login
from schemas.galgame import GalBase, GalBaseList

router = APIRouter(prefix="/api/v1/favorite", tags=["favorite"])
# W1: 添加 auto_error=False，与项目其他路由保持一致
security = HTTPBearer(auto_error=False)


# C3: GET → POST（写操作不应使用 GET）
@router.post("/add")
async def add_favorite(
    gal_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    # C6: 校验游戏是否存在
    game = await db.get(Galgame, gal_id)
    if not game:
        raise HTTPException(status_code=404, detail="游戏不存在")

    favorite = Favorite(
        user_id=user_id,
        gal_id=gal_id
    )
    db.add(favorite)
    try:
        await db.commit()
    except IntegrityError:
        # C5: 唯一约束冲突 → 已收藏
        await db.rollback()
        raise HTTPException(status_code=409, detail="已收藏")

    await db.refresh(favorite)

    # W3: 收藏数 +1（Core UPDATE 避免 ORM 批量问题）
    table = Galgame.__table__
    await db.execute(
        update(table).where(table.c.id == gal_id).values(favorite=table.c.favorite + 1)
    )
    await db.commit()

    # W4: 增删改后使缓存版本失效
    await update_version(GAL_VERSION_KEY)

    return {"message": "收藏成功", "favorite_id": favorite.id}


# C3: GET → DELETE（写操作不应使用 GET）
@router.delete("/remove")
async def remove_favorite(
    gal_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    # C2: db.get() 不支持 dict 查单列 PK，改用 select 查询
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.gal_id == gal_id)
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        raise HTTPException(status_code=404, detail="收藏不存在")

    await db.delete(favorite)
    await db.commit()

    # W3: 收藏数 -1（不低于 0）
    table = Galgame.__table__
    await db.execute(
        update(table).where(
            table.c.id == gal_id,
            table.c.favorite > 0
        ).values(favorite=table.c.favorite - 1)
    )
    await db.commit()

    # W4: 增删改后使缓存版本失效
    await update_version(GAL_VERSION_KEY)

    return {"message": "取消收藏成功"}


@router.get("/visit")
async def visit(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    favorite = await db.get(Favorite, id)
    if not favorite:
        raise HTTPException(status_code=404, detail="收藏不存在")
    return {"message": "访问成功", "gal_id": favorite.gal_id}


@router.get("/list", response_model=GalBaseList)
async def flist(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    # W6: fitter → filters
    filters = [Favorite.user_id == user_id]
    skip = (page - 1) * size

    # W2: 查询总数
    count_stmt = (
        select(func.count())
        .select_from(Favorite)
        .where(*filters)
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    stmt = (
        select(Galgame.id, Galgame.cn_name, Galgame.en_name, Galgame.jp_name, Galgame.cover)
        .join(Favorite, Favorite.gal_id == Galgame.id)
        .where(*filters)
        .offset(skip)
        .limit(size)
    )

    result = await db.execute(stmt)
    rows = result.all()
    items = []

    # W2: GalBase 增加 id 字段，支持前端跳转
    for gid, cn, en, jp, cover in rows:
        name = cn or en or jp
        items.append(GalBase(id=gid, name=name, cover=cover))

    data = GalBaseList(
        total=total,
        items=items
    )

    return data
