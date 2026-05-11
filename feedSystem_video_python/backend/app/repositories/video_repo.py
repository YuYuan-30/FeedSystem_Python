from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
