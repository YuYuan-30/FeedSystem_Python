import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.core.redis import get_json_cache, set_json_cache
from app.core.redis_lock import redis_lock_key, release_lock, try_acquire_lock


async def get_json_with_cache_protection(
    cache_key: str,
    ttl_seconds: int,
    builder: Callable[[], Awaitable[Any]],
    lock_ttl_seconds: int = 3,
    wait_retries: int = 5,
    wait_seconds: float = 0.05,
) -> Any:
    """读取 JSON 缓存；未命中时用 Redis 锁保护回源，降低热门 key 击穿 MySQL 的风险。"""
    cached = await get_json_cache(cache_key)
    if cached is not None:
        return cached

    lock_key = redis_lock_key(cache_key)
    lock_token = await try_acquire_lock(lock_key, ttl_seconds=lock_ttl_seconds)
    if lock_token is not None:
        try:
            cached = await get_json_cache(cache_key)
            if cached is not None:
                return cached

            value = await builder()
            await set_json_cache(cache_key, value, ttl_seconds=ttl_seconds)
            return value
        finally:
            await release_lock(lock_key, lock_token)

    for _ in range(wait_retries):
        await asyncio.sleep(wait_seconds)
        cached = await get_json_cache(cache_key)
        if cached is not None:
            return cached

    return await builder()
