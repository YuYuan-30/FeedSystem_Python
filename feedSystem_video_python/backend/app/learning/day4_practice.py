"""
Day 4 亲手敲练习：关注关系、标签提取和 Cache-Aside。

练习方式：
1. 先读 day4_notes.md，确认你知道 MySQL 和 Redis 各自负责什么。
2. 再对照真实实现，把下面四个关键片段自己敲一遍。
3. 重点不是记住函数名，而是讲清“数据从哪里来、经过哪里、最后去哪”。
"""


def practice_extract_tags() -> None:
    """练习 1：对照 extract_tags，理解发布视频时如何从文本中提取 #标签。"""
    # 源码位置：`app/core/tags.py` -> `extract_tags`
    # 调用位置：`app/services/video_service.py` -> `VideoService.publish`
    # 你可以自己敲一遍：
    # seen = set()
    # tags = []
    # for match in tag_pattern.findall(text):
    #     tag = match.strip()
    #     if tag and tag not in seen:
    #         seen.add(tag)
    #         tags.append(tag)


async def practice_follow_relation() -> None:
    """练习 2：对照 SocialService.follow，理解关注关系为什么要先校验再入库。"""
    # 源码位置：`app/services/social_service.py` -> `SocialService.follow`
    # 相关源码：`app/repositories/social_repo.py` -> `SocialRepository.follow`
    # 相关源码：`app/models/social.py` -> `Social`
    # 你可以自己敲一遍：
    # if current_user.id == vlogger_id:
    #     raise CannotFollowSelfError
    # if await account_repo.find_by_id(vlogger_id) is None:
    #     raise AccountNotFoundError
    # if await social_repo.is_followed(current_user.id, vlogger_id):
    #     raise AlreadyFollowedError
    # await social_repo.follow(current_user.id, vlogger_id)


async def practice_video_detail_cache_aside() -> None:
    """练习 3：对照 VideoService.get_detail，理解详情缓存的 Cache-Aside 读链路。"""
    # 源码位置：`app/services/video_service.py` -> `VideoService.get_detail`
    # 缓存工具：`app/core/redis.py` -> `get_json_cache` / `set_json_cache`
    # 你可以自己敲一遍：
    # cache_key = video_detail_cache_key(video_id)
    # cached = await get_json_cache(cache_key)
    # if cached is not None:
    #     return VideoPublic.model_validate(cached)
    # video = await repo.get_by_id(video_id)
    # public = VideoPublic.model_validate(video)
    # await set_json_cache(cache_key, public.model_dump(mode="json"), ttl_seconds=300)
    # return public


async def practice_following_feed_query() -> None:
    """练习 4：对照 list_by_following，理解关注流如何用子查询筛选作者。"""
    # 源码位置：`app/repositories/video_repo.py` -> `VideoRepository.list_by_following`
    # 调用位置：`app/services/feed_service.py` -> `FeedService.list_by_following`
    # 你可以自己敲一遍：
    # following_subquery = select(Social.vlogger_id).where(Social.follower_id == follower_id)
    # stmt = (
    #     select(Video)
    #     .where(Video.author_id.in_(following_subquery))
    #     .order_by(Video.create_time.desc(), Video.id.desc())
    #     .limit(limit)
    # )
