import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select,update,delete,func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from config.db import get_db
from utils.verify_user import verify_admin
from model.galgame import Galgame
from config.cache import delete_cache_pattern, update_version, GAL_VERSION_KEY,delete_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/control", tags=["admin_control"]) 
security = HTTPBearer(auto_error=False)

@router.get("/BrowseGal")
async def admin_control(
    page: int = Query(1,ge = 1),
    size: int = Query(10,ge = 1),
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    identity = verify_admin(credentials = credentials)
    if identity is False:
        raise HTTPException(status_code=403, detail="无权限访问")

    query = await db.execute(
        select(Galgame.id)
        .where(Galgame.status == 0)
        .order_by(Galgame.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    rows = query.all()

    cnt = await db.execute(
        select(func.count(Galgame.id)).select_from(Galgame).where(Galgame.status == 0)
    )
    total = cnt.scalar() or 0

    return {
        "message": "获取成功",
        "total": total,
        "data": [r[0] for r in rows]
    }


@router.put("/UpdateStatus")
async def update_status(
    gal_id: int,
    status : bool,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    identity = verify_admin(credentials = credentials)
    if identity is False:
        raise HTTPException(status_code=403, detail="无权限访问")

    try:
        update_query = await db.execute(
            update(Galgame)
            .where(Galgame.id == gal_id)
            .values(status=status)
        )
        await db.commit()
    except Exception as e:
        logger.exception("更新游戏状态出错: gal_id=%s, status=%s", gal_id, status)
        raise HTTPException(status_code=500, detail="更新状态时发生错误")

    # 无论通过还是拒绝，状态变更后都必须使缓存失效
    await delete_cache_pattern("Galgame:*")
    await delete_cache_pattern(f"Gal_visit:*id={gal_id}*")
    await update_version(GAL_VERSION_KEY)

    return {
        "message": "已通过该游戏" if status else "已拒绝该游戏",
        "gal_id": gal_id,
        "status": status
    }


@router.delete("/DeleteGal")
async def delete_gal(
    gal_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    identity = verify_admin(credentials = credentials)
    if identity is False:
        raise HTTPException(status_code=403, detail="无权限访问")

    try:
        delete_query = await db.execute(
            delete(Galgame).where(Galgame.id == gal_id)
        )
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="该游戏存在关联数据，无法删除")
    except Exception as e:
        logger.exception("管理员删除游戏出错: gal_id=%s", gal_id)
        raise HTTPException(status_code=500, detail="删除游戏时发生错误")

    await delete_cache_pattern("Galgame:*")
    await delete_cache_pattern(f"Gal_visit:*id={gal_id}")
    await delete_cache(f"gal_views:{gal_id}")
    await delete_cache_pattern(f"links:*game_id={gal_id}")
    await update_version(GAL_VERSION_KEY)

    return {
        "message": "已删除该游戏",
        "gal_id": gal_id
    }