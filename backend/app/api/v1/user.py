from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from config.db import get_db
from schemas.user import LoginRequest, Account, AccountUpdate
from model.user import User
from passlib.context import CryptContext
from jose import jwt, JWTError
from config.security import SECRET_KEY, ALGORITHM
from utils.email import verify_email_code
from utils.verify_user import verify_login
from config.cache import update_version
from utils.webp import upload_image_to_cloudinary

# auto_error=False：缺 token 时走 verify_login 统一返回 401，与无效 token 语义一致
security = HTTPBearer(auto_error=False)
router = APIRouter(prefix="/api/v1/user", tags=["User"])
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


@router.post("/login")
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(data.password, user.password_hash):
        raise HTTPException(status_code = 401, detail = "用户名或密码不正确")

    token = jwt.encode(
        {"sub": str(user.id), "username": user.username},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return{
        "msg":"用户登录信息",
        "id" : user.id,
        "username": user.username,
        "access_token": token
    }


@router.post("/register")
async def register(
    data: Account,
    code: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User)
        .where(
            or_(User.username == data.username, User.email == data.email)
        ))
    
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在")

    ok = await verify_email_code(data.email, code)
    if not ok:
        raise HTTPException(status_code=400, detail="验证码不正确或已过期")

    hashed_password = pwd_context.hash(data.password)
    new_user = User(
        username = data.username,
        password_hash = hashed_password,
        email = data.email,
        bio = data.bio,
        avatar = data.avatar
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "msg":"用户注册信息",
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "bio": new_user.bio,
        "avatar": new_user.avatar
    }


@router.put("/update")
async def update(
    data: AccountUpdate,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if data.username:
        existing = await db.execute(select(User).where(User.username == data.username, User.id != user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="用户名已存在")
        user.username = data.username

    if data.email:
        existing = await db.execute(select(User).where(User.email == data.email, User.id != user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="邮箱已存在")
        user.email = data.email

    if data.bio is not None:
        user.bio = data.bio

    if data.avatar:
        # Cloudinary 上传是同步 HTTP + PIL 解码（CPU 密集），丢到线程池避免阻塞事件循环
        result = await run_in_threadpool(upload_image_to_cloudinary, data.avatar)
        if not result or not result.get("status"):
            raise HTTPException(status_code=422, detail="头像上传失败")
        user.avatar = result["url"]

    if data.password:
        user.password_hash = await run_in_threadpool(pwd_context.hash, data.password)

    try:
        await db.commit()
    except IntegrityError:
        # 并发下唯一性查重可能漏判，由唯一索引兜底
        await db.rollback()
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
    await db.refresh(user)
    await update_version()

    return {
        "msg": "用户信息更新成功",
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "bio": user.bio,
        "avatar": user.avatar
    }
    

@router.delete("/delete")
async def delete(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    user_id = verify_login(credentials=credentials)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.delete(user)
    await db.commit()
    await update_version()

    return {
        "msg": "用户已删除",
        "id": user.id,
        "username": user.username
    }


@router.get("/")
async def index(
    id:Optional[int] = None,
    credentials:Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    if not id and not credentials:
        raise HTTPException(status_code=400,detail="参数错误")

    if not id and credentials:
        id = verify_login(credentials=credentials)

    result = await db.execute(
        select(User)
        .where(User.id == id)
    )
    user = result.one_or_none()
    if not user:
        raise HTTPException(status_code=404,detail="用户不存在")

    return{
        "msg": "用户信息",
        "username" :user.username,
        "avatar" :user.avatar,
        "bio" :user.bio,
        "email" : user.email
    }
    


        
    