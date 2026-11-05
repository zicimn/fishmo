from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class AddLink(BaseModel):
    url: str = Field(min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, max_length=255)
    code: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=255)
    size: Optional[float] = Field(default=None, ge=0)
    size_unit: Optional[str] = Field(default=None, pattern="^(KB|MB|GB)$")

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("链接必须以 http:// 或 https:// 开头")
        return value


class EditLink(BaseModel):
    content: Optional[str] = Field(default=None, max_length=255)
    code: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=255)
    size: Optional[float] = Field(default=None, ge=0)
    size_unit: Optional[str] = Field(default=None, pattern="^(KB|MB|GB)$")


def to_link_item(link: Any, *, author: Any) -> dict:
    return {
        "id": link.id,
        "url": link.url,
        "content": link.content,
        "code": link.code,
        "category": link.category,
        "size": link.size,
        "size_unit": link.size_unit.value if link.size_unit else None,
        "status": bool(link.status),
        "game_id": link.game_id,
        "author_id": link.author_id,
        "author": {
            "id": author.id,
            "username": author.username,
            "avatar": author.avatar,
        },
        "created_at": link.created_at,
        "updated_at": link.updated_at,
    }