from typing import Literal

from fastapi import APIRouter, Depends, Query

from deps import GetSearchService
from services import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("/")
async def search(
    keyword: str = Query(..., min_length=1, max_length=50),
    search_type: Literal["name", "tag", "company"] = Query("name"),
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=50),
    service: SearchService = Depends(GetSearchService),
):
    return await service.Search(keyword, search_type, page, size)