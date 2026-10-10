from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from schemas.article import ArticleList, ArticleItem, ArticlePublish, ArticleDetail, ArticleManageItem, ArticleManageList
from config.cache import (
    get_search_version, get_cache_key, get_from_cache, set_to_cache,
    delete_cache_pattern, update_version,
    ARTICLE_VERSION_KEY,
)
from typing import Optional
from model.article import Article
from model.user import User
from model.comment import Comment
from utils.verify_user import verify_login, verify_admin
from default.file import Default_cover
from utils.webp import upload_image_to_cloudinary, upload_images_to_cloudinary
from utils.counter import ArticleViewCounter

router = APIRouter(prefix="/api/v1/article", tags=["article"])
security = HTTPBearer(auto_error=False)


@router.get("/", response_model=ArticleList)
async def index(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    version = await get_search_version(ARTICLE_VERSION_KEY)
    cache_key = get_cache_key(
        "Article", page=page, size=size, category=category, version=version,
    )
    cache_data = await get_from_cache(cache_key)

    if cache_data:
        return cache_data

    skip = (page - 1) * size

    filters = [Article.status == True]

    if category:
        # category 在 DB 中是逗号分隔的字符串（如 "评测,攻略"），
        # 此处使用 LIKE 匹配，确保传 "评测" 能匹配到包含该分类的文章
        filters.append(Article.category.like(f"%{category}%"))

    # 评论数子查询（receive_type=0 表示 article 类型评论，与 ReceiveEnum.article 对齐）
    comment_stmt = (
        select(func.count(Comment.id))
        .where(Comment.receive_type == 0)
        .where(Comment.receive_id == Article.id)
        .scalar_subquery()
    )

    stmt = (
        select(
            Article.id,
            Article.title,
            Article.cover,
            Article.category,
            Article.created_at,
            Article.views,
            func.coalesce(comment_stmt, 0).label("comment_count"),
        )
        .where(*filters)
        .offset(skip)
        .limit(size)
        .order_by(Article.created_at.desc())
    )

    query = await db.execute(stmt)
    rows = query.all()

    # 总数统计复用同一组 WHERE
    cnt = await db.execute(
        select(func.count(Article.id)).select_from(Article).where(*filters)
    )
    total = cnt.scalar() or 0

    items = []
    for id, title, cover, category, time, views, comcnt in rows:
        items.append(
            ArticleItem(
                id=id,
                title=title,
                cover=cover,
                category=category or "",
                time=time,
                views=views,
                comcnt=comcnt,
            )
        )

    data = ArticleList(total=total, items=items)

    await set_to_cache(cache_key, data.model_dump())

    return data


@router.post("/add")
async def publish(
    data: ArticlePublish,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_id = verify_login(credentials=credentials)

    cover = None
    if data.cover:
        res_cover = await run_in_threadpool(
            upload_image_to_cloudinary, data.cover, "fishmo_article_cover"
        )
        if not res_cover or not res_cover.get("status"):
            error = (res_cover or {}).get("error", "图片格式不支持或超过大小限制")
            raise HTTPException(status_code=422, detail=f"封面上传失败：{error}")
        cover = res_cover.get("url")

    if data.images:
        images = await run_in_threadpool(
            upload_images_to_cloudinary, data.images, "fishmo_gal_images"
        )
        if not images:
            raise HTTPException(status_code=422, detail="图片上传失败，请检查图片格式与大小")
        data.images = images

        if cover is None:
            cover = images[0]

    if cover is None:
        cover = Default_cover

    new_article = Article(
        author_id=user_id,
        title=data.title,
        content=data.content,
        cover=cover,
        images=data.images,
        tag=data.tag,
        category=data.category or "",  # schema validator 已将 [] 转为 ""，此处兜底 None → ""
        status=True,
    )

    db.add(new_article)
    await db.commit()
    await db.refresh(new_article)

    # 新增后缓存失效
    await delete_cache_pattern("Article:*")
    await update_version(ARTICLE_VERSION_KEY)

    return {
        "msg": "添加成功",
        "id": new_article.id,
    }


@router.delete("/delete")
async def delete(
    id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user_id = verify_login(credentials=credentials)

    query = await db.execute(
        select(Article)
        .where(Article.id == id)
        .where(Article.author_id == user_id)
    )
    result = query.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=403, detail="没有该文章或者您不是发布者")

    await db.delete(result)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="该文章存在关联数据，无法删除")

    # 删除后使相关缓存失效
    await delete_cache_pattern("Article:*")
    await delete_cache_pattern(f"Article_visit:*id={id}")
    await update_version(ARTICLE_VERSION_KEY)

    return {
        "msg": "删除成功",
        "id": id,
        "user_id": user_id,
    }


@router.put("/edit")
async def edit(
    id: int,
    data: ArticlePublish,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    user_id = verify_login(credentials=credentials)

    query = await db.execute(
        select(Article)
        .where(Article.id == id)
        .where(Article.author_id == user_id)
    )
    result = query.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=403, detail="没有该文章或者您不是发布者")

    if data.title:
        result.title = data.title
    if data.content:
        result.content = data.content
    if data.category:
        result.category = data.category
    if data.tag:
        result.tag = data.tag

    if data.cover:
        if data.cover.startswith(("http://", "https://")):
            result.cover = data.cover
        else:
            res_cover = await run_in_threadpool(
                upload_image_to_cloudinary, data.cover, "fishmo_article_cover"
            )
            if not res_cover or not res_cover.get("status"):
                error = (res_cover or {}).get("error", "图片格式不支持或超过大小限制")
                raise HTTPException(status_code=422, detail=f"封面图上传失败：{error}")
            result.cover = res_cover.get("url")

    if data.images:
        final_images = []
        for img in data.images:
            if img.startswith(("http://", "https://")):
                final_images.append(img)
                continue
            res_img = await run_in_threadpool(
                upload_image_to_cloudinary, img, "fishmo_gal_images"
            )
            if not res_img or not res_img.get("status"):
                raise HTTPException(status_code=422, detail="图片上传失败，请检查图片格式与大小")
            final_images.append(res_img.get("url"))
        result.images = final_images

    await db.commit()

    # 编辑成功后使相关缓存失效
    await delete_cache_pattern("Article:*")
    await delete_cache_pattern(f"Article_visit:*id={id}")
    await update_version(ARTICLE_VERSION_KEY)

    return {
        "msg": "编辑成功",
        "id": id,
        "user_id": user_id,
    }


@router.get("/manage", response_model=ArticleManageList)
async def manage(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    user_id = verify_login(credentials=credentials)

    skip = (page - 1) * size

    filters = [Article.author_id == user_id]

    query = await db.execute(
        select(Article.id, Article.title, Article.cover)
        .where(*filters)
        .offset(skip)
        .limit(size)
        .order_by(Article.created_at.desc())
    )
    rows = query.all()

    cnt = await db.execute(
        select(func.count(Article.id)).select_from(Article).where(*filters)
    )
    total = cnt.scalar() or 0

    items = [ArticleManageItem(id=id, title=title, cover=cover) for id, title, cover in rows]

    return ArticleManageList(total=total, items=items)


@router.get("/{id}")
async def visit(
    id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    version = await get_search_version(ARTICLE_VERSION_KEY)
    cache_key = get_cache_key("Article_visit", id=id, version=version)

    # 浏览量计数与响应缓存解耦：先计数再判断缓存
    delta = await ArticleViewCounter.incr(id)

    cache_data = await get_from_cache(cache_key)
    if cache_data:
        return cache_data

    query = await db.execute(
        select(Article, User.username, User.avatar)
        .join(Article.author)
        .where(Article.id == id)
    )
    row = query.first()

    if not row:
        raise HTTPException(status_code=404, detail="未找到")

    result, username, avatar = row

    identity = verify_admin(credentials=credentials)
    if result.status is False and identity is False:
        raise HTTPException(status_code=403, detail="当前未被公开")

    # 统计关联评论数
    comment_cnt = await db.execute(
        select(func.count(Comment.id))
        .where(Comment.receive_type == 0)
        .where(Comment.receive_id == id)
    )
    comment_count = comment_cnt.scalar() or 0

    views_total = (result.views or 0) + delta

    data = ArticleDetail(
        id=result.id,
        title=result.title,
        content=result.content,
        cover=result.cover,
        tag=result.tag,
        category=result.category.split(",") if result.category else [],
        images=result.images,
        views=views_total,
        author_id=result.author_id,
        author_name=username,
        author_avatar=avatar,
        comment_count=comment_count,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )

    await set_to_cache(cache_key, data.model_dump(), expire=60 * 30)

    return data