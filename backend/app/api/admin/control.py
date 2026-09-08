from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config.db import get_db
from utils.verify_user import verify_admin
from model.galgame import Galgame 
from schemas.galgame import GalBaseList,GalBase

router = APIRouter(prefix="/api/admin/control", tags=["admin_control"]) 
security = HTTPBearer(auto_error=False)

@router.get("/BrowseGal")
async def admin_control(
    page: int = Query(1,ge = 1),
    size: int = Query(10,ge = 1),
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    identity = verify_admin(credentials)
    if identity is False:
        raise HTTPException(status_code=403, detail="无权限访问")

    query = await db.execute(
        select(Galgame.id,Galgame.cn_name, Galgame.en_name, Galgame.id, Galgame.jp_name,Galgame.cover)
        .where(Galgame.status == 0)
        .order_by(Galgame.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    rows = query.all()

    items = []
    for id,cn_name,en_name,jp_name,cover in rows:
        name = cn_name or en_name or jp_name
        items.append(GalBase(id=id,name=name,cover=cover))

    data = GalBaseList(total=len(items),items=items)
    return data