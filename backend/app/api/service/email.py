from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr
from utils.email import send_email
import random

router = APIRouter(prefix="/api/v1/email", tags=["Email"])

@router.post("/send")
async def send(email: EmailStr):
    await send_email(email)
    return {"message": "验证码已发送，请检查你的邮箱。"}