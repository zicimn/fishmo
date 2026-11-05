from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        return value.strip()


class Account(BaseModel):
    username: str = Field(min_length=2, max_length=20)
    password: str = Field(min_length=6, max_length=64)
    email: EmailStr
    avatar: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=500)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("用户名不能为空")
        return value


class AccountUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=2, max_length=20)
    password: Optional[str] = Field(default=None, min_length=6, max_length=64)
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=500)

    @field_validator("username")
    @classmethod
    def strip_username(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else None


def to_user_private(user: Any) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
        "bio": user.bio,
        "is_admin": bool(user.is_admin),
        "created_at": user.created_at,
    }


def to_user_public(
    user: Any,
    *,
    gal_cnt: int = 0,
    article_cnt: int = 0,
    is_self: bool = False,
) -> dict:
    data = {
        "id": user.id,
        "username": user.username,
        "avatar": user.avatar,
        "bio": user.bio,
        "gal_cnt": gal_cnt,
        "article_cnt": article_cnt,
        "is_self": is_self,
        "created_at": user.created_at,
    }
    # 邮箱只对本人可见，避免个人主页公开联系方式
    if is_self:
        data["email"] = user.email
    return data


def to_account_brief(user: Any) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "avatar": user.avatar,
    }