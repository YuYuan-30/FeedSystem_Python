from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, VideoTag


class TagRepository:
    def __init__(self, db: AsyncSession):
        """保存当前请求使用的数据库会话，标签和视频标签关系都从这里维护。"""
        self.db = db

    async def get_or_create(self, name: str) -> Tag:
        """按标签名查询标签；不存在时创建，保证同名标签只保留一份。"""
        stmt = select(Tag).where(Tag.name == name)
        result = await self.db.execute(stmt)
        tag = result.scalar_one_or_none()
        if tag is not None:
            return tag

        tag = Tag(name=name)
        self.db.add(tag)
        await self.db.flush()
        await self.db.refresh(tag)
        return tag

    async def attach_tags(self, video_id: int, tag_names: list[str]) -> None:
        """给视频绑定一组标签，发布视频时和视频元数据处于同一个事务。"""
        for name in tag_names:
            tag = await self.get_or_create(name)
            self.db.add(VideoTag(video_id=video_id, tag_id=tag.id))
        await self.db.flush()
