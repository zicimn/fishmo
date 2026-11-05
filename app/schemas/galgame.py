from typing import Any, List, Optional

from pydantic import BaseModel, Field, model_validator

from models.enums import CategoryEnum, PlatformEnum


class AddGal(BaseModel):
    name: Optional[str] = Field(default=None, max_length=50)
    cn_name: Optional[str] = Field(default=None, max_length=50)
    jp_name: Optional[str] = Field(default=None, max_length=50)
    en_name: Optional[str] = Field(default=None, max_length=50)

    content: Optional[str] = Field(default=None, max_length=20000)
    company: Optional[List[str]] = None
    category: Optional[CategoryEnum] = None
    cover: str
    images: Optional[List[str]] = None
    tag: Optional[List[str]] = None
    platfrom: Optional[List[PlatformEnum]] = None

    @model_validator(mode="after")
    def normalize_names(self):
        self.cn_name = (self.cn_name or "").strip()
        self.jp_name = (self.jp_name or "").strip()
        self.en_name = (self.en_name or "").strip()
        self.name = (self.name or "").strip()
        if not self.name:
            self.name = self.cn_name or self.jp_name or self.en_name
        if not self.name:
            raise ValueError("name / cn_name / jp_name / en_name 至少填写一个")
        return self


class EditGal(BaseModel):
    name: Optional[str] = Field(default=None, max_length=50)
    cn_name: Optional[str] = Field(default=None, max_length=50)
    jp_name: Optional[str] = Field(default=None, max_length=50)
    en_name: Optional[str] = Field(default=None, max_length=50)

    content: Optional[str] = Field(default=None, max_length=20000)
    company: Optional[List[str]] = None
    category: Optional[CategoryEnum] = None
    cover: Optional[str] = None
    images: Optional[List[str]] = None
    tag: Optional[List[str]] = None
    platfrom: Optional[List[PlatformEnum]] = None


def to_gal_item(
    *,
    gal_id: int,
    name: str,
    cover: str,
    views: int,
    author_id: int,
    author_name: str,
    author_avatar: Optional[str],
    category: Optional[str] = None,
    updated_at=None,
    status: bool = True,
) -> dict:
    return {
        "id": gal_id,
        "name": name,
        "cover": cover,
        "views": views or 0,
        "category": category,
        "status": bool(status),
        "author_id": author_id,
        "author": author_name,
        "avatar": author_avatar,
        "updated_at": updated_at,
    }


def to_gal_detail(
    gal: Any,
    *,
    author_name: str,
    author_avatar: Optional[str],
    views_total: int,
    is_favorited: bool = False,
) -> dict:
    return {
        "id": gal.id,
        "name": gal.name,
        "cn_name": gal.cn_name,
        "jp_name": gal.jp_name,
        "en_name": gal.en_name,
        "content": gal.content,
        "company": gal.company or [],
        "category": gal.category,
        "cover": gal.cover,
        "images": gal.images or [],
        "tag": gal.tag or [],
        "views": views_total,
        "likes": gal.likes or 0,
        "favorite": gal.favorite or 0,
        "is_favorited": is_favorited,
        "platfrom": gal.platfrom or [],
        "status": bool(gal.status),
        "author_id": gal.author_id,
        "author_name": author_name,
        "author_avatar": author_avatar,
        "created_at": gal.created_at,
        "updated_at": gal.updated_at,
    }


def to_admin_gal(
    gal: Any,
    *,
    author_name: str,
    author_avatar: Optional[str],
) -> dict:
    return {
        "id": gal.id,
        "name": gal.name,
        "cn_name": gal.cn_name,
        "jp_name": gal.jp_name,
        "en_name": gal.en_name,
        "cover": gal.cover,
        "category": gal.category,
        "views": gal.views or 0,
        "status": bool(gal.status),
        "author_id": gal.author_id,
        "author": author_name,
        "avatar": author_avatar,
        "created_at": gal.created_at,
        "updated_at": gal.updated_at,
    }