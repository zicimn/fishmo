from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from deps import (
    GetAuthService,
    GetCurrentUser,
    GetOptionalUser,
    GetUserService,
    client_ip,
)
from models import User
from schemas.user import Account, AccountUpdate, LoginRequest
from services import AuthService, UserService
from utils.responsed import BadRequest, info
from utils.verify import TokenPayload, get_token_payload

router = APIRouter(prefix="/api/v1/user", tags=["user"])


@router.post("/login")
async def login(
    data: LoginRequest,
    request: Request,
    service: AuthService = Depends(GetAuthService),
):
    return await service.Login(data, client_ip(request))


@router.post("/register")
async def register(
    data: Account,
    request: Request,
    code: str = Query(..., min_length=6, max_length=6, description="邮箱验证码"),
    service: AuthService = Depends(GetAuthService),
):
    return await service.Register(data, code, client_ip(request))


@router.post("/logout")
async def logout(
    payload: TokenPayload = Depends(get_token_payload),
    service: AuthService = Depends(GetAuthService),
):
    return await service.Logout(payload)


@router.put("/update")
async def update(
    data: AccountUpdate,
    user: User = Depends(GetCurrentUser),
    service: UserService = Depends(GetUserService),
):
    return await service.UpdateProfile(user, data)


@router.delete("/delete")
async def delete(
    user: User = Depends(GetCurrentUser),
    service: UserService = Depends(GetUserService),
):
    return await service.DeleteAccount(user)


@router.get("/")
async def index(
    id: Optional[int] = Query(None, ge=1),
    viewer: Optional[User] = Depends(GetOptionalUser),
    service: UserService = Depends(GetUserService),
):
    target_id = id or (viewer.id if viewer else None)
    if target_id is None:
        raise BadRequest("请提供用户 id，或先登录")
    return await service.GetInfo(target_id, viewer)