from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


def _coerce_category(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return ",".join(str(item).strip() for item in value if str(item).strip())
    return str(value)


class ArticlePublish(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    cover: Optional[str] = None
    tag: Optional[List[str]] = None
    category: Optional[str] = None
    images: Optional[List[str]] = None

    @field_validator("category", mode="before")
    @classmethod
    def coerce_category(cls, value: Any) -> Optional[str]:
        return _coerce_category(value)


class ArticleEdit(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, min_length=1)
    cover: Optional[str] = None
    tag: Optional[List[str]] = None
    category: Optional[str] = None
    images: Optional[List[str]] = None

    @field_validator("category", mode="before")
    @classmethod
    def coerce_category(cls, value: Any) -> Optional[str]:
        return _coerce_category(value)


def split_category(value: Optional[str]) -> List[str]:
    return [item for item in (value or "").split(",") if item]


def to_article_preview(
    *,
    article_id: int,
    title: str,
    cover: str,
    category: Optional[str],
    views: int,
    comment_count: int,
    created_at,
    author_id: int,
    author_name: str,
    author_avatar: Optional[str],
) -> dict:
    return {
        "id": article_id,
        "title": title,
        "cover": cover,
        "category": split_category(category),
        "views": views or 0,
        "comcnt": comment_count or 0,
        "created_at": created_at,
        "time": created_at,
        "author_id": author_id,
        "author": author_name,
        "avatar": author_avatar,
    }


def to_article_detail(
    article: Any,
    *,
    author: Any,
    views_total: int,
    comment_count: int,
) -> dict:
    return {
        "id": article.id,
        "title": article.title,
        "content": article.content,
        "cover": article.cover,
        "tag": article.tag or [],
        "category": split_category(article.category),
        "images": article.images or [],
        "views": views_total,
        "status": bool(article.status),
        "author_id": article.author_id,
        "author_name": author.username,
        "author_avatar": author.avatar,
        "comment_count": comment_count,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
    }


def to_article_manage(article: Any) -> dict:
    return {
        "id": article.id,
        "title": article.title,
        "cover": article.cover,
        "category": split_category(article.category),
        "views": article.views or 0,
        "status": bool(article.status),
        "created_at": article.created_at,
        "updated_at": article.updated_at,
    }


def to_admin_article(article: Any, *, author: Any) -> dict:
    return {
        "id": article.id,
        "title": article.title,
        "cover": article.cover,
        "category": split_category(article.category),
        "views": article.views or 0,
        "status": bool(article.status),
        "author_id": article.author_id,
        "author": author.username,
        "avatar": author.avatar,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
    }