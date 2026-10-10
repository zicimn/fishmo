from pydantic import BaseModel, Field, field_validator
from typing import Any, List, Optional
from .user import UserInfo
from datetime import datetime


class ArticleItem(BaseModel):
    id: int
    title: str
    cover: str
    category: str
    comcnt: int
    views: int
    time: datetime


class ArticleList(BaseModel):
    total: int
    items: List[ArticleItem]


class ArticlePublish(BaseModel):
    title: str
    content: str
    cover: Optional[str] = None
    tag: Optional[List[str]] = None
    category: Optional[str] = None
    images: Optional[List[str]] = None

    @field_validator("category", mode="before")
    @classmethod
    def coerce_category(cls, v: Any) -> Optional[str]:
        """
        将前端发来的列表（string[]）转为逗号分隔字符串，与 ORM String(255) 兼容。
        mode='before' 在 Pydantic 类型校验前执行，确保以下输入均可接受：
          - []           → ""（空字符串）
          - ["评测"]      → "评测"
          - ["评测","攻略"] → "评测,攻略"
          - None / 未传   → None（调用层再 fallback 为 ""）
          - "评测"        → "评测"（直接字符串，兼容已有调用方）
        """
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            return ",".join(v)
        return str(v)


class ArticleDetail(BaseModel):
    id: int
    title: str
    content: str
    cover: Optional[str] = None
    tag: Optional[List[str]] = None
    category: List[str]
    images: Optional[List[str]] = None
    views: int
    author_id: int
    author_name: str
    author_avatar: Optional[str] = None
    comment_count: int
    created_at: datetime
    updated_at: datetime


class ArticleManageItem(BaseModel):
    id: int
    title: str
    cover: str


class ArticleManageList(BaseModel):
    total: int
    items: List[ArticleManageItem]