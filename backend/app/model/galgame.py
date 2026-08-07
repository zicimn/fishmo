from sqlalchemy import Column, Integer, String, DateTime, Text, SmallInteger,JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped,mapped_column
from typing import Optional,List
from config.db import Base
from schemas.galgame import PlatformEnum

class Galgame(Base):
    __tablename__ = "galgame"

    id:Mapped[int] = mapped_column(Integer,primary_key=True,autoincrement=True)
    uid:Mapped[int] = mapped_column(Integer,unique=True)

    cn_name:Mapped[str] = mapped_column(String(50),comment="中文名称")
    en_name:Mapped[str] = mapped_column(String(50),comment="英文名称")
    jp_name:Mapped[str] = mapped_column(String(50),comment="日文名称")

    content:Mapped[Optional[str]] = mapped_column(Text,comment="游戏简介",default=None)
    company:Mapped[Optional[List[str]]] = mapped_column(JSON,default=None)
    category:Mapped[str] = mapped_column(String(50),default="other")
    cover:Mapped[str] = mapped_column(String(255),comment="封面")
    images:Mapped[Optional[List[str]]] = mapped_column(JSON,default=None)
    tag:Mapped[Optional[List[str]]] = mapped_column(JSON,default=None)

    views:Mapped[int] = mapped_column(Integer,default=0)
    likes:Mapped[int] = mapped_column(Integer,default=0)
    favorite:Mapped[int] = mapped_column(Integer,default=0)
    platfrom:Mapped[Optional[List[PlatformEnum]]] = mapped_column(JSON,default=[],comment="支持平台")
    
    __table_args__ = ()


