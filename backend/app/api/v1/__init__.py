from .user import router as user_router
from .email import router as email_router
from .galgame import router as gal_router
from .link import router as link_router
from .comment import router as comment_router
__all__ = [
    "user_router",
    "email_router",
    "gal_router",
    "link_router",
    "comment_router"
]