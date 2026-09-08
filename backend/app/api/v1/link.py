from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.db import get_db
from config.cache import (
    get_search_version, get_cache_key, get_from_cache, set_to_cache,
    delete_cache_pattern, update_version, LINK_VERSION_KEY,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from model.galgame import Galgame
from model.user import User
from model.link import Link
from model.enums import SizeUnitEnum
from typing import Optional
from utils.verify_user import verify_login
from schemas.link import LinkList, LinkItems, LinkItem, AddLink, EditLink
from schemas.user import UserInfo

router = APIRouter(prefix="/api/v1/link", tags=["link"])
security = HTTPBearer(auto_error=False)


@router.get("/user/{user_id}", response_model=LinkList)
async def get_list_by_user(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """按用户 id 获取其发布的链接列表（分页，按更新时间倒序，用于个人主页/我的链接管理）。"""
    version = await get_search_version(LINK_VERSION_KEY)
    cache_key = get_cache_key("links_user", user_id=user_id, page=page, size=size, version=version)
    cache_data = await get_from_cache(cache_key)

    if cache_data:
        return cache_data

    skip = (page - 1) * size

    # 公开的个人主页链接列表：仅展示公开链接（与 /link/{game_id} 口径一致）。
    # 该端点无鉴权、可传任意 user_id，若不过滤 status，未来一旦出现非公开链接，
    # 就会造成水平越权泄漏任意作者的私链，故这里不做“作者可见全部”语义。
    filters = [Link.author_id == user_id, Link.status == True]

    query = await db.execute(
        select(Link, User.username, User.avatar)
        .join(Link.author)
        .where(*filters)
        .order_by(Link.updated_at.desc())
        .offset(skip)
        .limit(size)
    )

    rows = query.all()

    cnt = await db.execute(
        select(func.count(Link.id)).select_from(Link).where(*filters)
    )
    total = cnt.scalar() or 0

    items = []
    for result, username, avatar in rows:
        item = LinkItem(
            id=result.id,
            url=result.url,
            content=result.content,
            code=result.code,
            category=result.category,
            size=result.size,
            size_unit=result.size_unit.value if result.size_unit else None,
            status=result.status,
            game_id=result.game_id,
        )
        account = UserInfo(
            username=username,
            avatar=avatar
        )
        items.append(
            LinkItems(
                item=item,
                account=account
            )
        )

    data = LinkList(
        total=total,
        items=items
    )

    await set_to_cache(cache_key, data.model_dump())

    return data


@router.get("/{game_id}", response_model=LinkList)
async def get_list(
    game_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    # 列表缓存 key 带 version，与增删改时的 update_version() 失效机制保持一致
    version = await get_search_version(LINK_VERSION_KEY)
    cache_key = get_cache_key("links", game_id=game_id, page=page, size=size, version=version)
    cache_data = await get_from_cache(cache_key)

    if cache_data:
        return cache_data

    # 先校验游戏存在，避免对不存在的游戏返回空列表
    # db.get() 优先走 identity map，纯主键查询更高效
    existing = await db.get(Galgame, game_id)
    if not existing:
        raise HTTPException(status_code=404, detail="未找到该游戏")

    skip = (page - 1) * size

    # 过滤条件集中管理：列表查询与总数统计共用同一组 WHERE，保证两者口径一致
    filters = [Link.game_id == game_id, Link.status == True]  # 仅展示公开链接

    query = await db.execute(
        select(Link, User.username, User.avatar)
        .join(Link.author)
        .where(*filters)
        .offset(skip)
        .limit(size)
    )

    rows = query.all()

    # 总数统计复用同一组 WHERE（不带 offset/limit），返回真实总条数而非页数
    cnt = await db.execute(
        select(func.count(Link.id)).select_from(Link).where(*filters)
    )
    total = cnt.scalar() or 0

    items = []
    for result, username, avatar in rows:
        item = LinkItem(
            id=result.id,
            url=result.url,
            content=result.content,
            code=result.code,
            category=result.category,
            size=result.size,
            size_unit=result.size_unit.value if result.size_unit else None,
            status=result.status,
            game_id=result.game_id,
        )
        account = UserInfo(
            username=username,
            avatar=avatar
        )
        items.append(
            LinkItems(
                item=item,
                account=account
            )
        )

    data = LinkList(
        total=total,
        items=items
    )

    await set_to_cache(cache_key, data.model_dump())

    return data


@router.post("/add")
async def add(
    game_id: int,
    data: AddLink,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    # 无条件校验游戏存在，不与详情视图缓存命中耦合（避免缓存未命中时漏校验）
    # db.get() 优先走 identity map，纯主键查询更高效
    game = await db.get(Galgame, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="未找到该游戏")

    # size_unit 字符串转枚举：空值保持 None，非空转为 SizeUnitEnum 实例
    size_unit_val = SizeUnitEnum(data.size_unit) if data.size_unit else None

    new_link = Link(
        url=data.url,
        content=data.content,
        code=data.code,
        author_id=user_id,
        game_id=game_id,
        category=data.category,
        size=data.size,
        size_unit=size_unit_val,
        status=True  # 新增即公开，后续可由 control 路由管理
    )

    db.add(new_link)
    await db.commit()
    await db.refresh(new_link)

    await delete_cache_pattern("links:*")
    await delete_cache_pattern("links_user:*")
    await update_version(LINK_VERSION_KEY)

    return {
        "msg": "添加成功",
        "id": new_link.id
    }


@router.put("/review")
async def review(
    link_id: int,
    data: EditLink,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = verify_login(credentials=credentials)

    query = await db.execute(
        select(Link).where(Link.id == link_id).where(Link.author_id == user_id)
    )
    result = query.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=403, detail="没有该链接或者您不是发布者")

    # 全部使用 is not None 判断：仅当客户端显式传值时才更新，允许将字段清空为 None
    if data.category is not None:
        result.category = data.category

    if data.code is not None:
        result.code = data.code

    if data.content is not None:
        result.content = data.content

    if data.size is not None:
        result.size = data.size

    if data.size_unit is not None:
        result.size_unit = SizeUnitEnum(data.size_unit)

    await db.commit()

    await delete_cache_pattern("links:*")
    await delete_cache_pattern("links_user:*")
    await update_version(LINK_VERSION_KEY)

    return {
        "msg": "编辑成功",
        "id": link_id,
        "user_id": user_id
    }


@router.delete("/delete")
async def delete(
    link_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    result = await db.execute(
        select(Link).where(Link.id == link_id).where(Link.author_id == user_id)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=403, detail="没有该链接或者您不是发布者")

    await db.delete(link)
    try:
        await db.commit()
    except IntegrityError:
        # 外键约束等完整性错误统一兜底为 400，避免未捕获异常导致 500
        await db.rollback()
        raise HTTPException(status_code=400, detail="无法删除")

    # 删除后使相关缓存失效：版本号 +1 + 主动清理列表 key
    await delete_cache_pattern("links:*")
    await delete_cache_pattern("links_user:*")
    await update_version(LINK_VERSION_KEY)

    return {
        "msg": "链接已删除",
        "id": link_id,
        "user_id": user_id
    }
