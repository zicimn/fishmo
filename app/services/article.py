"""文章业务：列表、详情、发布、编辑、删除、个人管理。"""

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.cache import (
    ARTICLE_VERSION_KEY,
    COMMENT_VERSION_KEY,
    delete_cache_pattern,
    get_cache_key,
    get_from_cache,
    get_version,
    set_to_cache,
    update_version,
)
from default.file import Default_cover
from models import Article, Comment, ReceiveEnum, User
from schemas.article import (
    ArticleEdit,
    ArticlePublish,
    to_admin_article,
    to_article_detail,
    to_article_manage,
    to_article_preview,
)
from services.image import ImageService
from utils.counter import ArticleViewCounter
from utils.responsed import Conflict, Forbidden, NotFound, info

ARTICLE_COVER_FOLDER = "fishmo_article_cover"
ARTICLE_IMAGE_FOLDER = "fishmo_article_images"


def _comment_count_subquery():
    return (
        select(func.count(Comment.id))
        .where(Comment.receive_type == int(ReceiveEnum.article))
        .where(Comment.receive_id == Article.id)
        .scalar_subquery()
    )


def _clean_list(values: list[str] | None, max_items: int = 20, max_len: int = 40) -> list[str]:
    cleaned: list[str] = []
    for value in values or []:
        text = str(value).strip()[:max_len]
        if text and text not in cleaned:
            cleaned.append(text)
        if len(cleaned) >= max_items:
            break
    return cleaned


class ArticleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def GetList(
        self,
        page: int,
        size: int,
        category: str | None = None,
    ) -> dict:
        version = await get_version(ARTICLE_VERSION_KEY)
        cache_key = get_cache_key(
            "Article", page=page, size=size, category=category, version=version
        )
        cached = await get_from_cache(cache_key)
        if cached:
            return info("查询成功", data=cached)

        filters = [Article.status.is_(True)]
        if category:
            filters.append(Article.category.like(f"%{category}%"))

        comment_count = _comment_count_subquery()
        rows = (
            await self.db.execute(
                select(
                    Article.id,
                    Article.title,
                    Article.cover,
                    Article.category,
                    Article.created_at,
                    Article.views,
                    func.coalesce(comment_count, 0).label("comment_count"),
                    User.id.label("author_id"),
                    User.username.label("author_name"),
                    User.avatar.label("author_avatar"),
                )
                .join(User, User.id == Article.author_id)
                .where(*filters)
                .order_by(Article.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).all()
        total = (
            await self.db.execute(
                select(func.count(Article.id)).select_from(Article).where(*filters)
            )
        ).scalar() or 0

        items = [
            to_article_preview(
                article_id=row.id,
                title=row.title,
                cover=row.cover,
                category=row.category,
                views=row.views,
                comment_count=row.comment_count,
                created_at=row.created_at,
                author_id=row.author_id,
                author_name=row.author_name,
                author_avatar=row.author_avatar,
            )
            for row in rows
        ]
        data = {"total": int(total), "items": items}
        await set_to_cache(cache_key, data)
        return info("查询成功", data=data)

    async def GetId(self, article_id: int, viewer: User | None = None) -> dict:
        version = await get_version(ARTICLE_VERSION_KEY)
        cache_key = get_cache_key("Article_visit", id=article_id, version=version)

        delta = await ArticleViewCounter.incr(article_id)
        cached = await get_from_cache(cache_key)
        if cached:
            return info("查询成功", data=cached)

        row = (
            await self.db.execute(
                select(Article, User)
                .join(User, User.id == Article.author_id)
                .where(Article.id == article_id)
            )
        ).first()
        if not row:
            raise NotFound("未找到该文章")

        article, author = row
        allowed_private = bool(
            viewer and (viewer.id == article.author_id or viewer.is_admin)
        )
        if not article.status and not allowed_private:
            raise Forbidden("该文章尚未公开")

        comment_count = (
            await self.db.execute(
                select(func.count(Comment.id))
                .where(Comment.receive_type == int(ReceiveEnum.article))
                .where(Comment.receive_id == article_id)
            )
        ).scalar() or 0

        data = to_article_detail(
            article,
            author=author,
            views_total=(article.views or 0) + delta,
            comment_count=int(comment_count),
        )
        if article.status:
            await set_to_cache(cache_key, data, expire=60 * 30)
        return info("查询成功", data=data)

    async def Manage(self, user_id: int, page: int, size: int) -> dict:
        filters = [Article.author_id == user_id]
        rows = (
            await self.db.execute(
                select(Article)
                .where(*filters)
                .order_by(Article.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()
        total = (
            await self.db.execute(
                select(func.count(Article.id)).select_from(Article).where(*filters)
            )
        ).scalar() or 0
        return info(
            "查询成功",
            data={"total": int(total), "items": [to_article_manage(item) for item in rows]},
        )

    async def Create(self, user_id: int, data: ArticlePublish) -> dict:
        cover = await ImageService.ResolveOptional(
            data.cover, ARTICLE_COVER_FOLDER, label="封面图"
        )
        images = (
            await ImageService.ResolveMany(data.images, ARTICLE_IMAGE_FOLDER, label="插图")
            if data.images
            else None
        )
        if cover is None and images:
            cover = images[0]
        if cover is None:
            cover = Default_cover

        article = Article(
            author_id=user_id,
            title=data.title.strip(),
            content=data.content,
            cover=cover,
            images=images,
            tag=_clean_list(data.tag),
            category=(data.category or "").strip(),
            status=True,
        )
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        await self.Invalidate(article.id)
        return info("发布成功", data={"id": article.id})

    async def Update(self, user_id: int, article_id: int, data: ArticleEdit) -> dict:
        article = await self._get_owned(user_id, article_id)
        fields = data.model_fields_set

        if "title" in fields and data.title:
            article.title = data.title.strip()
        if "content" in fields and data.content is not None:
            article.content = data.content
        if "category" in fields:
            article.category = (data.category or "").strip()
        if "tag" in fields:
            article.tag = _clean_list(data.tag)
        if "cover" in fields and data.cover:
            article.cover = await ImageService.ResolveOne(
                data.cover, ARTICLE_COVER_FOLDER, label="封面图"
            )
        if "images" in fields:
            if data.images is None:
                article.images = None
            else:
                article.images = await ImageService.ResolveMany(
                    data.images, ARTICLE_IMAGE_FOLDER, label="插图"
                )

        await self.db.commit()
        await self.db.refresh(article)
        await self.Invalidate(article_id)
        return info("编辑成功", data={"id": article_id})

    async def Delete(self, user_id: int, article_id: int) -> dict:
        article = await self._get_owned(user_id, article_id)
        return await self._delete(article, "删除成功")

    # ------------------------------------------------------------------
    # 管理端
    # ------------------------------------------------------------------
    async def ListForAdmin(
        self,
        page: int,
        size: int,
        status: str = "all",
    ) -> dict:
        filters = []
        if status == "published":
            filters.append(Article.status.is_(True))
        elif status == "hidden":
            filters.append(Article.status.is_(False))

        rows = (
            await self.db.execute(
                select(Article)
                .where(*filters)
                .order_by(Article.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()
        total = (
            await self.db.execute(
                select(func.count(Article.id)).select_from(Article).where(*filters)
            )
        ).scalar() or 0
        return info(
            "查询成功",
            data={
                "total": int(total),
                "items": [to_admin_article(item, author=item.author) for item in rows],
            },
        )

    async def SetStatusAsAdmin(self, article_id: int, status: bool) -> dict:
        article = await self.db.get(Article, article_id)
        if not article:
            raise NotFound("文章不存在")
        article.status = status
        await self.db.commit()
        await self.Invalidate(article_id)
        return info(
            "文章已公开" if status else "文章已隐藏",
            data={"article_id": article_id, "status": status},
        )

    async def DeleteAsAdmin(self, article_id: int) -> dict:
        article = await self.db.get(Article, article_id)
        if not article:
            raise NotFound("文章不存在")
        return await self._delete(article, "已删除该文章")

    async def _delete(self, article: Article, msg: str) -> dict:
        article_id = article.id
        await self.db.execute(
            delete(Comment).where(
                Comment.receive_id == article_id,
                Comment.receive_type == int(ReceiveEnum.article),
            )
        )
        await self.db.delete(article)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise Conflict("该文章存在关联数据，无法删除")

        await ArticleViewCounter.remove(article_id)
        await self.Invalidate(article_id, cascaded=True)
        return info(msg, data={"id": article_id})

    async def _get_owned(self, user_id: int, article_id: int) -> Article:
        article = (
            await self.db.execute(
                select(Article).where(
                    Article.id == article_id, Article.author_id == user_id
                )
            )
        ).scalar_one_or_none()
        if not article:
            raise Forbidden("没有该文章，或您不是发布者")
        return article

    async def Invalidate(self, article_id: int, *, cascaded: bool = False) -> None:
        await delete_cache_pattern("Article:*")
        await delete_cache_pattern(f"Article_visit:*id={article_id}")
        await update_version(ARTICLE_VERSION_KEY)
        if cascaded:
            await delete_cache_pattern(f"comments:*receive_id={article_id}*")
            await delete_cache_pattern("comments_user:*")
            await update_version(COMMENT_VERSION_KEY)