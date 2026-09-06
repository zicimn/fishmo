from pydantic import BaseModel, model_validator
from typing import List, Optional
from model.enums import PlatformEnum, CategoryEnum


class GalItem(BaseModel):
    id: int
    name: str
    cover: str
    views: int
    author: str
    # 作者头像可空：无头像的作者不能导致 Pydantic 校验 500
    avatar: Optional[str] = None
    # 作者 id：支持按用户过滤列表后，前端直接用于作者校验/管理入口判断
    author_id: Optional[int] = None


class GalList(BaseModel):
    total: int
    items: List[GalItem]


class AddGal(BaseModel):
    # 三个名称列在 DB 均为 NOT NULL，接口层保证至少一个名称非空，其余归一化为空串
    cn_name: Optional[str] = None
    jp_name: Optional[str] = None
    en_name: Optional[str] = None

    content: Optional[str] = None
    company: Optional[List[str]] = None
    category: Optional[CategoryEnum] = None
    cover: str
    images: Optional[List[str]] = None
    tag: Optional[List[str]] = None
    platfrom: Optional[List[PlatformEnum]] = None

    @model_validator(mode="after")
    def _ensure_at_least_one_name(self):
        # 数据库三列 NOT NULL 且无 server_default：必须保证至少一个名称非空，
        # 未提供的名称统一置空串，避免 NULL 入库触发 IntegrityError。
        if not any((self.cn_name, self.jp_name, self.en_name)):
            raise ValueError("cn_name / jp_name / en_name 至少填写一个")
        self.cn_name = self.cn_name or ""
        self.jp_name = self.jp_name or ""
        self.en_name = self.en_name or ""
        return self


class EditGal(BaseModel):

    cn_name: Optional[str] = None
    jp_name: Optional[str] = None
    en_name: Optional[str] = None

    content: Optional[str] = None
    company: Optional[List[str]] = None
    category: Optional[CategoryEnum] = None
    cover: Optional[str] = None
    images: Optional[List[str]] = None
    tag: Optional[List[str]] = None
    platfrom: Optional[List[PlatformEnum]] = None
