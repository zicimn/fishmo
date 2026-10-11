from pydantic import BaseModel, Field
from typing import List, Optional
from .user import UserInfo


class CommentItem(BaseModel):
    """评论响应模型：单条评论内容"""
    id: int
    content: Optional[str] = Field(default=None, max_length=2000)
    receive_id: int
    parent_id: Optional[int] = None
    reply_to_id: Optional[int] = None


class CommentItems(BaseModel):
    """评论条目：评论内容 + 作者信息"""
    item: CommentItem
    account: UserInfo
    # 被回复用户信息（仅子评论有值）
    reply_to_account: Optional[UserInfo] = None


class NestedCommentItems(BaseModel):
    """嵌套评论条目：顶级评论 + 其子评论列表"""
    item: CommentItem
    account: UserInfo
    replies: List[CommentItems] = []
    reply_count: int = 0


class CommentList(BaseModel):
    """评论列表响应模型"""
    total: int
    items: List[NestedCommentItems]


class UserCommentList(BaseModel):
    """用户评论列表响应模型（扁平结构，不含嵌套）"""
    total: int
    items: List[CommentItems]


class AddComment(BaseModel):
    """新增评论请求模型"""
    content: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    # 父评论 ID：为 None 时表示发布顶级评论
    parent_id: Optional[int] = Field(default=None, description="父评论id，None 表示顶级评论")
    # 被回复用户 ID：用于前端展示"@某人"
    reply_to_id: Optional[int] = Field(default=None, description="被回复用户id")


class EditComment(BaseModel):
    """编辑评论请求模型：仅允许修改内容"""
    content: Optional[str] = Field(default=None, min_length=1, max_length=2000)
