from typing import Optional

from fastapi import APIRouter, Depends, Query

from deps import GetAdminService, GetAdminUser
from models import User
from services import AdminService

router = APIRouter(prefix="/api/admin/control", tags=["admin"])


@router.get("/BrowseGal")
async def browse_gal(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    status: str = Query("pending", pattern="^(pending|published|all)$"),
    _: User = Depends(GetAdminUser),
    service: AdminService = Depends(GetAdminService),
):
    return await service.BrowseGames(page, size, status)


@router.put("/UpdateStatus")
async def update_status(
    gal_id: int = Query(..., ge=1),
    status: bool = Query(...),
    _: User = Depends(GetAdminUser),
    service: AdminService = Depends(GetAdminService),
):
    return await service.UpdateGameStatus(gal_id, status)


@router.delete("/DeleteGal")
async def delete_gal(
    gal_id: int = Query(..., ge=1),
    _: User = Depends(GetAdminUser),
    service: AdminService = Depends(GetAdminService),
):
    return await service.DeleteGame(gal_id)


@router.get("/Stats")
async def stats(
    _: User = Depends(GetAdminUser),
    service: AdminService = Depends(GetAdminService),
):
    return await service.Stats()


@router.get("/Users")
async def users(
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=50),
    keyword: Optional[str] = Query(None, max_length=50),
    _: User = Depends(GetAdminUser),
    service: AdminService = Depends(GetAdminService),
):
    return await service.Users(page, size, keyword)


@router.put("/UserStatus")
async def update_user_status(
    user_id: int = Query(..., ge=1),
    status: bool = Query(...),
    admin: User = Depends(GetAdminUser),
    service: AdminService = Depends(GetAdminService),
):
    return await service.UpdateUserStatus(admin, user_id, status)


@router.get("/Articles")
async def articles(
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=50),
    status: str = Query("all", pattern="^(all|published|hidden)$"),
    _: User = Depends(GetAdminUser),
    service: AdminService = Depends(GetAdminService),
):
    return await service.BrowseArticles(page, size, status)


@router.put("/UpdateArticleStatus")
async def update_article_status(
    article_id: int = Query(..., ge=1),
    status: bool = Query(...),
    _: User = Depends(GetAdminUser),
    service: AdminService = Depends(GetAdminService),
):
    return await service.UpdateArticleStatus(article_id, status)


@router.delete("/DeleteArticle")
async def delete_article(
    article_id: int = Query(..., ge=1),
    _: User = Depends(GetAdminUser),
    service: AdminService = Depends(GetAdminService),
):
    return await service.DeleteArticle(article_id)