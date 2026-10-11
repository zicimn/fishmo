from sqlalchemy import Integer, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped,mapped_column,relationship
from typing import Optional,List,TYPE_CHECKING
from config.db import Base
from datetime import datetime


if TYPE_CHECKING:
    from .user import User

class Comment(Base):
    __tablename__ = "comment"

    id : Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    content: Mapped[Optional[str]] = mapped_column(Text)

    author_id: Mapped[int] = mapped_column(Integer,ForeignKey("user.id",ondelete="RESTRICT",comment="发布者id"))
    # receive_id 按 receive_type 区分目标对象：当前 receive_type=galgame 时存游戏 id。
    # 保持裸 Integer（不做外键），兼容未来 article 等类型的多态目标。
    receive_id: Mapped[int] = mapped_column(Integer,comment="接收对象id")
    receive_type: Mapped[int] = mapped_column(Integer,comment="接收类型")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    author:Mapped["User"] = relationship(
        "User",
        back_populates="comments",
        lazy="selectin"
    )