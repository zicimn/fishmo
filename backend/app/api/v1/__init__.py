from .user import router as user_router
from .email import router as email_router
from .galgame import router as gal_router
__all__ = [
    "user_router",
    "email_router",
    "gal_router"
]