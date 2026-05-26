from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from redis.exceptions import RedisError

from app.core.auth import CurrentUser, get_current_user
from app.core.redis import redis_client


def rate_limit_key(scope: str, subject: str) -> str:
    """生成限流 Redis key，scope 表示业务场景，subject 表示被限制的对象。"""
    return f"v1:ratelimit:{scope}:{subject}"


def get_client_ip(request: Request) -> str:
    """从请求中提取客户端 IP；本地开发时通常会是 127.0.0.1。"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    if request.client is None:
        return "unknown"
    return request.client.host


async def allow_request(scope: str, subject: str, limit: int, window_seconds: int) -> bool:
    """执行固定窗口限流；Redis 异常时返回 True，让主业务继续工作。"""
    key = rate_limit_key(scope, subject)
    try:
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, window_seconds)
        return int(count) <= limit
    except RedisError:
        return True


def rate_limit_by_ip(scope: str, limit: int, window_seconds: int) -> Callable:
    """创建按 IP 限流的 FastAPI 依赖，适合注册、登录这类未登录接口。"""

    async def dependency(request: Request) -> None:
        subject = get_client_ip(request)
        allowed = await allow_request(scope, subject, limit, window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="too many requests",
            )

    return dependency


def rate_limit_by_account(scope: str, limit: int, window_seconds: int) -> Callable:
    """创建按账号限流的 FastAPI 依赖，适合点赞、评论、关注这类登录后写操作。"""

    async def dependency(current_user: CurrentUser = Depends(get_current_user)) -> None:
        subject = str(current_user.id)
        allowed = await allow_request(scope, subject, limit, window_seconds)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="too many requests",
            )

    return dependency
