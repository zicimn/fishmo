import json
from typing import Optional, Any
import redis.asyncio as redis


redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    password=None,      # Redis 密码
    decode_responses=True,          # 自动解码为字符串
    encoding="utf-8",              # 编码格式
    max_connections=20,             # 连接池最大连接数
    socket_connect_timeout=5,       # 连接超时（秒）
    socket_timeout=5,               # 操作超时（秒）
    health_check_interval=30        # 健康检查间隔
)

async def get_search_version():
    v = await redis_client.get("search_version")
    return int(v or 0)


async def update_version():
    await redis_client.incr("search_version")


def get_cache_key(prefix:str,*args,version:int = None,**kwargs) -> str:
    key_parts = [prefix]

    if version is not None:
            key_parts.append(f"v{version}")

    key_parts.extend([str(arg) for arg in args])
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    return ":".join(key_parts)


async def get_from_cache(key: str) -> Optional[Any]:
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None


async def set_to_cache(key: str, value: Any, expire: int = 300) -> None:
    await redis_client.setex(key, expire, json.dumps(value, default=str))


async def delete_cache(key: str) -> None:
    await redis_client.delete(key)


async def delete_cache_pattern(pattern: str) -> None:
    async for key in redis_client.scan_iter(match=pattern):
        await redis_client.delete(key)
