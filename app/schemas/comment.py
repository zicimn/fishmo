from typing import Any, Optional

from pydantic import BaseModel, Field


class AddComment(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    parent_id: Optional[int] = Field(default=None, description="父评论 id，None 表示顶级评论")
    reply_to_id: Optional[int] = Field(default=None, description="被回复评论的 id")


class EditComment(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


def to_comment_item(
    comment: Any,
    *,
    author: Any,
    reply_to_username: Optional[str] = None,
) -> dict:
    return {
        "id": comment.id,
        "content": comment.content,
        "receive_id": comment.receive_id,
        "receive_type": comment.receive_type,
        "parent_id": comment.parent_id,
        "reply_to_id": comment.reply_to_id,
        "reply_to_username": reply_to_username,
        "author_id": comment.author_id,
        "author": {
            "id": author.id,
            "username": author.username,
            "avatar": author.avatar,
        },
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
    }