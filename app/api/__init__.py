"""路由聚合：main.py 只需 include 一次 service_router。"""

from fastapi import APIRouter

from .admin import router as admin_router
from .article import router as article_router
from .comment import router as comment_router
from .email import router as email_router
from .favorite import router as favorite_router
from .galgame import router as galgame_router
from .link import router as link_router
from .search import router as search_router
from .user import router as user_router

service_router = APIRouter()
service_router.include_router(user_router)
service_router.include_router(email_router)
service_router.include_router(galgame_router)
service_router.include_router(link_router)
service_router.include_router(comment_router)
service_router.include_router(favorite_router)
service_router.include_router(search_router)
service_router.include_router(article_router)
service_router.include_router(admin_router)

__all__ = ["service_router"]