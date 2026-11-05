from typing import Optional

from fastapi import APIRouter, Depends, Query

from deps import GetCurrentUser, GetFavoriteService, GetOptionalUser
from models import User
from services import FavoriteService

router = APIRouter(prefix="/api/v1/favorite", tags=["favorite"])


@router.post("/add")
async def add(
    gal_id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: FavoriteService = Depends(GetFavoriteService),
):
    return await service.Add(user.id, gal_id)


@router.delete("/remove")
async def remove(
    gal_id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: FavoriteService = Depends(GetFavoriteService),
):
    return await service.Remove(user.id, gal_id)


@router.get("/visit")
async def visit(
    gal_id: int = Query(..., ge=1, description="游戏 id"),
    viewer: Optional[User] = Depends(GetOptionalUser),
    service: FavoriteService = Depends(GetFavoriteService),
):
    return await service.Status(gal_id, viewer)


@router.get("/list")
async def get_list(
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=50),
    user: User = Depends(GetCurrentUser),
    service: FavoriteService = Depends(GetFavoriteService),
):
    return await service.GetList(user.id, page, size)