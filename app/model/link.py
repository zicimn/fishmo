from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Boolean, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from config.db import Base
from datetime import datetime
from .enums import SizeUnitEnum

if TYPE_CHECKING:
    from .user import User
    from .galgame import Galgame


class Link(Base):

    __tablename__ = "link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    url: Mapped[str] = mapped_column(String(255), comment="链接")
    content: Mapped[Optional[str]] = mapped_column(String(255), comment="链接内容")
    code: Mapped[Optional[str]] = mapped_column(String(255), comment="提取码")

    # 外键格式为 表名.列名：author_id -> user.id，game_id -> galgame.id
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="RESTRICT", comment="发布者id"))
    game_id: Mapped[int] = mapped_column(Integer, ForeignKey("galgame.id", ondelete="RESTRICT", comment="游戏id"))
    category: Mapped[Optional[str]] = mapped_column(String(255), comment="链接类型")
    size: Mapped[Optional[float]] = mapped_column(Float, comment="大小")
    size_unit: Mapped[Optional[SizeUnitEnum]] = mapped_column(
        SAEnum(SizeUnitEnum, values_callable=lambda x: [e.value for e in x]),
        default=None, comment="大小单位"
    )
    # 新增即公开：add 时服务端强制 status=True，默认 True 兜底
    status: Mapped[bool] = mapped_column(Boolean, default=True, comment="状态")

    author: Mapped["User"] = relationship(
        "User",
        back_populates="links",
        lazy="selectin"
    )

    # 多对一侧命名为单数 galgame；Galgame.links 集合侧为 lazy="raise"，与项目其他多对一关系一致用 selectin
    galgame: Mapped["Galgame"] = relationship(
        "Galgame",
        back_populates="links",
        lazy="selectin"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
