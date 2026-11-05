"""Redis 缓存、限流与 JWT 黑名单。

约定：
- 所有缓存 key 都带业务域版本号（``v{n}``），写操作只需自增版本号即可整体失效；
- Redis 不可用时缓存读写降级为“未命中/不写入”，限流与黑名单查询失败开放，
  避免缓存故障拖垮整个站点；登出写黑名单失败则关闭（由调用方报错）。
- 每次操作最多等待 2 秒；失败后熔断 30 秒，期间直接跳过 Redis。
"""

import asyncio
import json
import logging
import time
from typing import Any, Optional

import redis.asyncio as redis

from config.security import REDIS_DB, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT

logger = logging.getLogger(__name__)

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True,
    encoding="utf-8",
    max_connections=20,
    socket_connect_timeout=5,
    socket_timeout=5,
    health_check_interval=30,
)

# 业务域版本计数 key
SEARCH_VERSION_KEY = "search_version"
GAL_VERSION_KEY = "gal_version"
LINK_VERSION_KEY = "link_version"
COMMENT_VERSION_KEY = "comment_version"
ARTICLE_VERSION_KEY = "article_version"
USER_VERSION_KEY = "user_version"


# 单次 Redis 操作上限；连接被防火墙丢包时，TCP 超时可能远大于 socket_connect_timeout。
_REDIS_OP_TIMEOUT = 2.0
# 失败后熔断窗口：窗口内直接按“未命中”处理，避免每个请求都等超时。
_REDIS_RETRY_AFTER = 30.0
_redis_down_until = 0.0


async def _safe(coro_factory, fallback=None, action: str = "redis"):
    global _redis_down_until
    if time.monotonic() < _redis_down_until:
        return fallback
    try:
        return await asyncio.wait_for(coro_factory(), timeout=_REDIS_OP_TIMEOUT)
    except Exception as exc:  # noqa: BLE001 - 缓存故障需要整体降级
        _redis_down_until = time.monotonic() + _REDIS_RETRY_AFTER
        logger.warning("Redis %s 失败，%s 秒内跳过缓存：%s", action, int(_REDIS_RETRY_AFTER), exc)
        return fallback


async def redis_guard(coro_factory, fallback=None, action: str = "redis"):
    """供计数器、定时任务等模块复用：带超时与熔断的 Redis 操作。"""
    return await _safe(coro_factory, fallback=fallback, action=action)


async def get_version(name: str = SEARCH_VERSION_KEY) -> int:
    value = await _safe(lambda: redis_client.get(name), fallback=0, action="读取版本号")
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


# 兼容旧调用方
get_search_version = get_version


async def update_version(name: str = SEARCH_VERSION_KEY) -> None:
    await _safe(lambda: redis_client.incr(name), action="自增版本号")


def get_cache_key(prefix: str, *args, version: int = None, **kwargs) -> str:
    parts = [prefix]
    if version is not None:
        parts.append(f"v{version}")
    parts.extend(str(arg) for arg in args)
    parts.extend(f"{key}={value}" for key, value in sorted(kwargs.items()) if value is not None)
    return ":".join(parts)


async def get_from_cache(key: str) -> Optional[Any]:
    raw = await _safe(lambda: redis_client.get(key), fallback=None, action="读取缓存")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        logger.warning("缓存内容不是合法 JSON，已忽略：%s", key)
        return None


async def set_to_cache(key: str, value: Any, expire: int = 300) -> None:
    payload = json.dumps(value, ensure_ascii=False, default=str)
    await _safe(
        lambda: redis_client.setex(key, expire, payload),
        action="写入缓存",
    )


async def delete_cache(key: str) -> None:
    await _safe(lambda: redis_client.delete(key), action="删除缓存")


async def delete_cache_pattern(pattern: str) -> None:
    async def _delete():
        async for key in redis_client.scan_iter(match=pattern, count=200):
            await redis_client.delete(key)

    await _safe(_delete, action="批量删除缓存")


# ---------------------------------------------------------------------------
# 固定窗口限流：INCR + EXPIRE，失败开放（返回 True）
# ---------------------------------------------------------------------------

_RATE_LIMIT_LUA = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""


async def rate_limit(key: str, limit: int, window: int) -> bool:
    """返回 True 表示放行，False 表示超限。Redis 不可用时放行。"""

    async def _run():
        current = await redis_client.eval(_RATE_LIMIT_LUA, 1, key, window)
        return int(current) <= limit

    result = await _safe(_run, fallback=True, action="限流")
    return bool(result)


# ---------------------------------------------------------------------------
# JWT 黑名单：登出时把 jti 写入 Redis，TTL 与 token 剩余有效期一致
# ---------------------------------------------------------------------------


def _blacklist_key(jti: str) -> str:
    return f"token_blacklist:{jti}"


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    # 故意不使用 _safe：登出必须确保 token 真正失效（失败关闭）
    await asyncio.wait_for(
        redis_client.setex(_blacklist_key(jti), max(1, ttl_seconds), "1"),
        timeout=_REDIS_OP_TIMEOUT,
    )


async def is_token_blacklisted(jti: str) -> bool:
    value = await _safe(
        lambda: redis_client.exists(_blacklist_key(jti)),
        fallback=0,
        action="查询 token 黑名单",
    )
    return bool(value)