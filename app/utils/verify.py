"""JWT 与密码哈希。

- JWT 有效期 7 天，载荷含 ``jti``，登出后写入 Redis 黑名单；
- 登录时对不存在的账号也执行一次 argon2 校验，抹平时序差异；
- 管理员身份不写进 token，每次请求回库判定。
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config.security import ALGORITHM, SECRET_KEY, TOKEN_EXPIRE_DAYS
from utils.responsed import Unauthorized

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# 账号不存在时用于比对，避免“用户不存在”响应明显更快而被枚举
DUMMY_PASSWORD_HASH = pwd_context.hash("fishmo-timing-equalization-placeholder")


@dataclass(frozen=True)
class TokenPayload:
    user_id: int
    username: str
    jti: str
    exp: datetime

    def remaining_seconds(self) -> int:
        return max(0, int((self.exp - datetime.now(timezone.utc)).total_seconds()))


async def hash_password(plain: str) -> str:
    return await run_in_threadpool(pwd_context.hash, plain)


async def verify_password(plain: str, hashed: str) -> bool:
    return await run_in_threadpool(pwd_context.verify, plain, hashed)


def create_access_token(user_id: int, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "jti": uuid4().hex,
        "iat": now,
        "exp": now + timedelta(days=TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
        username = str(payload.get("username", ""))
        jti = str(payload["jti"])
        exp_ts = payload.get("exp")
        if exp_ts is None:
            raise ValueError("token 缺少 exp")
        exp = datetime.fromtimestamp(float(exp_ts), tz=timezone.utc)
    except (JWTError, KeyError, TypeError, ValueError):
        raise Unauthorized("登录状态无效，请重新登录")

    # 延迟导入，避免 config ← utils 循环依赖
    from config.cache import is_token_blacklisted

    if await is_token_blacklisted(jti):
        raise Unauthorized("登录已失效，请重新登录")

    return TokenPayload(user_id=user_id, username=username, jti=jti, exp=exp)


async def get_token_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenPayload:
    if credentials is None:
        raise Unauthorized("请先登录")
    return await decode_token(credentials.credentials)


async def try_decode_credentials(
    credentials: Optional[HTTPAuthorizationCredentials],
) -> Optional[TokenPayload]:
    """可选鉴权：无 token 或 token 无效都返回 None。"""
    if credentials is None:
        return None
    try:
        return await decode_token(credentials.credentials)
    except Unauthorized:
        return None