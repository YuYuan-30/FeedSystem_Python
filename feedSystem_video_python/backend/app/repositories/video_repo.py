from datetime import datetime

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social import Social
from app.models.tag import Tag, VideoTag
from app.models.video import Video


class VideoRepository:
    def __init__(self, db: AsyncSession):
        """保存当前请求使用的数据库会话，视频模块所有 SQL 都通过它执行。"""
        self.db = db

    async def create(
        self,
        author_id: int,
        username: str,
        title: str,
        description: str,
        play_url: str,
        cover_url: str,
    ) -> Video:
        """向 videos 表插入一条视频元数据，并刷新出数据库生成的自增 ID。"""
        video = Video(
            author_id=author_id,
            username=username,
            title=title,
            description=description,
            play_url=play_url,
            cover_url=cover_url,
        )
        self.db.add(video)
        await self.db.flush()
        await self.db.refresh(video)
        return video

    async def list_by_author_id(self, author_id: int) -> list[Video]:
        """按作者 ID 查询视频列表，按发布时间倒序返回。"""
        stmt = (
            select(Video)
            .where(Video.author_id == author_id)
            .order_by(Video.create_time.desc(), Video.id.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, video_id: int) -> Video | None:
        """根据视频 ID 查询视频详情；找不到时返回 None。"""
        return await self.db.get(Video, video_id)

    async def exists(self, video_id: int) -> bool:
        """只查询视频 ID 是否存在，避免为了校验存在性加载整行数据。"""
        stmt = select(Video.id).where(Video.id == video_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def increment_like_counters(self, video_id: int) -> None:
        """点赞成功后增加视频点赞数和热度，和插入 likes 关系处于同一事务。"""
        stmt = (
            update(Video)
            .where(Video.id == video_id)
            .values(
                likes_count=Video.likes_count + 1,
                popularity=Video.popularity + 1,
            )
        )
        await self.db.execute(stmt)

    async def decrement_like_counters(self, video_id: int) -> None:
        """取消点赞后减少视频点赞数和热度，并用 GREATEST 防止计数变成负数。"""
        stmt = (
            update(Video)
            .where(Video.id == video_id)
            .values(
                likes_count=func.greatest(Video.likes_count - 1, 0),
                popularity=func.greatest(Video.popularity - 1, 0),
            )
        )
        await self.db.execute(stmt)

    async def increment_popularity(self, video_id: int) -> None:
        """评论发布成功后增加视频热度，暂时不改点赞数。"""
        stmt = update(Video).where(Video.id == video_id).values(popularity=Video.popularity + 1)
        await self.db.execute(stmt)

    async def decrement_popularity(self, video_id: int) -> None:
        """评论删除后降低视频热度，并保证热度不会小于 0。"""
        stmt = (
            update(Video)
            .where(Video.id == video_id)
            .values(popularity=func.greatest(Video.popularity - 1, 0))
        )
        await self.db.execute(stmt)

    async def list_latest(self, limit: int, before: datetime | None) -> list[Video]:
        """按发布时间倒序查询最新视频；before 不为空时使用 create_time 游标翻页。"""
        stmt = select(Video).order_by(Video.create_time.desc(), Video.id.desc()).limit(limit)
        if before is not None:
            stmt = stmt.where(Video.create_time < before)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_following(
        self,
        follower_id: int,
        limit: int,
        before: datetime | None,
    ) -> list[Video]:
        """查询关注流：只返回当前用户关注作者发布的视频，并按发布时间倒序分页。"""
        following_subquery = select(Social.vlogger_id).where(Social.follower_id == follower_id)
        stmt = (
            select(Video)
            .where(Video.author_id.in_(following_subquery))
            .order_by(Video.create_time.desc(), Video.id.desc())
            .limit(limit)
        )
        if before is not None:
            stmt = stmt.where(Video.create_time < before)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_tag(self, tag_name: str, limit: int, before: datetime | None) -> list[Video]:
        """查询标签流：通过 video_tags 关系表找到带指定标签的视频。"""
        stmt = (
            select(Video)
            .join(VideoTag, VideoTag.video_id == Video.id)
            .join(Tag, Tag.id == VideoTag.tag_id)
            .where(Tag.name == tag_name)
            .order_by(Video.create_time.desc(), Video.id.desc())
            .limit(limit)
        )
        if before is not None:
            stmt = stmt.where(Video.create_time < before)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_likes_count(
        self,
        limit: int,
        likes_count_before: int | None,
        id_before: int | None,
    ) -> list[Video]:
        """按点赞数倒序查询视频，用 likes_count + id 复合游标避免翻页重复。"""
        stmt = select(Video).order_by(Video.likes_count.desc(), Video.id.desc()).limit(limit)
        if likes_count_before is not None and id_before is not None:
            stmt = stmt.where(
                or_(
                    Video.likes_count < likes_count_before,
                    and_(Video.likes_count == likes_count_before, Video.id < id_before),
                )
            )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
