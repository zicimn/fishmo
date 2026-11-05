"""登录、注册、登出。"""

import logging

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.cache import USER_VERSION_KEY, blacklist_token, rate_limit, update_version
from models import User
from schemas.user import Account, LoginRequest, to_user_private
from services.image import AVATAR_SIZE, ImageService
from utils.email import verify_email_code
from utils.responsed import AppError, BadRequest, Busy, Conflict, Forbidden, Unauthorized, info
from utils.verify import (
    DUMMY_PASSWORD_HASH,
    TokenPayload,
    create_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)

# 登录：同一 IP 60 次/5 分钟；同一账号 10 次/5 分钟
LOGIN_IP_LIMIT = (60, 300)
LOGIN_ACCOUNT_LIMIT = (10, 300)
# 注册：同一 IP 5 次/小时
REGISTER_IP_LIMIT = (5, 3600)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _issue(self, user: User) -> dict:
        token = create_access_token(user.id, user.username)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": 7 * 24 * 3600,
            "user": to_user_private(user),
        }

    async def Login(self, data: LoginRequest, ip: str) -> dict:
        if not await rate_limit(f"rl:login:ip:{ip}", *LOGIN_IP_LIMIT):
            raise Busy("登录尝试过于频繁，请稍后再试")
        if not await rate_limit(
            f"rl:login:account:{data.username.lower()}", *LOGIN_ACCOUNT_LIMIT
        ):
            raise Busy("该账号尝试次数过多，请稍后再试")

        user = (
            await self.db.execute(select(User).where(User.username == data.username))
        ).scalar_one_or_none()

        # 即使账号不存在也执行一次 argon2 校验，避免时序枚举
        password_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
        password_ok = await verify_password(data.password, password_hash)

        if not user or not password_ok:
            raise Unauthorized("用户名或密码不正确")
        if user.status != 1:
            raise Forbidden("账号已被禁用，请联系管理员")

        return info("登录成功", data=await self._issue(user))

    async def Register(self, data: Account, code: str, ip: str) -> dict:
        if not await rate_limit(f"rl:register:ip:{ip}", *REGISTER_IP_LIMIT):
            raise Busy("注册过于频繁，请稍后再试")
        if not await rate_limit(f"rl:register:email:{data.email}", 5, 3600):
            raise Busy("该邮箱验证码请求过于频繁，请稍后再试")

        existing = (
            await self.db.execute(
                select(User.id).where(
                    or_(User.username == data.username, User.email == data.email)
                )
            )
        ).scalar_one_or_none()
        if existing:
            raise Conflict("用户名或邮箱已被占用")

        if not await verify_email_code(data.email, code):
            raise BadRequest("验证码不正确或已过期")

        avatar = await ImageService.ResolveOptional(
            data.avatar, "fishmo_avatars", AVATAR_SIZE, "头像"
        )
        user = User(
            username=data.username,
            email=str(data.email),
            password_hash=await hash_password(data.password),
            avatar=avatar,
            bio=data.bio,
            status=1,
            is_admin=0,
        )
        self.db.add(user)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise Conflict("用户名或邮箱已被占用")

        await self.db.refresh(user)
        await update_version(USER_VERSION_KEY)
        return info("注册成功", data=await self._issue(user))

    async def Logout(self, payload: TokenPayload) -> dict:
        try:
            await blacklist_token(payload.jti, payload.remaining_seconds())
        except Exception:  # noqa: BLE001 - 登出必须失败关闭
            logger.exception("写入 token 黑名单失败")
            raise AppError("退出登录失败，请稍后重试")
        return info("已退出登录")