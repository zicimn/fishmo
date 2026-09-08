from sqlalchemy import ForeignKey, DateTime, UniqueConstraint
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from config.db import Base  # W5: 修正导入路径（原 app.config）
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .galgame import Galgame


class Favorite(Base):
    __tablename__ = "favorite"

    # C5: 同一用户对同一游戏只能收藏一次
    __table_args__ = (
        UniqueConstraint("user_id", "gal_id", name="uq_favorite_user_gal"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"), comment="用户ID"
    )

    gal_id: Mapped[int] = mapped_column(
        ForeignKey("galgame.id", ondelete="RESTRICT"), comment="文章ID"
    )

    # W7: 使用 server_default=func.now() 替代 default=datetime.now
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="收藏时间"
    )

    # C1: back_populates 从 "links" 改为 "favorites"，避免与 Link 模型冲突
    author: Mapped["User"] = relationship(
        "User",
        back_populates="favorites",
        lazy="selectin"
    )

    galgame: Mapped["Galgame"] = relationship(
        "Galgame",
        back_populates="favorites",
        lazy="selectin"
    )
