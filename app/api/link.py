from fastapi import APIRouter, Depends, Query

from deps import GetCurrentUser, GetLinkService
from models import User
from schemas.link import AddLink, EditLink
from services import LinkService

router = APIRouter(prefix="/api/v1/link", tags=["link"])


@router.get("/user/{user_id}")
async def list_by_user(
    user_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    service: LinkService = Depends(GetLinkService),
):
    return await service.GetByUser(user_id, page, size)


@router.get("/{game_id}")
async def list_by_game(
    game_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    service: LinkService = Depends(GetLinkService),
):
    return await service.GetByGame(game_id, page, size)


@router.post("/add")
async def add(
    data: AddLink,
    game_id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: LinkService = Depends(GetLinkService),
):
    return await service.Add(user.id, game_id, data)


@router.put("/review")
async def review(
    data: EditLink,
    link_id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: LinkService = Depends(GetLinkService),
):
    return await service.Update(user.id, link_id, data)


@router.delete("/delete")
async def delete(
    link_id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: LinkService = Depends(GetLinkService),
):
    return await service.Delete(user.id, link_id)