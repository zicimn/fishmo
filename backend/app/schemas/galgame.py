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
    name: Optional[str] = None
    # 三个名称列保留兼容，可选
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
    def _normalize_names(self):
        # 三列 NOT NULL 兜底空串，避免 NULL 入库触发 IntegrityError
        self.cn_name = self.cn_name or ""
        self.jp_name = self.jp_name or ""
        self.en_name = self.en_name or ""
        # name 优先用前端传入的值，否则从三名称派生
        if not self.name:
            self.name = self.cn_name or self.jp_name or self.en_name or ""
        if not self.name:
            raise ValueError("name / cn_name / jp_name / en_name 至少填写一个")
        return self


class EditGal(BaseModel):
    name: Optional[str] = None
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


class GalBase(BaseModel):
    id: int  # W2: 前端跳转需要游戏 id
    name: str
    cover: str


class GalBaseList(BaseModel):
    total: int  # W2: 列表总数
    items: List[GalBase]