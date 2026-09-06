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


@router.get("/{game_id}", response_model=CommentList)
async def get_list(
    game_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    version = await get_search_version(COMMENT_VERSION_KEY)
    cache_key = get_cache_key("comments", game_id=game_id, page=page, size=size, version=version)
    cache_data = await get_from_cache(cache_key)

    if cache_data:
        return cache_data

    # 先校验游戏存在，避免对不存在的游戏返回空列表
    existing_query = await db.execute(select(Galgame.id).where(Galgame.id == game_id))
    existing_result = existing_query.scalar_one_or_none()
    if not existing_result:
        raise HTTPException(status_code=404, detail="未找到该游戏")

    skip = (page - 1) * size

    # 过滤条件集中管理：列表查询与总数统计共用同一组 WHERE，保证两者口径一致。
    # receive_id 存游戏 id，与 add 时的写入语义保持一致，避免跨游戏串数据。
    filters = [Comment.receive_id == game_id, Comment.receive_type == int(ReceiveEnum.galgame)]

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
    game_id: int,
    data: AddComment,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    # 无条件校验游戏存在，不与详情视图缓存命中耦合
    query = await db.execute(select(Galgame.id).where(Galgame.id == game_id))
    result = query.scalar_one_or_none()
    if not result:
        raise HTTPException(status_code=404, detail="未找到该游戏")

    new_comment = Comment(
        content=data.content,
        author_id=user_id,
        receive_id=game_id,
        receive_type=int(ReceiveEnum.galgame)
    )

    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)

    # 新增后版本号 +1 + 主动清理该游戏下的评论列表 key（pattern 与 get_cache_key 生成的 key 匹配）
    await delete_cache_pattern(f"comments:*game_id={game_id}")
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
