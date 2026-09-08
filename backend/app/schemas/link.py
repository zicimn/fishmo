from pydantic import BaseModel, Field
from typing import List, Optional
from .user import UserInfo


class LinkItem(BaseModel):
    """链接响应模型：单条链接信息（含审核状态与所属游戏 id）"""
    id: int
    url: str
    content: Optional[str] = None
    code: Optional[str] = None
    category: Optional[str] = None
    size: Optional[float] = None
    size_unit: Optional[str] = None
    status: bool
    # 所属游戏 id：按用户过滤的链接列表需要据此跳转到对应游戏/管理页
    game_id: int


class AddLink(BaseModel):
    """新增链接请求模型：服务端 add 时强制 status=True 直接公开，故请求体不含 status"""
    url: str = Field(min_length=1, max_length=255)
    content: Optional[str] = Field(default=None, max_length=255)
    code: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=255)
    size: Optional[float] = Field(default=None, ge=0)
    size_unit: Optional[str] = Field(default=None, pattern="^(KB|MB|GB)$")


class EditLink(BaseModel):
    """编辑链接请求模型：仅允许更新链接内容字段，全部可选"""
    content: Optional[str] = Field(default=None, max_length=255)
    code: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=255)
    size: Optional[float] = Field(default=None, ge=0)
    size_unit: Optional[str] = Field(default=None, pattern="^(KB|MB|GB)$")


class LinkItems(BaseModel):
    item: LinkItem
    account: UserInfo


class LinkList(BaseModel):
    total: int
    items: List[LinkItems]
