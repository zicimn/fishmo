from datetime import datetime
from typing import Optional,List,TYPE_CHECKING

from sqlalchemy import DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column,relationship
from sqlalchemy.sql import func

from config.db import Base

if TYPE_CHECKING:
    from .galgame import Galgame
    from .link import Link
    from .comment import Comment
    from .favorite import Favorite

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[int] = mapped_column(SmallInteger, default=1, comment="0-禁用 1-正常")
    is_admin: Mapped[int] = mapped_column(SmallInteger, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # 集合侧禁止懒加载：任何 User 查询都不应隐式全量加载其 galgames。
    # 如需加载必须显式 selectinload()，避免登录/注册/查询用户时误触全表扫描。
    galgames: Mapped[List["Galgame"]] = relationship(
        "Galgame",
        back_populates="author",
        lazy="raise"
    )

    links: Mapped[List["Link"]] = relationship(
        "Link",
        back_populates="author",
        lazy="raise"
    )

    comments: Mapped[List["Comment"]] = relationship(
        "Comment",
        back_populates="author",
        lazy="raise"
    )

    # C1: 收藏关系集合侧，lazy="raise" 禁止隐式全量加载
    favorites: Mapped[List["Favorite"]] = relationship(
        "Favorite",
        back_populates="author",
        lazy="raise"
    )