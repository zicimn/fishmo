from fastapi import APIRouter, Depends, Query, Request
from pydantic import EmailStr

from deps import GetEmailService, client_ip
from services import EmailService

router = APIRouter(prefix="/api/v1/email", tags=["email"])


@router.post("/send")
async def send(
    email: EmailStr,
    request: Request,
    purpose: str = Query("register", pattern="^(register|reset)$"),
    service: EmailService = Depends(GetEmailService),
):
    return await service.Send(str(email), client_ip(request), purpose)