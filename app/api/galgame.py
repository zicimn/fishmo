from typing import Optional

from fastapi import APIRouter, Depends, Query

from deps import GetCurrentUser, GetGalgameService, GetOptionalUser
from models import CategoryEnum, PlatformEnum, User
from schemas.galgame import AddGal, EditGal
from services import GalgameService

router = APIRouter(prefix="/api/v1/galgame", tags=["galgame"])


@router.get("/")
async def index(
    category: Optional[CategoryEnum] = Query(None),
    platform: Optional[PlatformEnum] = Query(None),
    author_id: Optional[int] = Query(None, ge=1),
    keyword: Optional[str] = Query(None, max_length=50),
    sort: str = Query("updated_at"),
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=50),
    viewer: Optional[User] = Depends(GetOptionalUser),
    service: GalgameService = Depends(GetGalgameService),
):
    return await service.GetList(
        page=page,
        size=size,
        category=category.value if category else None,
        platform=platform.value if platform else None,
        author_id=author_id,
        keyword=keyword,
        sort=sort,
        viewer=viewer,
    )


# 必须注册在 /{id} 之前，否则 "rvisit" 会被当作 id
@router.get("/rvisit")
async def random_visit(service: GalgameService = Depends(GetGalgameService)):
    return await service.Random()


@router.post("/add")
async def add(
    data: AddGal,
    user: User = Depends(GetCurrentUser),
    service: GalgameService = Depends(GetGalgameService),
):
    return await service.Create(user.id, data)


@router.delete("/delete")
async def delete(
    id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: GalgameService = Depends(GetGalgameService),
):
    return await service.Delete(user.id, id)


@router.put("/edit")
async def edit(
    data: EditGal,
    id: int = Query(..., ge=1),
    user: User = Depends(GetCurrentUser),
    service: GalgameService = Depends(GetGalgameService),
):
    return await service.Update(user.id, id, data)


@router.get("/{id}")
async def visit(
    id: int,
    viewer: Optional[User] = Depends(GetOptionalUser),
    service: GalgameService = Depends(GetGalgameService),
):
    return await service.GetId(id, viewer)