"""邮箱验证码：Redis 存储 + Resend 发送。"""

import asyncio
import logging
import random
from typing import Optional

import resend
from pydantic import EmailStr

from config.cache import delete_cache, get_cache_key, get_from_cache, set_to_cache
from config.security import RESEND_API_KEY, RESEND_FROM
from utils.responsed import AppError

logger = logging.getLogger(__name__)
resend.api_key = RESEND_API_KEY

CODE_TTL = 300


def get_email_cache_key(email: EmailStr | str, purpose: str = "register") -> str:
    return get_cache_key("email_code", purpose, email)


async def clear_email(email: EmailStr | str, purpose: str = "register") -> None:
    await delete_cache(get_email_cache_key(email, purpose))


async def send_email_code(
    email: EmailStr | str,
    purpose: str = "register",
) -> int:
    """生成并发送验证码，返回有效期秒数。"""
    code = str(random.randint(100000, 999999))
    cache_key = get_email_cache_key(email, purpose)
    await set_to_cache(cache_key, code, expire=CODE_TTL)

    subject = "你的邮箱验证码"
    params: resend.Emails.SendParams = {
        "from": RESEND_FROM,
        "to": [str(email)],
        "subject": subject,
        "html": f"""
            <div style="font-family:system-ui,sans-serif;line-height:1.7">
              <h2>邮箱验证</h2>
              <p>你的验证码是：</p>
              <p style="font-size:28px;font-weight:700;letter-spacing:6px;color:#0ea5e9">{code}</p>
              <p>该验证码 5 分钟内有效。若非本人操作，请忽略此邮件。</p>
            </div>
        """,
    }

    try:
        # Resend SDK 是同步实现，丢线程池避免阻塞事件循环
        await asyncio.to_thread(resend.Emails.send, params)
    except Exception as exc:  # noqa: BLE001
        logger.exception("发送验证码失败：%s", exc)
        await delete_cache(cache_key)
        raise AppError("验证码发送失败，请稍后重试")

    return CODE_TTL


async def verify_email_code(
    email: EmailStr | str,
    code: str,
    purpose: str = "register",
) -> bool:
    cached_code: Optional[str] = await get_from_cache(get_email_cache_key(email, purpose))
    if not cached_code or str(cached_code) != str(code).strip():
        return False
    await delete_cache(get_email_cache_key(email, purpose))
    return True