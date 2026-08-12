from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.db import get_db
from config.cache import (
    get_search_version, get_cache_key, get_from_cache, set_to_cache,
    redis_client, delete_cache_pattern, delete_cache, update_version,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update
from model.galgame import Galgame
from model.user import User
from schemas.galgame import GalItem, GalList, PlatformEnum, AddGal, EditGal
from typing import Optional
from utils.verify_user import verify_login
from utils.webp import upload_image_to_cloudinary, upload_images_to_cloudinary

router = APIRouter(prefix="/api/v1/galgame", tags=["gal"])
security = HTTPBearer(auto_error=False)

# 浏览量计数：Redis key 的 TTL（秒），与响应缓存解耦——即使响应命中缓存，计数也不中断
VIEWS_REDIS_TTL = 24 * 60 * 60
# 浏览量落库批大小：Redis 计数每累计满该值，用 SQL 原子自增刷入数据库并重置计数窗口
VIEWS_FLUSH_BATCH = 10


@router.get("/", response_model=GalList)
async def index(
    category: Optional[str] = None,
    platform: Optional[PlatformEnum] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    version = await get_search_version()
    cache_key = get_cache_key("Galgame", page=page, size=size, category=category, platform=platform, version=version)

    cache_data = await get_from_cache(cache_key)
    if cache_data:
        return cache_data

    skip = (page - 1) * size
    # 过滤条件集中管理：列表查询与总数统计共用同一组 WHERE，保证两者口径一致
    filters = [Galgame.status == True]  # 可见状态
    if category:  # 有作品类型选择
        filters.append(Galgame.category == category)
    if platform:  # 有选择平台
        filters.append(Galgame.platfrom.contains([platform]))

    stmt = (
        select(Galgame.cn_name, Galgame.jp_name, Galgame.en_name, Galgame.cover, Galgame.views, User.username, User.avatar)
        .join(Galgame.author)
        .where(*filters)
        .offset(skip)
        .limit(size)
        .order_by(Galgame.updated_at)
    )

    result = await db.execute(stmt)

    # 总数统计复用同一组 WHERE（不带 offset/limit），返回真实总条数而非页数
    cnt = await db.execute(
        select(func.count(Galgame.id)).select_from(Galgame).where(*filters)
    )
    rows = result.all()
    total = cnt.scalar() or 0

    items = []

    for cn, jp, en, cover, views, author, avatar in rows:
        name = cn or jp or en or "undefind"
        items.append(
            GalItem(
                name=name,
                cover=cover,
                views=views,
                author=author,
                avatar=avatar,
            )
        )

    data = GalList(
        total=total,
        items=items
    )

    await set_to_cache(cache_key, data.model_dump())

    return data


@router.get("/{id}")
async def visit(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    version = await get_search_version()
    cache_key = get_cache_key("Gal_visit", id=id, version=version)
    cache_data = await get_from_cache(cache_key)

    # 浏览量计数与响应缓存解耦：无论缓存是否命中都必须执行 Redis INCR，
    # 否则缓存命中时浏览量会漏计。key 带 TTL，防止永久驻留。
    redis_key = f"gal_views:{id}"
    delta = await redis_client.incr(redis_key)
    if delta == 1:
        # 新计数窗口：设置 TTL
        await redis_client.expire(redis_key, VIEWS_REDIS_TTL)

    # 阈值批量落库：用 SQL 原子自增（views = views + delta）替代"读-改-写"，
    # 避免并发下 result.views + delta 的读-改-写丢更新。落库后重置计数窗口。
    # flush_hit 标记本次请求是否触发了落库：若触发，Redis 计数已并入 DB，
    # 后续展示浏览量时不能再叠加 delta，否则会重复计数。
    flush_hit = delta % VIEWS_FLUSH_BATCH == 0
    if flush_hit:
        await db.execute(
            update(Galgame)
            .where(Galgame.id == id)
            .values(views=Galgame.views + delta)
        )
        await db.commit()
        await redis_client.delete(redis_key)

    if cache_data:
        # 缓存命中：计数已在上面完成，直接返回缓存内容（views 滞后最长一个缓存周期，可接受）
        return cache_data

    query = await db.execute(
        select(Galgame, User.username, User.avatar).join(Galgame.author).where(Galgame.id == id)
    )
    row = query.first()

    if not row:
        raise HTTPException(status_code=404, detail="未找到")

    result, username, avatar = row

    if result.status == False:
        raise HTTPException(status_code=403, detail="当前未被公开")

    # 当前应展示的浏览量：
    # - 本次触发落库（flush_hit）：result.views 已包含 Redis 计数，直接展示 DB 值；
    # - 未触发落库：result.views + 未落库的 Redis 计数（含本次访问）。
    views_total = (result.views or 0) if flush_hit else (result.views or 0) + delta

    data = {
        "msg": "查询成功",
        "id": result.id,
        "name": result.cn_name or result.jp_name or result.en_name or "other",
        "content": result.content,
        "company": result.company,
        "category": result.category,
        "cover": result.cover,
        "images": result.images,
        "tag": result.tag,
        "views": views_total,
        "likes": result.likes,
        "favorite": result.favorite,
        "platfrom": result.platfrom,
        "update_at": result.updated_at,
        "author_name": username,
        "author_avatar": avatar
    }

    await set_to_cache(cache_key, data, expire=60 * 30)

    return data


@router.post("/add")
async def add(
    data: AddGal,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    # 去重只比较实际填写的名称（schema 已保证至少一个非空），避免空串误命中
    existing_conditions = []
    for col, val in (
        (Galgame.cn_name, data.cn_name),
        (Galgame.jp_name, data.jp_name),
        (Galgame.en_name, data.en_name),
    ):
        if val:
            existing_conditions.append(col == val)

    if existing_conditions:
        existing_query = await db.execute(
            select(Galgame.cn_name, Galgame.jp_name, Galgame.en_name)
            .where(or_(*existing_conditions))
        )
        existing_result = existing_query.scalar_one_or_none()
        if existing_result:
            raise HTTPException(status_code=409, detail="该游戏已存在")

    cover = None
    if data.cover:
        # Cloudinary 上传是同步 HTTP + PIL 解码（CPU 密集），丢到线程池避免阻塞事件循环
        res_cover = await run_in_threadpool(upload_image_to_cloudinary, data.cover, "fishmo_gal_cover")
        if res_cover.get("status") == False:
            error = res_cover.get("error")
            raise HTTPException(status_code=500, detail=f"图片上传失败错误如下,Error:{error}")
        cover = res_cover.get("url")

    if data.images:
        images = await run_in_threadpool(upload_images_to_cloudinary, data.images, "fishmo_gal_images")
        if not images:
            raise HTTPException(status_code=500, detail="图片上传错误")
        data.images = images

    new_gal = Galgame(
        cn_name=data.cn_name,
        jp_name=data.jp_name,
        en_name=data.en_name,
        content=data.content,
        company=data.company,
        category=data.category,
        cover=cover,
        images=data.images,
        tag=data.tag,
        platfrom=data.platfrom,
        author_id=user_id
        # status=True 后面出control路由进行管理
    )

    db.add(new_gal)
    await db.commit()
    await db.refresh(new_gal)

    # 新增后版本号 +1（列表/详情缓存 key 均带版本号），并主动清理列表 key
    await delete_cache_pattern("Galgame:*")
    await update_version()

    return {
        "msg": "添加成功",
        "id": new_gal.id
    }


@router.delete("/delete")
async def delete(
    id: int,
    credentails: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentails)

    query = await db.execute(
        select(Galgame)
        .where(Galgame.id == id)
        .where(Galgame.author_id == user_id)
    )
    result = query.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=403, detail="没有该游戏或者您不是发布者")

    await db.delete(result)
    await db.commit()

    # 删除后使相关缓存失效：版本号 +1 + 主动清理 key（pattern 无空格，与 get_cache_key 生成的 key 匹配）
    await delete_cache_pattern("Galgame:*")
    await delete_cache_pattern(f"Gal_visit:*id={id}")
    # 清理浏览量 Redis 计数 key，避免残留
    await delete_cache(f"gal_views:{id}")
    await update_version()

    return {
        "msg": "删除成功",
        "id": id,
        "user_id": user_id
    }


@router.put("/edit")
async def edit(
    id: int,
    data: EditGal,
    credentails: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentails)

    query = await db.execute(
        select(Galgame)
        .where(Galgame.id == id)
        .where(Galgame.author_id == user_id)
    )
    result = query.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=403, detail="没有该游戏或者您不是发布者")

    if data.cn_name:
        result.cn_name = data.cn_name

    if data.jp_name:
        result.jp_name = data.jp_name

    if data.en_name:
        result.en_name = data.en_name

    if data.content:
        result.content = data.content

    if data.company:
        result.company = data.company

    if data.tag:
        result.tag = data.tag

    if data.platfrom:
        result.platfrom = data.platfrom

    await db.commit()

    # 编辑成功后使相关缓存失效：版本号 +1 + 主动清理 key
    await delete_cache_pattern("Galgame:*")
    await delete_cache_pattern(f"Gal_visit:*id={id}")
    await update_version()

    return {
        "msg": "编辑成功",
        "id": id,
        "user_id": user_id
    }
