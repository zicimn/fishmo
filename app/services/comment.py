"""评论（galgame / article 双域 + 2 层嵌套）。"""

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.cache import (
    ARTICLE_VERSION_KEY,
    COMMENT_VERSION_KEY,
    delete_cache_pattern,
    get_cache_key,
    get_from_cache,
    get_version,
    rate_limit,
    set_to_cache,
    update_version,
)
from models import Article, Comment, Galgame, ReceiveEnum, User
from schemas.comment import AddComment, EditComment, to_comment_item
from utils.responsed import BadRequest, Busy, Forbidden, NotFound, info
from utils.sanitize import has_visible_text, sanitize_comment

COMMENT_RATE_LIMIT = (20, 60)


def _receive_type(type_name: str) -> int:
    if type_name == "article":
        return int(ReceiveEnum.article)
    if type_name == "galgame":
        return int(ReceiveEnum.galgame)
    raise BadRequest("评论类型仅支持 galgame 或 article")


class CommentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_target(self, target_id: int, receive_type: int):
        model = Article if receive_type == int(ReceiveEnum.article) else Galgame
        target = await self.db.get(model, target_id)
        if not target:
            raise NotFound("未找到评论目标")
        return target

    async def GetList(self, target_id: int, type_name: str, page: int, size: int) -> dict:
        receive_type = _receive_type(type_name)
        await self._get_target(target_id, receive_type)

        version = await get_version(COMMENT_VERSION_KEY)
        cache_key = get_cache_key(
            "comments",
            receive_id=target_id,
            type=type_name,
            page=page,
            size=size,
            version=version,
        )
        cached = await get_from_cache(cache_key)
        if cached:
            return info("查询成功", data=cached)

        filters = [
            Comment.receive_id == target_id,
            Comment.receive_type == receive_type,
            Comment.parent_id.is_(None),
        ]
        top_comments = (
            await self.db.execute(
                select(Comment)
                .where(*filters)
                .options(
                    selectinload(Comment.author),
                    selectinload(Comment.replies).selectinload(Comment.author),
                )
                .order_by(Comment.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()
        total = (
            await self.db.execute(
                select(func.count(Comment.id)).select_from(Comment).where(*filters)
            )
        ).scalar() or 0

        # 批量解析被回复用户，避免逐条查询
        reply_user_ids = {
            reply.reply_to_id
            for top in top_comments
            for reply in top.replies
            if reply.reply_to_id
        }
        reply_users: dict[int, str] = {}
        if reply_user_ids:
            rows = await self.db.execute(
                select(User.id, User.username).where(User.id.in_(reply_user_ids))
            )
            reply_users = {user_id: username for user_id, username in rows.all()}

        items = []
        for top in top_comments:
            replies = sorted(top.replies, key=lambda item: item.created_at)
            items.append(
                {
                    **to_comment_item(top, author=top.author),
                    "replies": [
                        to_comment_item(
                            reply,
                            author=reply.author,
                            reply_to_username=reply_users.get(reply.reply_to_id),
                        )
                        for reply in replies
                    ],
                    "reply_count": len(replies),
                }
            )

        data = {"total": int(total), "items": items}
        await set_to_cache(cache_key, data, expire=120)
        return info("查询成功", data=data)

    async def GetByUser(self, user_id: int, page: int, size: int) -> dict:
        version = await get_version(COMMENT_VERSION_KEY)
        cache_key = get_cache_key(
            "comments_user", user_id=user_id, page=page, size=size, version=version
        )
        cached = await get_from_cache(cache_key)
        if cached:
            return info("查询成功", data=cached)

        filters = [Comment.author_id == user_id]
        rows = (
            await self.db.execute(
                select(Comment)
                .where(*filters)
                .options(selectinload(Comment.author))
                .order_by(Comment.updated_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()
        total = (
            await self.db.execute(
                select(func.count(Comment.id)).select_from(Comment).where(*filters)
            )
        ).scalar() or 0

        data = {
            "total": int(total),
            "items": [to_comment_item(item, author=item.author) for item in rows],
        }
        await set_to_cache(cache_key, data, expire=120)
        return info("查询成功", data=data)

    async def Add(
        self,
        user_id: int,
        target_id: int,
        type_name: str,
        data: AddComment,
    ) -> dict:
        if not await rate_limit(f"rl:comment:{user_id}", *COMMENT_RATE_LIMIT):
            raise Busy("评论过于频繁，请稍后再试")

        receive_type = _receive_type(type_name)
        await self._get_target(target_id, receive_type)

        content = sanitize_comment(data.content)
        if not has_visible_text(content):
            raise BadRequest("评论内容不能为空")
        if len(data.content) > 2000:
            raise BadRequest("评论内容不能超过 2000 字")

        parent_id = data.parent_id
        reply_to_id = data.reply_to_id
        parent_author_id: int | None = None

        if parent_id is not None:
            parent = await self.db.get(Comment, parent_id)
            if not parent:
                raise NotFound("父评论不存在")
            if parent.receive_id != target_id or parent.receive_type != receive_type:
                raise BadRequest("父评论不属于该目标")
            if parent.parent_id is not None:
                raise BadRequest("不允许超过 2 层嵌套")
            parent_author_id = parent.author_id

            if reply_to_id is not None:
                reply = await self.db.get(Comment, reply_to_id)
                if not reply:
                    raise NotFound("被回复的评论不存在")
                # 只能回复本楼层的楼主或该楼层下的子评论
                if reply.receive_id != target_id or reply.receive_type != receive_type:
                    raise BadRequest("被回复评论不属于该目标")
                if reply.id != parent_id and reply.parent_id != parent_id:
                    raise BadRequest("只能回复同一楼层内的评论")
                reply_to_id = reply.author_id
            else:
                reply_to_id = parent_author_id
        elif reply_to_id is not None:
            raise BadRequest("顶级评论不能指定回复对象")

        comment = Comment(
            content=content,
            author_id=user_id,
            receive_id=target_id,
            receive_type=receive_type,
            parent_id=parent_id,
            reply_to_id=reply_to_id,
        )
        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment)
        await self._invalidate(receive_type, target_id)
        return info("评论已发布", data={"id": comment.id})

    async def Edit(self, user: User, comment_id: int, data: EditComment) -> dict:
        comment = await self.db.get(Comment, comment_id)
        if not comment:
            raise NotFound("评论不存在")
        if comment.author_id != user.id and not user.is_admin:
            raise Forbidden("只能编辑自己的评论")

        content = sanitize_comment(data.content)
        if not has_visible_text(content):
            raise BadRequest("评论内容不能为空")
        comment.content = content

        await self.db.commit()
        await self._invalidate(comment.receive_type, comment.receive_id)
        return info("评论已更新", data={"id": comment_id})

    async def Delete(self, user: User, comment_id: int) -> dict:
        comment = await self.db.get(Comment, comment_id)
        if not comment:
            raise NotFound("评论不存在")
        if comment.author_id != user.id and not user.is_admin:
            raise Forbidden("只能删除自己的评论")

        # 先删子评论，避免 ORM 关系级联触发 lazy="raise"
        await self.db.execute(delete(Comment).where(Comment.parent_id == comment_id))
        await self.db.execute(delete(Comment).where(Comment.id == comment_id))
        await self.db.commit()
        await self._invalidate(comment.receive_type, comment.receive_id)
        return info("评论已删除", data={"id": comment_id})

    async def _invalidate(self, receive_type: int | None = None, target_id: int | None = None) -> None:
        await delete_cache_pattern("comments:*")
        await delete_cache_pattern("comments_user:*")
        await update_version(COMMENT_VERSION_KEY)
        # 文章列表/详情包含评论数，评论变化时必须同步失效文章缓存
        if receive_type == int(ReceiveEnum.article) and target_id is not None:
            await delete_cache_pattern("Article:*")
            await delete_cache_pattern(f"Article_visit:*id={target_id}")
            await update_version(ARTICLE_VERSION_KEY)