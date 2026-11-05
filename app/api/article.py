from typing import Optional

from fastapi import APIRouter, Depends, Query

from deps import GetArticleService, GetCurrentUser, GetOptionalUser
from models import User
from schemas.article import ArticleEdit, ArticlePublish
from services import ArticleService

router = APIRouter(prefix="/api/v1/article", tags=["article"])


@router.get("/")
async def index(
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=50),
    category: Optional[str] = Query(None, max_length=50),
    service: ArticleService = Depends(GetArticleService),
):
    return await service.GetList(page, size, category)


@router.post("/add")
async def add(
    data: ArticlePublish,
    user: User = Depends(GetCurrentUser),
    service: ArticleService = Depends(GetArticleService),
):
    return await service.Create(user.id, data)


@router.delete("/delete")
async def delete(
    id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: ArticleService = Depends(GetArticleService),
):
    return await service.Delete(user.id, id)


@router.put("/edit")
async def edit(
    data: ArticleEdit,
    id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: ArticleService = Depends(GetArticleService),
):
    return await service.Update(user.id, id, data)


# 必须注册在 /{id} 之前
@router.get("/manage")
async def manage(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    user: User = Depends(GetCurrentUser),
    service: ArticleService = Depends(GetArticleService),
):
    return await service.Manage(user.id, page, size)


@router.get("/{id}")
async def visit(
    id: int,
    viewer: Optional[User] = Depends(GetOptionalUser),
    service: ArticleService = Depends(GetArticleService),
):
    return await service.GetId(id, viewer)