"""
Day 6 亲手敲练习：Redis 锁与缓存防击穿。

练习方式：
1. 先读 day6_notes.md，确认你知道缓存击穿、double-check、Lua 安全解锁分别解决什么问题。
2. 再对照真实实现，把下面三个关键片段自己敲一遍。
3. 重点不是背 Redis 命令，而是能讲清“为什么只让一个请求回源 MySQL”。
"""


def practice_redis_lock_key() -> None:
    """练习 1：对照 redis_lock_key，理解为什么锁 key 要和业务缓存 key 分开。"""
    # 源码位置：`app/core/redis_lock.py` -> `redis_lock_key`
    # 调用位置：`app/core/cache_protector.py` -> `get_json_with_cache_protection`
    # 你可以自己敲一遍：
    # return f"v1:lock:{cache_key}"


async def practice_try_acquire_lock() -> None:
    """练习 2：对照 try_acquire_lock，理解 SET NX EX 如何表达“抢锁”。"""
    # 源码位置：`app/core/redis_lock.py` -> `try_acquire_lock`
    # 调用位置：`app/core/cache_protector.py` -> `get_json_with_cache_protection`
    # 你可以自己敲一遍：
    # token = uuid4().hex
    # locked = await redis_client.set(lock_key, token, nx=True, ex=ttl_seconds)
    # if not locked:
    #     return None
    # return token


async def practice_cache_protection_flow() -> None:
    """练习 3：对照 get_json_with_cache_protection，理解缓存 miss 后的保护式回源。"""
    # 源码位置：`app/core/cache_protector.py` -> `get_json_with_cache_protection`
    # 调用位置：`app/services/video_service.py` -> `VideoService.get_detail`
    # 你可以自己敲一遍：
    # cached = await get_json_cache(cache_key)
    # if cached is not None:
    #     return cached
    # lock_token = await try_acquire_lock(lock_key, ttl_seconds=3)
    # if lock_token is not None:
    #     try:
    #         cached = await get_json_cache(cache_key)
    #         if cached is not None:
    #             return cached
    #         value = await builder()
    #         await set_json_cache(cache_key, value, ttl_seconds=ttl_seconds)
    #         return value
    #     finally:
    #         await release_lock(lock_key, lock_token)
