from sqlalchemy import Integer,DateTime,Text,ForeignKey,JSON,String,Boolean
from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy.sql import func
from typing import TYPE_CHECKING,Optional,List
from config.db import Base
from datetime import datetime


if TYPE_CHECKING:
    from .user import User

class Article(Base):
    __tablename__ = "article"

    id : Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    title : Mapped[str] = mapped_column(String(255))
    content : Mapped[str] = mapped_column(Text)

    author_id: Mapped[int] = mapped_column(Integer,ForeignKey("user.id",ondelete="RESTRICT",comment="发布者id"))
    category: Mapped[str] = mapped_column(String(255),nullable=False)
    tag : Mapped[Optional[List[str]]] = mapped_column(JSON,default=None,nullable=True)
    status:Mapped[bool] = mapped_column(Boolean,default=False,comment="状态")
    images:Mapped[Optional[List[str]]] = mapped_column(JSON,default=None)
    cover:Mapped[str] = mapped_column(String(255))
    views: Mapped[int] = mapped_column(Integer,default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    author:Mapped["User"] = relationship(
        "User",
        back_populates="articles",
        lazy="selectin"
    )

    # 注意：Article 的评论/收藏是通过多态 receive_id/receive_type 或 gal_id 管理的，
    # 不在 ORM 层面定义直接关系，而是通过显式 SQL 查询操作，避免 mapper 初始化冲突。

    