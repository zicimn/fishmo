from pydantic import BaseModel, Field
from typing import List, Optional
from .user import UserInfo


class CommentItem(BaseModel):
    """评论响应模型：单条评论内容（含所属游戏 id）"""
    id: int
    content: Optional[str] = Field(default=None, max_length=2000)
    receive_id: int


class CommentItems(BaseModel):
    item: CommentItem
    account: UserInfo


class CommentList(BaseModel):
    total: int
    items: List[CommentItems]


class AddComment(BaseModel):
    """新增评论请求模型：仅 content，接收对象通过路由参数 game_id 传入"""
    content: Optional[str] = Field(default=None, min_length=1, max_length=2000)


class EditComment(BaseModel):
    """编辑评论请求模型：仅允许修改内容"""
    content: Optional[str] = Field(default=None, min_length=1, max_length=2000)
