import json
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import get_settings


settings = get_settings()

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


def token_cache_key(account_id: int) -> str:
    """生成账号当前 access token 的 Redis key，方便统一管理 key 命名。"""
    return f"v1:account:{account_id}"


def video_detail_cache_key(video_id: int) -> str:
    """生成视频详情缓存 key，详情页读多写少，适合做 Cache-Aside。"""
    return f"v1:video:detail:{video_id}"


def feed_latest_cache_key(limit: int, latest_time: int, viewer_id: int | None) -> str:
    """生成最新 Feed 缓存 key；viewer_id 用来区分 is_liked 这类个性化字段。"""
    viewer_part = viewer_id or 0
    return f"v1:feed:latest:viewer={viewer_part}:limit={limit}:before={latest_time}"


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


async def get_json_cache(key: str) -> Any | None:
    """读取 JSON 缓存；Redis 异常或 JSON 损坏时都当作缓存未命中。"""
    try:
        raw = await redis_client.get(key)
    except RedisError:
        return None
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def set_json_cache(key: str, value: Any, ttl_seconds: int) -> None:
    """写入 JSON 缓存；失败时不影响主流程，因为 MySQL 才是数据真相。"""
    try:
        await redis_client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl_seconds)
    except (RedisError, TypeError):
        return


async def delete_cache_key(key: str) -> None:
    """删除单个缓存 key，用于写操作后的缓存失效。"""
    try:
        await redis_client.delete(key)
    except RedisError:
        return


async def delete_cache_prefix(prefix: str) -> None:
    """按前缀删除缓存 key，用于发布视频后清理最新 Feed 这类列表缓存。"""
    try:
        keys = [key async for key in redis_client.scan_iter(f"{prefix}*")]
        if keys:
            await redis_client.delete(*keys)
    except RedisError:
        return


async def close_redis() -> None:
    """应用关闭时释放 Redis 连接，避免开发环境 reload 后残留连接。"""
    await redis_client.aclose()
