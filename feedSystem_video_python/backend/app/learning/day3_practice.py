"""
Day 3 亲手敲练习：事务、冗余计数和复合游标。

练习方式：
1. 先读 day3_notes.md，确认你知道每个字段为什么存在。
2. 再对照真实实现，把下面三个关键片段自己敲一遍。
3. 重点不是背 API，而是讲清“如果不这样写会出什么问题”。
"""


async def practice_like_transaction() -> None:
    """练习 1：对照 LikeService.like，理解点赞关系和计数字段为什么要一起提交。"""
    # 源码位置：`app/services/like_service.py` -> `LikeService.like`
    # 相关源码：`app/repositories/like_repo.py` -> `LikeRepository.create`
    # 相关源码：`app/repositories/video_repo.py` -> `VideoRepository.increment_like_counters`
    # 你可以自己敲一遍：
    # if not await video_repo.exists(video_id):
    #     raise VideoNotFoundError
    # if await like_repo.is_liked(video_id, current_user.id):
    #     raise AlreadyLikedError
    # await like_repo.create(video_id=video_id, account_id=current_user.id)
    # await video_repo.increment_like_counters(video_id)


async def practice_unlike_counter_guard() -> None:
    """练习 2：对照 decrement_like_counters，理解为什么取消点赞要防止负数。"""
    # 源码位置：`app/repositories/video_repo.py` -> `VideoRepository.decrement_like_counters`
    # 调用位置：`app/services/like_service.py` -> `LikeService.unlike`
    # 你可以自己敲一遍：
    # update(Video).where(Video.id == video_id).values(
    #     likes_count=func.greatest(Video.likes_count - 1, 0),
    #     popularity=func.greatest(Video.popularity - 1, 0),
    # )


async def practice_likes_count_cursor() -> None:
    """练习 3：对照 list_likes_count，理解点赞榜为什么需要 likes_count + id 复合游标。"""
    # 源码位置：`app/repositories/video_repo.py` -> `VideoRepository.list_likes_count`
    # 调用位置：`app/services/feed_service.py` -> `FeedService.list_likes_count`
    # 你可以自己敲一遍：
    # stmt = select(Video).order_by(Video.likes_count.desc(), Video.id.desc())
    # stmt = stmt.where(
    #     or_(
    #         Video.likes_count < likes_count_before,
    #         and_(Video.likes_count == likes_count_before, Video.id < id_before),
    #     )
    # )
