from sqlalchemy import Column, Integer, String, DateTime, Text, SmallInteger,JSON,ForeignKey,Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped,mapped_column,relationship
from typing import Optional,List,TYPE_CHECKING
from config.db import Base
from .enums import PlatformEnum
from datetime import datetime

if TYPE_CHECKING:
    from .user import User
    from .link import Link

class Galgame(Base):
    __tablename__ = "galgame"

    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)

    # 三个名称列 NOT NULL：Python 侧默认空串兜底，避免缺省时写入 NULL 触发 IntegrityError
    cn_name:Mapped[str] = mapped_column(String(50),default="",comment="中文名称")
    en_name:Mapped[str] = mapped_column(String(50),default="",comment="英文名称")
    jp_name:Mapped[str] = mapped_column(String(50),default="",comment="日文名称")

    content:Mapped[Optional[str]] = mapped_column(Text,comment="游戏简介",default=None)
    company:Mapped[Optional[List[str]]] = mapped_column(JSON,default=None)
    category:Mapped[str] = mapped_column(String(50),default="其他")
    cover:Mapped[str] = mapped_column(String(255),comment="封面")
    images:Mapped[Optional[List[str]]] = mapped_column(JSON,default=None)
    tag:Mapped[Optional[List[str]]] = mapped_column(JSON,default=None)

    views:Mapped[int] = mapped_column(Integer,default=0)
    likes:Mapped[int] = mapped_column(Integer,default=0)
    favorite:Mapped[int] = mapped_column(Integer,default=0)
    platfrom:Mapped[Optional[List[PlatformEnum]]] = mapped_column(JSON,default=[],comment="支持平台")
    status:Mapped[bool] = mapped_column(Boolean,default=False,comment="状态")

    author_id: Mapped[int] = mapped_column(Integer,ForeignKey("user.id",ondelete="RESTRICT",comment="发布者id"))

    author:Mapped["User"] = relationship(
        "User",
        back_populates="galgames",
        lazy="selectin"
    )

    # 集合侧禁止懒加载：查询 Galgame 时不应隐式全量加载其 links，需要时显式 selectinload()
    links: Mapped[List["Link"]] = relationship(
        "Link",
        back_populates="galgame",
        lazy="raise"
    )


    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = ()


