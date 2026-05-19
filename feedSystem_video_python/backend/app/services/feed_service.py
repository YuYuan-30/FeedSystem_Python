from datetime import UTC, datetime

from app.core.auth import CurrentUser
from app.core.redis import feed_latest_cache_key, get_json_cache, set_json_cache
from app.models.video import Video
from app.repositories.feed_repo import FeedRepository
from app.repositories.like_repo import LikeRepository
from app.schemas.feed import (
    FeedAuthor,
    FeedVideoItem,
    ListByFollowingResponse,
    ListByTagResponse,
    ListLatestResponse,
    ListLikesCountResponse,
)


def millis_to_datetime(value: int) -> datetime | None:
    """把前端传来的毫秒级时间戳游标转换成 datetime；0 表示第一页。"""
    if value <= 0:
        return None
    return datetime.fromtimestamp(value / 1000, tz=UTC).replace(tzinfo=None)


def datetime_to_millis(value: datetime) -> int:
    """把数据库里的 create_time 转成毫秒时间戳，作为下一页游标返回前端。"""
    return int(value.replace(tzinfo=UTC).timestamp() * 1000)


class FeedService:
    def __init__(self, feed_repo: FeedRepository, like_repo: LikeRepository):
        """注入 Feed 查询和点赞查询对象，用于组装带 is_liked 的 Feed 项。"""
        self.feed_repo = feed_repo
        self.like_repo = like_repo

    async def list_latest(
        self,
        limit: int,
        latest_time: int,
        viewer: CurrentUser | None,
    ) -> ListLatestResponse:
        """查询最新 Feed：先尝试短 TTL 缓存，未命中再走 MySQL 游标分页。"""
        cache_key = feed_latest_cache_key(limit, latest_time, viewer.id if viewer else None)
        cached = await get_json_cache(cache_key)
        if cached is not None:
            return ListLatestResponse.model_validate(cached)

        before = millis_to_datetime(latest_time)
        videos = await self.feed_repo.list_latest(limit, before)
        items = await self._build_feed_items(videos, viewer)
        next_time = datetime_to_millis(videos[-1].create_time) if videos else 0
        response = ListLatestResponse(
            video_list=items,
            next_time=next_time,
            has_more=len(videos) == limit,
        )
        await set_json_cache(cache_key, response.model_dump(mode="json"), ttl_seconds=5)
        return response

    async def list_by_following(
        self,
        limit: int,
        latest_time: int,
        viewer: CurrentUser,
    ) -> ListByFollowingResponse:
        """查询关注 Feed：用关注关系筛选作者，再按发布时间游标分页。"""
        before = millis_to_datetime(latest_time)
        videos = await self.feed_repo.list_by_following(viewer.id, limit, before)
        items = await self._build_feed_items(videos, viewer)
        next_time = datetime_to_millis(videos[-1].create_time) if videos else 0
        return ListByFollowingResponse(
            video_list=items,
            next_time=next_time,
            has_more=len(videos) == limit,
        )

    async def list_by_tag(
        self,
        tag_name: str,
        limit: int,
        latest_time: int,
        viewer: CurrentUser | None,
    ) -> ListByTagResponse:
        """查询标签 Feed：按标签名找到视频，再按发布时间游标分页。"""
        before = millis_to_datetime(latest_time)
        videos = await self.feed_repo.list_by_tag(tag_name.strip().lstrip("#"), limit, before)
        items = await self._build_feed_items(videos, viewer)
        next_time = datetime_to_millis(videos[-1].create_time) if videos else 0
        return ListByTagResponse(
            video_list=items,
            next_time=next_time,
            has_more=len(videos) == limit,
        )

    async def list_likes_count(
        self,
        limit: int,
        likes_count_before: int | None,
        id_before: int | None,
        viewer: CurrentUser | None,
    ) -> ListLikesCountResponse:
        """查询点赞榜 Feed：用 likes_count + id 复合游标分页。"""
        videos = await self.feed_repo.list_likes_count(limit, likes_count_before, id_before)
        items = await self._build_feed_items(videos, viewer)
        next_likes = videos[-1].likes_count if videos else None
        next_id = videos[-1].id if videos else None
        return ListLikesCountResponse(
            video_list=items,
            next_likes_count_before=next_likes,
            next_id_before=next_id,
            has_more=len(videos) == limit,
        )

    async def _build_feed_items(
        self,
        videos: list[Video],
        viewer: CurrentUser | None,
    ) -> list[FeedVideoItem]:
        """把 Video 模型转换成 Feed 响应项，并批量补充当前用户是否点赞。"""
        viewer_id = viewer.id if viewer is not None else None
        liked_ids = await self.like_repo.batch_liked_video_ids([video.id for video in videos], viewer_id)
        return [
            FeedVideoItem(
                id=video.id,
                author=FeedAuthor(id=video.author_id, username=video.username),
                title=video.title,
                description=video.description,
                play_url=video.play_url,
                cover_url=video.cover_url,
                create_time=datetime_to_millis(video.create_time),
                likes_count=video.likes_count,
                is_liked=video.id in liked_ids,
            )
            for video in videos
        ]
