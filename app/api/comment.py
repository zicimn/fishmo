from typing import Literal

from fastapi import APIRouter, Depends, Query

from deps import GetCommentService, GetCurrentUser
from models import User
from schemas.comment import AddComment, EditComment
from services import CommentService

router = APIRouter(prefix="/api/v1/comment", tags=["comment"])


@router.get("/user/{user_id}")
async def list_by_user(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    service: CommentService = Depends(GetCommentService),
):
    return await service.GetByUser(user_id, page, size)


@router.get("/{target_id}")
async def list_by_target(
    target_id: int,
    type: Literal["galgame", "article"] = Query("galgame"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    service: CommentService = Depends(GetCommentService),
):
    return await service.GetList(target_id, type, page, size)


@router.post("/add")
async def add(
    data: AddComment,
    game_id: int = Query(..., ge=1),
    type: Literal["galgame", "article"] = Query("galgame"),
    user: User = Depends(GetCurrentUser),
    service: CommentService = Depends(GetCommentService),
):
    return await service.Add(user.id, game_id, type, data)


@router.put("/edit")
async def edit(
    data: EditComment,
    comment_id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: CommentService = Depends(GetCommentService),
):
    return await service.Edit(user, comment_id, data)


@router.delete("/delete")
async def delete(
    comment_id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: CommentService = Depends(GetCommentService),
):
    return await service.Delete(user, comment_id)