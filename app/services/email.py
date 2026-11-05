"""邮箱验证码发送。"""

from sqlalchemy.ext.asyncio import AsyncSession

from config.cache import rate_limit
from utils.email import send_email_code
from utils.responsed import Busy, info


class EmailService:
    def __init__(self, db: AsyncSession | None = None):
        self.db = db

    async def Send(self, email: str, ip: str, purpose: str = "register") -> dict:
        # 同一 IP 20 次/小时；同一邮箱 5 次/10 分钟
        if not await rate_limit(f"rl:email:ip:{ip}", 20, 3600):
            raise Busy("验证码发送过于频繁，请稍后再试")
        if not await rate_limit(f"rl:email:addr:{email}", 5, 600):
            raise Busy("该邮箱发送过于频繁，请稍后再试")

        ttl = await send_email_code(email, purpose)
        return info("验证码已发送，请检查邮箱", data={"expires_in": ttl})