"""Galgame 业务：列表、详情、随机、发布、编辑、删除。"""

import random

from sqlalchemy import delete, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.cache import (
    COMMENT_VERSION_KEY,
    GAL_VERSION_KEY,
    LINK_VERSION_KEY,
    delete_cache_pattern,
    get_cache_key,
    get_from_cache,
    get_version,
    set_to_cache,
    update_version,
)
from models import Comment, Favorite, Galgame, Link, ReceiveEnum, User
from schemas.galgame import AddGal, EditGal, to_gal_detail, to_gal_item
from services.image import ImageService
from utils.counter import ViewCounter
from utils.responsed import (
    BadRequest,
    Conflict,
    Forbidden,
    NotFound,
    info,
)

GAL_COVER_FOLDER = "fishmo_gal_cover"
GAL_IMAGE_FOLDER = "fishmo_gal_images"


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _clean_list(values: list[str] | None, max_items: int = 20, max_len: int = 40) -> list[str]:
    cleaned: list[str] = []
    for value in values or []:
        text = str(value).strip()[:max_len]
        if text and text not in cleaned:
            cleaned.append(text)
        if len(cleaned) >= max_items:
            break
    return cleaned


class GalgameService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    async def GetList(
        self,
        *,
        page: int,
        size: int,
        category: str | None = None,
        platform: str | None = None,
        author_id: int | None = None,
        keyword: str | None = None,
        sort: str = "updated_at",
        viewer: User | None = None,
    ) -> dict:
        if sort not in ("updated_at", "views"):
            sort = "updated_at"

        version = await get_version(GAL_VERSION_KEY)
        cache_key = get_cache_key(
            "Galgame",
            page=page,
            size=size,
            category=category,
            platform=platform,
            author_id=author_id,
            keyword=keyword,
            sort=sort,
            version=version,
        )
        cached = await get_from_cache(cache_key)
        if cached:
            return info("查询成功", data=cached)

        filters = []
        # 作者本人/管理员可按 author_id 查看自己的全部作品；其他人只能看已公开作品
        can_see_private = bool(
            author_id is not None
            and viewer is not None
            and (viewer.id == author_id or viewer.is_admin)
        )
        if author_id is not None:
            filters.append(Galgame.author_id == author_id)
        if not can_see_private:
            filters.append(Galgame.status.is_(True))
        if category:
            filters.append(Galgame.category == category)
        if platform:
            filters.append(Galgame.platfrom.contains([platform]))
        if keyword:
            pattern = f"%{_escape_like(keyword.strip())}%"
            filters.append(
                or_(
                    Galgame.cn_name.ilike(pattern),
                    Galgame.jp_name.ilike(pattern),
                    Galgame.en_name.ilike(pattern),
                )
            )

        stmt = (
            select(
                Galgame.id,
                Galgame.author_id,
                Galgame.name,
                Galgame.cover,
                Galgame.views,
                Galgame.category,
                Galgame.updated_at,
                Galgame.status,
                User.username,
                User.avatar,
            )
            .join(User, User.id == Galgame.author_id)
            .where(*filters)
            .offset((page - 1) * size)
            .limit(size)
            .order_by(
                Galgame.views.desc() if sort == "views" else Galgame.updated_at.desc()
            )
        )
        rows = (await self.db.execute(stmt)).all()
        total = (
            await self.db.execute(
                select(func.count(Galgame.id)).select_from(Galgame).where(*filters)
            )
        ).scalar() or 0

        items = [
            to_gal_item(
                gal_id=row.id,
                name=row.name,
                cover=row.cover,
                views=row.views,
                category=row.category,
                updated_at=row.updated_at,
                status=row.status,
                author_id=row.author_id,
                author_name=row.username,
                author_avatar=row.avatar,
            )
            for row in rows
        ]
        data = {"total": int(total), "items": items}
        await set_to_cache(cache_key, data)
        return info("查询成功", data=data)

    async def GetId(self, gal_id: int, viewer: User | None = None) -> dict:
        version = await get_version(GAL_VERSION_KEY)
        cache_key = get_cache_key("Gal_visit", id=gal_id, version=version)

        # 浏览量计数与缓存解耦：即使命中缓存也要先计数
        delta = await ViewCounter.incr(gal_id)
        cached = await get_from_cache(cache_key)

        if cached:
            data = dict(cached)
            data["is_favorited"] = await self._is_favorited(gal_id, viewer)
            return info("查询成功", data=data)

        row = (
            await self.db.execute(
                select(Galgame, User.username, User.avatar)
                .join(User, User.id == Galgame.author_id)
                .where(Galgame.id == gal_id)
            )
        ).first()
        if not row:
            raise NotFound("未找到该游戏")

        gal, author_name, author_avatar = row
        allowed_private = bool(
            viewer and (viewer.id == gal.author_id or viewer.is_admin)
        )
        if not gal.status and not allowed_private:
            raise Forbidden("该游戏尚未公开")

        data = to_gal_detail(
            gal,
            author_name=author_name,
            author_avatar=author_avatar,
            views_total=(gal.views or 0) + delta,
            is_favorited=await self._is_favorited(gal_id, viewer),
        )
        if gal.status:
            await set_to_cache(cache_key, data, expire=60 * 30)
        return info("查询成功", data=data)

    async def Random(self) -> dict:
        gal_id = (
            await self.db.execute(
                select(Galgame.id)
                .where(Galgame.status.is_(True))
                .order_by(func.rand())
                .limit(1)
            )
        ).scalar_one_or_none()
        if gal_id is None:
            raise NotFound("暂无游戏")
        return info("随机游戏", data={"id": gal_id})

    # ------------------------------------------------------------------
    # 写入
    # ------------------------------------------------------------------
    async def Create(self, user_id: int, data: AddGal) -> dict:
        duplicate = (
            await self.db.execute(select(Galgame.id).where(Galgame.name == data.name))
        ).scalar_one_or_none()
        if duplicate:
            raise Conflict("该游戏已存在")

        cover = await ImageService.ResolveOne(
            data.cover, GAL_COVER_FOLDER, label="封面图"
        )
        images = (
            await ImageService.ResolveMany(data.images, GAL_IMAGE_FOLDER, label="截图")
            if data.images
            else None
        )

        gal = Galgame(
            name=data.name,
            cn_name=data.cn_name or "",
            jp_name=data.jp_name or "",
            en_name=data.en_name or "",
            content=data.content,
            company=_clean_list(data.company),
            category=data.category.value if data.category else "其他",
            cover=cover,
            images=images,
            tag=_clean_list(data.tag),
            platfrom=[item.value for item in data.platfrom] if data.platfrom else [],
            author_id=user_id,
            status=False,  # 新发布默认待审核
        )
        self.db.add(gal)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise Conflict("该游戏已存在")
        await self.db.refresh(gal)
        await self.Invalidate(gal.id)
        return info("发布成功，等待管理员审核", data={"id": gal.id})

    async def Update(self, user_id: int, gal_id: int, data: EditGal) -> dict:
        gal = await self._get_owned(user_id, gal_id)
        fields = data.model_fields_set

        if "name" in fields and data.name:
            name = data.name.strip()
            duplicate = (
                await self.db.execute(
                    select(Galgame.id).where(
                        Galgame.name == name, Galgame.id != gal_id
                    )
                )
            ).scalar_one_or_none()
            if duplicate:
                raise Conflict("该游戏名称已存在")
            gal.name = name

        for field, value in (
            ("cn_name", data.cn_name),
            ("jp_name", data.jp_name),
            ("en_name", data.en_name),
        ):
            if field in fields:
                setattr(gal, field, (value or "").strip())

        if "content" in fields:
            gal.content = (data.content or "").strip() or None
        if "company" in fields:
            gal.company = _clean_list(data.company)
        if "category" in fields and data.category is not None:
            gal.category = data.category.value
        if "tag" in fields:
            gal.tag = _clean_list(data.tag)
        if "platfrom" in fields:
            gal.platfrom = [item.value for item in data.platfrom] if data.platfrom else []

        if "cover" in fields and data.cover:
            gal.cover = await ImageService.ResolveOne(
                data.cover, GAL_COVER_FOLDER, label="封面图"
            )
        if "images" in fields:
            if data.images is None:
                gal.images = None
            else:
                gal.images = await ImageService.ResolveMany(
                    data.images, GAL_IMAGE_FOLDER, label="截图"
                )

        await self.db.commit()
        await self.db.refresh(gal)
        await self.Invalidate(gal_id)
        return info("编辑成功", data={"id": gal_id})

    async def Delete(self, user_id: int, gal_id: int) -> dict:
        gal = await self._get_owned(user_id, gal_id)
        return await self._delete_cascade(gal, msg="删除成功")

    async def DeleteAsAdmin(self, gal_id: int) -> dict:
        gal = await self.db.get(Galgame, gal_id)
        if not gal:
            raise NotFound("游戏不存在")
        return await self._delete_cascade(gal, msg="已删除该游戏")

    async def SetStatusAsAdmin(self, gal_id: int, status: bool) -> dict:
        gal = await self.db.get(Galgame, gal_id)
        if not gal:
            raise NotFound("游戏不存在")
        gal.status = status
        await self.db.commit()
        await self.Invalidate(gal_id)
        return info(
            "已通过该游戏" if status else "已下架该游戏",
            data={"gal_id": gal_id, "status": status},
        )

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    async def _get_owned(self, user_id: int, gal_id: int) -> Galgame:
        gal = (
            await self.db.execute(
                select(Galgame).where(
                    Galgame.id == gal_id, Galgame.author_id == user_id
                )
            )
        ).scalar_one_or_none()
        if not gal:
            raise Forbidden("没有该游戏，或您不是发布者")
        return gal

    async def _is_favorited(self, gal_id: int, viewer: User | None) -> bool:
        if viewer is None:
            return False
        favorite_id = (
            await self.db.execute(
                select(Favorite.id).where(
                    Favorite.user_id == viewer.id, Favorite.gal_id == gal_id
                )
            )
        ).scalar_one_or_none()
        return favorite_id is not None

    async def _delete_cascade(self, gal: Galgame, msg: str) -> dict:
        gal_id = gal.id
        # 关联数据先删，避免外键 RESTRICT 阻断删除
        await self.db.execute(delete(Favorite).where(Favorite.gal_id == gal_id))
        await self.db.execute(delete(Link).where(Link.game_id == gal_id))
        await self.db.execute(
            delete(Comment).where(
                Comment.receive_id == gal_id,
                Comment.receive_type == int(ReceiveEnum.galgame),
            )
        )
        # 用 Core DELETE 绕过 ORM 对 lazy="raise" 集合的级联加载
        try:
            await self.db.execute(
                delete(Galgame)
                .where(Galgame.id == gal_id)
                .execution_options(synchronize_session=False)
            )
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise BadRequest("该游戏存在关联数据，无法删除")

        await ViewCounter.remove(gal_id)
        await self.Invalidate(gal_id, cascaded=True)
        return info(msg, data={"id": gal_id})

    async def Invalidate(self, gal_id: int, *, cascaded: bool = False) -> None:
        await delete_cache_pattern("Galgame:*")
        await delete_cache_pattern(f"Gal_visit:*id={gal_id}")
        await update_version(GAL_VERSION_KEY)
        if cascaded:
            await delete_cache_pattern(f"links:*game_id={gal_id}*")
            await delete_cache_pattern(f"comments:*receive_id={gal_id}*")
            await delete_cache_pattern("comments_user:*")
            await update_version(LINK_VERSION_KEY)
            await update_version(COMMENT_VERSION_KEY)