import asyncio
import random
from pydantic import EmailStr
from fastapi import HTTPException
from config.cache import get_cache_key,set_to_cache,delete_cache,get_from_cache
import resend
from config.security import RESEND_API_KEY

resend.api_key = RESEND_API_KEY

def get_email_cache_key(email: EmailStr) -> str:
    return get_cache_key("email_code", email)


async def clear_email(email:EmailStr):
    cache_key = get_email_cache_key(email)
    await delete_cache(cache_key)


async def send_email(email: EmailStr):

    code = str(random.randint(100000, 999999))
    cache_key = get_email_cache_key(email)
    #放置到redis里面
    await set_to_cache(cache_key, code, expire=300)

    try:
        params: resend.Emails.SendParams = {
            "from": "fishmo <noboard@fishmo.top>",
            "to": [email],
            "subject": "你的邮箱验证码",
            "html": f"""
                <h1>邮箱验证</h1>
                <p>你的验证码是：</p>
                <h2 style="color: blue;">{code}</h2>
                <p>该验证码 5 分钟内有效。</p>
            """,
        }
        # resend SDK 是同步实现（内部走 requests），不能直接 await，
        # 用 asyncio.to_thread 丢到线程池执行，避免阻塞事件循环。
        await asyncio.to_thread(resend.Emails.send, params)
        return {"message": "验证码已发送，请检查你的邮箱。"}
    except Exception as e:
        await delete_cache(cache_key) # 删除缓存中的验证码
        raise HTTPException(status_code=500, detail=f"发送验证码失败: {str(e)}")
    

async def verify_email_code(email: EmailStr, code: str) -> bool:
    cache_key = get_email_cache_key(email)
    cached_code = await get_from_cache(cache_key)

    if cached_code and cached_code == code:
        await delete_cache(cache_key)  # 验证成功后删除缓存中的验证码
        return True
    else:
        return False