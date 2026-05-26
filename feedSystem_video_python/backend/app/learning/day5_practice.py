"""
Day 5 亲手敲练习：Redis 限流和 MQ 扩展点。

练习方式：
1. 先读 day5_notes.md，理解限流为什么是保护层、Redis 为什么可以失败放行。
2. 再对照真实实现，把下面三个关键片段自己敲一遍。
3. 重点不是背 Redis 命令，而是能讲清每个 key、TTL 和返回值的含义。
"""


def practice_rate_limit_key() -> None:
    """练习 1：对照 rate_limit_key，理解限流 key 为什么要包含 scope 和 subject。"""
    # 源码位置：`app/core/ratelimit.py` -> `rate_limit_key`
    # 你可以自己敲一遍：
    # return f"v1:ratelimit:{scope}:{subject}"


async def practice_allow_request() -> None:
    """练习 2：对照 allow_request，理解 Redis INCR + EXPIRE 固定窗口限流。"""
    # 源码位置：`app/core/ratelimit.py` -> `allow_request`
    # 你可以自己敲一遍：
    # count = await redis_client.incr(key)
    # if count == 1:
    #     await redis_client.expire(key, window_seconds)
    # return int(count) <= limit


async def practice_event_publisher() -> None:
    """练习 3：对照 EventPublisher，理解当前为什么返回 False 走同步 MySQL。"""
    # 源码位置：`app/core/events.py` -> `EventPublisher`
    # 调用位置：`app/services/like_service.py` -> `LikeService.like`
    # 调用位置：`app/services/social_service.py` -> `SocialService.follow`
    # 你可以自己敲一遍：
    # published = await publisher.publish_like(account_id, video_id)
    # if published:
    #     return
    # await like_repo.create(video_id=video_id, account_id=account_id)
