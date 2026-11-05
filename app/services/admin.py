"""管理端业务：审核游戏、用户状态、文章管理、统计。"""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.cache import (
    ARTICLE_VERSION_KEY,
    COMMENT_VERSION_KEY,
    GAL_VERSION_KEY,
    LINK_VERSION_KEY,
    USER_VERSION_KEY,
    update_version,
)
from models import Article, Comment, Favorite, Galgame, Link, User
from schemas.galgame import to_admin_gal
from services.article import ArticleService
from utils.responsed import BadRequest, NotFound, info


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.articles = ArticleService(db)

    # ------------------------------------------------------------------
    # 统计
    # ------------------------------------------------------------------
    async def Stats(self) -> dict:
        row = (
            await self.db.execute(
                select(
                    select(func.count(Galgame.id)).scalar_subquery(),
                    select(func.count(Galgame.id))
                    .where(Galgame.status.is_(False))
                    .scalar_subquery(),
                    select(func.count(User.id)).scalar_subquery(),
                    select(func.count(Article.id)).scalar_subquery(),
                    select(func.count(Comment.id)).scalar_subquery(),
                    select(func.count(Link.id)).scalar_subquery(),
                    select(func.count(Favorite.id)).scalar_subquery(),
                )
            )
        ).one()

        keys = ("games", "pending_games", "users", "articles", "comments", "links", "favorites")
        return info("统计成功", data={key: int(value or 0) for key, value in zip(keys, row)})

    # ------------------------------------------------------------------
    # 游戏
    # ------------------------------------------------------------------
    async def BrowseGames(self, page: int, size: int, status: str = "pending") -> dict:
        filters = []
        if status == "pending":
            filters.append(Galgame.status.is_(False))
        elif status == "published":
            filters.append(Galgame.status.is_(True))

        rows = (
            await self.db.execute(
                select(Galgame)
                .where(*filters)
                .order_by(Galgame.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).scalars().all()
        total = (
            await self.db.execute(
                select(func.count(Galgame.id)).select_from(Galgame).where(*filters)
            )
        ).scalar() or 0

        return info(
            "查询成功",
            data={
                "total": int(total),
                "items": [
                    to_admin_gal(
                        gal,
                        author_name=gal.author.username,
                        author_avatar=gal.author.avatar,
                    )
                    for gal in rows
                ],
            },
        )

    async def UpdateGameStatus(self, gal_id: int, status: bool) -> dict:
        from services.galgame import GalgameService

        return await GalgameService(self.db).SetStatusAsAdmin(gal_id, status)

    async def DeleteGame(self, gal_id: int) -> dict:
        from services.galgame import GalgameService

        return await GalgameService(self.db).DeleteAsAdmin(gal_id)

    # ------------------------------------------------------------------
    # 用户
    # ------------------------------------------------------------------
    async def Users(self, page: int, size: int, keyword: str | None = None) -> dict:
        filters = []
        if keyword:
            pattern = f"%{keyword.strip()}%"
            filters.append(or_(User.username.ilike(pattern), User.email.ilike(pattern)))

        gal_count = (
            select(func.count(Galgame.id))
            .where(Galgame.author_id == User.id)
            .correlate(User)
            .scalar_subquery()
        )
        article_count = (
            select(func.count(Article.id))
            .where(Article.author_id == User.id)
            .correlate(User)
            .scalar_subquery()
        )

        rows = (
            await self.db.execute(
                select(User, gal_count, article_count)
                .where(*filters)
                .order_by(User.created_at.desc())
                .offset((page - 1) * size)
                .limit(size)
            )
        ).all()
        total = (
            await self.db.execute(
                select(func.count(User.id)).select_from(User).where(*filters)
            )
        ).scalar() or 0

        items = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar": user.avatar,
                "bio": user.bio,
                "status": int(user.status),
                "is_admin": bool(user.is_admin),
                "gal_cnt": int(gal_cnt or 0),
                "article_cnt": int(article_cnt or 0),
                "created_at": user.created_at,
            }
            for user, gal_cnt, article_cnt in rows
        ]
        return info("查询成功", data={"total": int(total), "items": items})

    async def UpdateUserStatus(self, admin: User, user_id: int, status: bool) -> dict:
        if admin.id == user_id:
            raise BadRequest("不能禁用自己的账号")
        user = await self.db.get(User, user_id)
        if not user:
            raise NotFound("用户不存在")
        if user.is_admin and not status:
            raise BadRequest("不能禁用管理员账号")

        user.status = 1 if status else 0
        await self.db.commit()
        for key in (
            USER_VERSION_KEY,
            GAL_VERSION_KEY,
            LINK_VERSION_KEY,
            COMMENT_VERSION_KEY,
            ARTICLE_VERSION_KEY,
        ):
            await update_version(key)
        return info(
            "账号已启用" if status else "账号已禁用",
            data={"user_id": user_id, "status": int(user.status)},
        )

    # ------------------------------------------------------------------
    # 文章
    # ------------------------------------------------------------------
    async def BrowseArticles(self, page: int, size: int, status: str = "all") -> dict:
        return await self.articles.ListForAdmin(page, size, status)

    async def UpdateArticleStatus(self, article_id: int, status: bool) -> dict:
        return await self.articles.SetStatusAsAdmin(article_id, status)

    async def DeleteArticle(self, article_id: int) -> dict:
        return await self.articles.DeleteAsAdmin(article_id)