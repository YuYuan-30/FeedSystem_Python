from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import get_settings


settings = get_settings()

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


def token_cache_key(account_id: int) -> str:
    """生成账号当前 access token 的 Redis key，方便统一管理 key 命名。"""
    return f"v1:account:{account_id}"


async def cache_access_token(account_id: int, token: str) -> None:
    """把当前有效 access token 写入 Redis，TTL 与 access token 过期时间保持一致。"""
    ttl_seconds = settings.access_token_minutes * 60
    try:
        await redis_client.set(token_cache_key(account_id), token, ex=ttl_seconds)
    except RedisError:
        # Redis 是性能层，不是数据真相；写缓存失败时让主流程继续走 MySQL。
        return


async def get_cached_access_token(account_id: int) -> str | None:
    """从 Redis 读取账号当前有效 access token，读不到或 Redis 异常时返回 None。"""
    try:
        return await redis_client.get(token_cache_key(account_id))
    except RedisError:
        return None


async def delete_cached_access_token(account_id: int) -> None:
    """登出或刷新登录态时删除 Redis 中的旧 access token。"""
    try:
        await redis_client.delete(token_cache_key(account_id))
    except RedisError:
        return


async def close_redis() -> None:
    """应用关闭时释放 Redis 连接，避免开发环境 reload 后残留连接。"""
    await redis_client.aclose()
