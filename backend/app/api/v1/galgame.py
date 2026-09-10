from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.db import get_db
from config.cache import (
    get_search_version, get_cache_key, get_from_cache, set_to_cache,
    delete_cache_pattern, delete_cache, update_version,
    GAL_VERSION_KEY,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.exc import IntegrityError
from model.galgame import Galgame
from model.user import User
from schemas.galgame import GalItem, GalList, PlatformEnum, CategoryEnum, AddGal, EditGal
from typing import Optional
from utils.verify_user import verify_login,verify_admin
from utils.webp import upload_image_to_cloudinary, upload_images_to_cloudinary
from utils.counter import ViewCounter

router = APIRouter(prefix="/api/v1/galgame", tags=["gal"])
security = HTTPBearer(auto_error=False)

@router.get("/", response_model=GalList)
async def index(
    category: Optional[CategoryEnum] = None,
    platform: Optional[PlatformEnum] = None,
    author_id: Optional[int] = Query(None, description="按作者 id 过滤（我的游戏 / 个人主页列表）"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    version = await get_search_version(GAL_VERSION_KEY)
    cache_key = get_cache_key(
        "Galgame", page=page, size=size, category=category, platform=platform,
        author_id=author_id, version=version,
    )

    cache_data = await get_from_cache(cache_key)
    if cache_data:
        return cache_data

    skip = (page - 1) * size
    # 过滤条件集中管理：列表查询与总数统计共用同一组 WHERE，保证两者口径一致
    filters = []
    if author_id is not None:  # 按作者过滤（管理/个人主页列表）
        filters.append(Galgame.author_id == author_id)
    else: #作者可见自己的作品，其他人只能看到公开的
        filters.append(Galgame.status == True)  # 可见状态

    if category:  # 有作品类型选择（枚举绑定原始字符串值，避免 str-枚举绑定歧义）
        filters.append(Galgame.category == category.value)
    if platform:  # 有选择平台
        filters.append(Galgame.platfrom.contains([platform]))
    

    stmt = (
        select(Galgame.id, Galgame.author_id, Galgame.cn_name, Galgame.jp_name, Galgame.en_name, Galgame.cover, Galgame.views, User.username, User.avatar)
        .join(Galgame.author)
        .where(*filters)
        .offset(skip)
        .limit(size)
        .order_by(Galgame.updated_at.desc())
    )

    result = await db.execute(stmt)

    # 总数统计复用同一组 WHERE（不带 offset/limit），返回真实总条数而非页数
    cnt = await db.execute(
        select(func.count(Galgame.id)).select_from(Galgame).where(*filters)
    )
    rows = result.all()
    total = cnt.scalar() or 0

    items = []

    for id, author_id, cn, jp, en, cover, views, author, avatar in rows:
        name = cn or jp or en or "undefind"
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

    data = GalList(
        total=total,
        items=items
    )

    await set_to_cache(cache_key, data.model_dump())

    return data


@router.get("/{id}")
async def visit(
    id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    version = await get_search_version(GAL_VERSION_KEY)
    cache_key = get_cache_key("Gal_visit", id=id, version=version)

    # 浏览量计数与响应缓存解耦：无论缓存是否命中都必须执行 Redis 计数，
    # 否则缓存命中时浏览量会漏计。计数先于缓存判断执行；Redis hash 累积值
    # 由 scheduler 定时批量落库，此处不做落库。
    delta = await ViewCounter.incr(id)

    cache_data = await get_from_cache(cache_key)
    if cache_data:
        # 缓存命中：直接返回缓存内容（views 为写缓存时的值，滞后最长一个缓存周期，可接受）
        return cache_data

    query = await db.execute(
        select(Galgame, User.username, User.avatar).join(Galgame.author).where(Galgame.id == id)
    )
    row = query.first()

    if not row:
        raise HTTPException(status_code=404, detail="未找到")

    result, username, avatar = row

    identity = verify_admin(credentials=credentials)

    if result.status == False and identity is False:
        raise HTTPException(status_code=403, detail="当前未被公开")

    views_total = (result.views or 0) + delta

    data = {
        "msg": "查询成功",
        "id": result.id,
        "cn_name": result.cn_name,
        "jp_name": result.jp_name,
        "en_name": result.en_name,
        "author_id": result.author_id,
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
        if not res_cover or not res_cover.get("status"):
            error = (res_cover or {}).get("error", "图片格式不支持或超过大小限制")
            raise HTTPException(status_code=422, detail=f"封面图上传失败：{error}")
        cover = res_cover.get("url")

    if data.images:
        images = await run_in_threadpool(upload_images_to_cloudinary, data.images, "fishmo_gal_images")
        if not images:
            raise HTTPException(status_code=422, detail="图片上传失败，请检查图片格式与大小")
        data.images = images

    new_gal = Galgame(
        cn_name=data.cn_name,
        jp_name=data.jp_name,
        en_name=data.en_name,
        content=data.content,
        company=data.company,
        # 落库枚举原始字符串值；未选择时兜底"其他"，避免 None 写入 NOT NULL 列
        category=data.category.value if data.category else "其他",
        cover=cover,
        images=data.images,
        tag=data.tag,
        platfrom=data.platfrom,
        author_id=user_id,
        status=False  # 新增游戏默认待审核，管理员审核后公开
    )

    db.add(new_gal)
    await db.commit()
    await db.refresh(new_gal)

    # 新增后版本号 +1（列表/详情缓存 key 均带版本号），并主动清理列表 key
    await delete_cache_pattern("Galgame:*")
    await update_version(GAL_VERSION_KEY)

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
    try:
        await db.commit()
    except IntegrityError:
        # 游戏下存在关联链接（link.game_id 外键 ondelete=RESTRICT）时，删除会触发
        # IntegrityError。捕获并返回 400，避免未捕获异常导致 500，同时保留游戏数据。
        await db.rollback()
        raise HTTPException(status_code=400, detail="该游戏存在关联链接，无法删除")

    # 删除后使相关缓存失效：版本号 +1 + 主动清理 key（pattern 无空格，与 get_cache_key 生成的 key 匹配）
    await delete_cache_pattern("Galgame:*")
    await delete_cache_pattern(f"Gal_visit:*id={id}")
    # 清理浏览量 Redis 计数 key，避免残留
    await delete_cache(f"gal_views:{id}")
    await delete_cache_pattern(f"links:*game_id={id}")
    await update_version(GAL_VERSION_KEY)

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

    if data.category:
        result.category = data.category.value

    if data.cover:
        # 编辑表单回填的封面若是已托管 URL（原封面），直接复用，不重复上传；
        # 否则视为新 base64 图，丢到线程池避免阻塞事件循环（同步 HTTP + PIL 解码）。
        if data.cover.startswith(("http://", "https://")):
            result.cover = data.cover
        else:
            res_cover = await run_in_threadpool(upload_image_to_cloudinary, data.cover, "fishmo_gal_cover")
            if not res_cover or not res_cover.get("status"):
                error = (res_cover or {}).get("error", "图片格式不支持或超过大小限制")
                raise HTTPException(status_code=422, detail=f"封面图上传失败：{error}")
            result.cover = res_cover.get("url")

    if data.images:
        # 编辑时 images 可能是「未修改的原 URL + 新增 base64」混合列表：
        # 已托管 URL 直接保留；base64 部分逐张上传并原位放回，避免把 Cloudinary URL
        # 当作 base64 解码（必然失败）导致 500，同时保留前端传入的图片顺序。
        final_images = []
        for img in data.images:
            if img.startswith(("http://", "https://")):
                final_images.append(img)
                continue
            res_img = await run_in_threadpool(upload_image_to_cloudinary, img, "fishmo_gal_images")
            if not res_img or not res_img.get("status"):
                raise HTTPException(status_code=422, detail="图片上传失败，请检查图片格式与大小")
            final_images.append(res_img.get("url"))
        result.images = final_images

    if data.tag:
        result.tag = data.tag

    if data.platfrom:
        result.platfrom = data.platfrom

    await db.commit()

    # 编辑成功后使相关缓存失效：版本号 +1 + 主动清理 key
    await delete_cache_pattern("Galgame:*")
    await delete_cache_pattern(f"Gal_visit:*id={id}")
    await update_version(GAL_VERSION_KEY)

    return {
        "msg": "编辑成功",
        "id": id,
        "user_id": user_id
    }
