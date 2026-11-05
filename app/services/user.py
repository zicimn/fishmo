"""用户资料、公开主页与注销。"""

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.cache import (
    COMMENT_VERSION_KEY,
    GAL_VERSION_KEY,
    LINK_VERSION_KEY,
    USER_VERSION_KEY,
    update_version,
)
from models import Article, Galgame, User
from schemas.user import AccountUpdate, to_user_private, to_user_public
from services.image import AVATAR_SIZE, ImageService
from utils.responsed import BadRequest, Conflict, NotFound, info
from utils.verify import hash_password


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def GetInfo(self, target_id: int, viewer: User | None) -> dict:
        user = await self.db.get(User, target_id)
        if not user:
            raise NotFound("用户不存在")

        counts = await self.db.execute(
            select(
                select(func.count(Galgame.id))
                .where(Galgame.author_id == target_id)
                .scalar_subquery(),
                select(func.count(Article.id))
                .where(Article.author_id == target_id)
                .scalar_subquery(),
            )
        )
        gal_cnt, article_cnt = counts.one()
        is_self = bool(viewer and viewer.id == target_id)
        return info(
            "用户信息",
            data=to_user_public(
                user,
                gal_cnt=int(gal_cnt or 0),
                article_cnt=int(article_cnt or 0),
                is_self=is_self,
            ),
        )

    async def UpdateProfile(self, user: User, data: AccountUpdate) -> dict:
        fields = data.model_fields_set

        if "username" in fields and data.username:
            duplicate = (
                await self.db.execute(
                    select(User.id).where(
                        User.username == data.username, User.id != user.id
                    )
                )
            ).scalar_one_or_none()
            if duplicate:
                raise Conflict("用户名已存在")
            user.username = data.username

        if "email" in fields and data.email:
            duplicate = (
                await self.db.execute(
                    select(User.email).where(
                        User.email == data.email, User.id != user.id
                    )
                )
            ).scalar_one_or_none()
            if duplicate:
                raise Conflict("邮箱已存在")
            user.email = str(data.email)

        if "bio" in fields:
            user.bio = data.bio or None

        if "avatar" in fields:
            if data.avatar is None:
                user.avatar = None
            else:
                user.avatar = await ImageService.ResolveOne(
                    data.avatar, "fishmo_avatars", AVATAR_SIZE, "头像"
                )

        if "password" in fields and data.password:
            user.password_hash = await hash_password(data.password)

        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise Conflict("用户名或邮箱已存在")

        await self.db.refresh(user)
        # 用户名/头像被多个业务域的缓存引用
        for key in (USER_VERSION_KEY, GAL_VERSION_KEY, LINK_VERSION_KEY, COMMENT_VERSION_KEY):
            await update_version(key)
        return info("资料已更新", data={"user": to_user_private(user)})

    async def DeleteAccount(self, user: User) -> dict:
        user_id, username = user.id, user.username
        # Core DELETE 绕过 ORM 对 lazy="raise" 集合的级联加载；
        # 若仍有作品，外键 RESTRICT 会抛 IntegrityError
        try:
            await self.db.execute(
                delete(User)
                .where(User.id == user_id)
                .execution_options(synchronize_session=False)
            )
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise BadRequest("该账号下仍有作品，无法注销")

        for key in (USER_VERSION_KEY, GAL_VERSION_KEY, LINK_VERSION_KEY, COMMENT_VERSION_KEY):
            await update_version(key)
        return info("账号已注销", data={"id": user_id, "username": username})