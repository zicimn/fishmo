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
from sqlalchemy.orm import selectinload
from typing import Optional
from utils.verify_user import verify_login
from model.enums import ReceiveEnum
from model.user import User
from model.galgame import Galgame
from model.article import Article
from model.comment import Comment
from schemas.comment import (
    CommentItems, CommentItem, CommentList, UserCommentList,
    NestedCommentItems, AddComment, EditComment
)
from schemas.user import UserInfo

router = APIRouter(prefix="/api/v1/comment", tags=["comment"])
security = HTTPBearer(auto_error=False)


@router.get("/user/{user_id}", response_model=UserCommentList)
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
            parent_id=result.parent_id,
            reply_to_id=result.reply_to_id,
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

    data = UserCommentList(
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
    """获取目标的评论列表（仅顶级评论分页，每个顶级评论附带其子评论列表）。"""
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

    # 只查询顶级评论（parent_id IS NULL）
    filters = [
        Comment.receive_id == target_id,
        Comment.receive_type == receive_type_val,
        Comment.parent_id.is_(None)
    ]

    # 使用 selectinload 显式加载子评论（避免 N+1 查询）
    query = await db.execute(
        select(Comment)
        .where(*filters)
        .options(
            selectinload(Comment.replies).selectinload(Comment.author),
            selectinload(Comment.replies)
        )
        .order_by(Comment.created_at.desc())
        .offset(skip)
        .limit(size)
    )

    top_comments = query.scalars().all()

    # 统计顶级评论总数（用于分页）
    cnt = await db.execute(select(func.count(Comment.id)).select_from(Comment).where(*filters))
    total = cnt.scalar() or 0

    items = []

    for comment in top_comments:
        # 构建顶级评论条目
        item = CommentItem(
            id=comment.id,
            content=comment.content,
            receive_id=comment.receive_id,
            parent_id=comment.parent_id,
            reply_to_id=comment.reply_to_id,
        )
        account = UserInfo(
            username=comment.author.username,
            avatar=comment.author.avatar
        )

        # 构建子评论列表（按时间正序）
        replies_list = []
        sorted_replies = sorted(comment.replies, key=lambda r: r.created_at)
        for reply in sorted_replies:
            reply_item = CommentItem(
                id=reply.id,
                content=reply.content,
                receive_id=reply.receive_id,
                parent_id=reply.parent_id,
                reply_to_id=reply.reply_to_id,
            )
            reply_account = UserInfo(
                username=reply.author.username,
                avatar=reply.author.avatar
            )
            # 被回复用户信息
            reply_to_account = None
            if reply.reply_to_id:
                # 需要从已加载的 replies 中查找被回复用户，或单独查询
                # 这里简化处理：如果 reply_to_id 对应的是某个评论的作者
                for r in comment.replies:
                    if r.author_id == reply.reply_to_id:
                        reply_to_account = UserInfo(
                            username=r.author.username,
                            avatar=r.author.avatar
                        )
                        break
                # 如果没找到，可能是回复父评论作者
                if reply_to_account is None and comment.author_id == reply.reply_to_id:
                    reply_to_account = UserInfo(
                        username=comment.author.username,
                        avatar=comment.author.avatar
                    )

            replies_list.append(
                CommentItems(
                    item=reply_item,
                    account=reply_account,
                    reply_to_account=reply_to_account
                )
            )

        items.append(
            NestedCommentItems(
                item=item,
                account=account,
                replies=replies_list,
                reply_count=len(replies_list)
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

    # 如果有 parent_id，验证父评论存在且属于同一目标，且父评论本身是顶级评论
    parent_id = data.parent_id
    reply_to_id = data.reply_to_id

    if parent_id is not None:
        parent_comment = await db.get(Comment, parent_id)
        if not parent_comment:
            raise HTTPException(status_code=404, detail="父评论不存在")

        # 验证父评论属于同一目标
        if parent_comment.receive_id != game_id or parent_comment.receive_type != receive_type_val:
            raise HTTPException(status_code=400, detail="父评论不属于该目标")

        # 验证父评论是顶级评论（不允许超过 2 层嵌套）
        if parent_comment.parent_id is not None:
            raise HTTPException(status_code=400, detail="不允许超过 2 层嵌套")

        # 如果 reply_to_id 有值，前端传的是被回复评论的 ID，需要解析出作者 user_id
        if reply_to_id is not None:
            reply_to_comment = await db.get(Comment, reply_to_id)
            if not reply_to_comment:
                raise HTTPException(status_code=404, detail="被回复的评论不存在")
            # 将 reply_to_id 替换为被回复评论的作者 user_id
            reply_to_id = reply_to_comment.author_id

    new_comment = Comment(
        content=data.content,
        author_id=user_id,
        receive_id=game_id,
        receive_type=receive_type_val,
        parent_id=parent_id,
        reply_to_id=reply_to_id
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
