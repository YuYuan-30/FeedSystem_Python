from uuid import uuid4

from redis.exceptions import RedisError

from app.core.redis import redis_client


def redis_lock_key(cache_key: str) -> str:
    """根据业务缓存 key 生成对应的锁 key，避免锁和真实缓存混在一起。"""
    return f"v1:lock:{cache_key}"


async def try_acquire_lock(lock_key: str, ttl_seconds: int) -> str | None:
    """尝试抢 Redis 分布式锁，成功时返回随机 token，失败或 Redis 异常时返回 None。"""
    token = uuid4().hex
    try:
        locked = await redis_client.set(lock_key, token, nx=True, ex=ttl_seconds)
    except RedisError:
        return None
    if not locked:
        return None
    return token


async def release_lock(lock_key: str, token: str) -> None:
    """释放 Redis 锁；Lua 脚本会先校验 token，避免误删其他请求后来抢到的锁。"""
    script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    end
    return 0
    """
    try:
        await redis_client.eval(script, 1, lock_key, token)
    except RedisError:
        return
