from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,or_
from config.db import get_db
from schemas.user import LoginRequest,Account
from model.user import User
from passlib.context import CryptContext
from jose import jwt,JWTError
from config.security import SECRET_KEY, ALGORITHM
from utils.email import verify_email_code

security = HTTPBearer()
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
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

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
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "bio": new_user.bio,
        "avatar": new_user.avatar
    }
