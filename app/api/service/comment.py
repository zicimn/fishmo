from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.db import get_db
from config.cache import (
    get_search_version, get_cache_key, get_from_cache, set_to_cache,
    delete_cache_pattern, update_version, COMMENT_VERSION_KEY
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from typing import Optional
from utils.verify_user import verify_login
from model.enums import ReceiveEnum
from model.user import User
from model.galgame import Galgame
from model.article import Article
from model.comment import Comment
from schemas.comment import CommentItems, CommentItem, CommentList, AddComment, EditComment
from schemas.user import UserInfo

router = APIRouter(prefix="/api/v1/comment", tags=["comment"])
security = HTTPBearer(auto_error=False)


@router.get("/user/{user_id}", response_model=CommentList)
async def get_list_by_user(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """按用户 id 获取其发表的评论列表（分页，按更新时间倒序，用于个人主页/我的评论管理）。"""
    version = await get_search_version(COMMENT_VERSION_KEY)
    cache_key = get_cache_key("comments_user", user_id=user_id, page=page, size=size, version=version)
    cache_data = await get_from_cache(cache_key)

    if cache_data:
        return cache_data

    skip = (page - 1) * size

    filters = [Comment.author_id == user_id]

    query = await db.execute(
        select(Comment, User.username, User.avatar)
        .join(Comment.author)
        .where(*filters)
        .order_by(Comment.updated_at.desc())
        .offset(skip)
        .limit(size)
    )

    rows = query.all()

    cnt = await db.execute(select(func.count(Comment.id)).select_from(Comment).where(*filters))
    total = cnt.scalar() or 0

    items = []

    for result, username, avatar in rows:
        item = CommentItem(
            id=result.id,
            content=result.content,
            receive_id=result.receive_id,
        )
        account = UserInfo(
            username=username,
            avatar=avatar
        )
        items.append(
            CommentItems(
                item=item,
                account=account
            )
        )

    data = CommentList(
        total=total,
        items=items
    )

    await set_to_cache(cache_key, data.model_dump())

    return data


@router.get("/{target_id}", response_model=CommentList)
async def get_list(
    target_id: int,
    type: str = Query("galgame", description="评论目标类型：galgame（默认）或 article"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    # 根据 type 确定 receive_type 和校验目标存在
    if type == "article":
        receive_type_val = int(ReceiveEnum.article)
        existing = await db.get(Article, target_id)
    else:
        receive_type_val = int(ReceiveEnum.galgame)
        existing = await db.get(Galgame, target_id)

    if not existing:
        raise HTTPException(status_code=404, detail="未找到该目标")

    version = await get_search_version(COMMENT_VERSION_KEY)
    cache_key = get_cache_key("comments", receive_id=target_id, type=type, page=page, size=size, version=version)
    cache_data = await get_from_cache(cache_key)

    if cache_data:
        return cache_data

    skip = (page - 1) * size

    filters = [Comment.receive_id == target_id, Comment.receive_type == receive_type_val]

    query = await db.execute(
        select(Comment, User.username, User.avatar)
        .join(Comment.author)
        .where(*filters)
        .offset(skip)
        .limit(size)
    )

    rows = query.all()

    cnt = await db.execute(select(func.count(Comment.id)).select_from(Comment).where(*filters))
    total = cnt.scalar() or 0

    items = []

    for result, username, avatar in rows:
        item = CommentItem(
            id=result.id,
            content=result.content,
            receive_id=result.receive_id
        )
        account = UserInfo(
            username=username,
            avatar=avatar
        )
        items.append(
            CommentItems(
                item=item,
                account=account
            )
        )

    data = CommentList(
        total=total,
        items=items
    )

    await set_to_cache(cache_key, data.model_dump())

    return data


@router.post("/add")
async def add(
    game_id: int = Query(..., description="目标 id（游戏或文章 id，结合 type 使用）"),
    type: str = Query("galgame", description="目标类型：galgame（默认）或 article"),
    data: AddComment = ...,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    # 根据 type 确定 receive_type 和校验目标存在
    if type == "article":
        receive_type_val = int(ReceiveEnum.article)
        target = await db.get(Article, game_id)
    else:
        receive_type_val = int(ReceiveEnum.galgame)
        target = await db.get(Galgame, game_id)

    if not target:
        raise HTTPException(status_code=404, detail="未找到该目标")

    new_comment = Comment(
        content=data.content,
        author_id=user_id,
        receive_id=game_id,
        receive_type=receive_type_val
    )

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    # 新增后版本号 +1 + 主动清理该目标下的评论列表 key
    await delete_cache_pattern(f"comments:*receive_id={game_id}*")
    await delete_cache_pattern("comments_user:*")
    await update_version(COMMENT_VERSION_KEY)

    return {
        "msg": "添加成功",
        "id": new_comment.id
    }


@router.put("/edit")
async def edit(
    comment_id: int,
    data: EditComment,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = verify_login(credentials=credentials)

    filters = [Comment.id == comment_id, Comment.author_id == user_id]
    query = await db.execute(select(Comment).where(*filters))
    result = query.scalar_one_or_none()

    if not result:
        raise HTTPException(status_code=404, detail="没有该评论")

    if data.content is not None:
        result.content = data.content

    await db.commit()

    # 编辑成功后使相关缓存失效：版本号 +1 + 主动清理列表 key
    await delete_cache_pattern("comments:*")
    await delete_cache_pattern("comments_user:*")
    await update_version(COMMENT_VERSION_KEY)

    return {
        "msg": "编辑成功",
        "id": comment_id,
        "user_id": user_id
    }


@router.delete("/delete")
async def delete(
    comment_id: int,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    result = await db.execute(
        select(Comment).where(Comment.id == comment_id).where(Comment.author_id == user_id)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=403, detail="没有该评论或者您不是发布者")

    await db.delete(comment)
    try:
        await db.commit()
    except IntegrityError:
        # 外键约束等完整性错误统一兜底为 400，避免未捕获异常导致 500
        await db.rollback()
        raise HTTPException(status_code=400, detail="无法删除")

    # 删除后使相关缓存失效：版本号 +1 + 主动清理列表 key
    await delete_cache_pattern("comments:*")
    await delete_cache_pattern("comments_user:*")
    await update_version(COMMENT_VERSION_KEY)

    return {
        "msg": "评论已删除",
        "id": comment_id,
        "user_id": user_id
    }
