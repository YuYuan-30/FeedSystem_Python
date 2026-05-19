from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video
from app.repositories.video_repo import VideoRepository


class FeedRepository:
    def __init__(self, db: AsyncSession):
        """复用 VideoRepository 的查询能力，让 Feed 层专注排序和分页语义。"""
        self.video_repo = VideoRepository(db)

    async def list_latest(self, limit: int, before: datetime | None) -> list[Video]:
        """查询最新 Feed 页，before 是上一页最后一条视频的 create_time 游标。"""
        return await self.video_repo.list_latest(limit, before)

    async def list_by_following(
        self,
        follower_id: int,
        limit: int,
        before: datetime | None,
    ) -> list[Video]:
        """查询关注 Feed 页，只包含当前用户关注作者的视频。"""
        return await self.video_repo.list_by_following(follower_id, limit, before)

    async def list_by_tag(self, tag_name: str, limit: int, before: datetime | None) -> list[Video]:
        """查询标签 Feed 页，只包含带指定 #tag 的视频。"""
        return await self.video_repo.list_by_tag(tag_name, limit, before)

    async def list_likes_count(
        self,
        limit: int,
        likes_count_before: int | None,
        id_before: int | None,
    ) -> list[Video]:
        """查询点赞榜 Feed 页，使用 likes_count + id 复合游标。"""
        return await self.video_repo.list_likes_count(limit, likes_count_before, id_before)
