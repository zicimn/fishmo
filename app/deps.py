"""依赖注入：服务工厂与鉴权。

管理员身份每次都回库读取，不再信任 JWT 载荷里的 is_admin。
"""

from typing import Optional

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_db
from models import User
from services import (
    AdminService,
    ArticleService,
    AuthService,
    CommentService,
    EmailService,
    FavoriteService,
    GalgameService,
    LinkService,
    SearchService,
    UserService,
)
from utils.responsed import Forbidden, Unauthorized
from utils.verify import (
    TokenPayload,
    get_token_payload,
    security,
    try_decode_credentials,
)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def GetCurrentUser(
    payload: TokenPayload = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    user = await db.get(User, payload.user_id)
    if user is None:
        raise Unauthorized("登录已失效，请重新登录")
    if user.status != 1:
        raise Unauthorized("账号已被禁用")
    return user


async def GetOptionalUser(
    credentials=Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    payload = await try_decode_credentials(credentials)
    if payload is None:
        return None
    user = await db.get(User, payload.user_id)
    if user is None or user.status != 1:
        return None
    return user


async def GetAdminUser(user: User = Depends(GetCurrentUser)) -> User:
    if not user.is_admin:
        raise Forbidden("需要管理员权限")
    return user


def GetAuthService(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


def GetUserService(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


def GetEmailService(db: AsyncSession = Depends(get_db)) -> EmailService:
    return EmailService(db)


def GetGalgameService(db: AsyncSession = Depends(get_db)) -> GalgameService:
    return GalgameService(db)


def GetLinkService(db: AsyncSession = Depends(get_db)) -> LinkService:
    return LinkService(db)


def GetCommentService(db: AsyncSession = Depends(get_db)) -> CommentService:
    return CommentService(db)


def GetFavoriteService(db: AsyncSession = Depends(get_db)) -> FavoriteService:
    return FavoriteService(db)


def GetSearchService(db: AsyncSession = Depends(get_db)) -> SearchService:
    return SearchService(db)


def GetArticleService(db: AsyncSession = Depends(get_db)) -> ArticleService:
    return ArticleService(db)


def GetAdminService(db: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(db)