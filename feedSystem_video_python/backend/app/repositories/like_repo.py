from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.like import Like


class LikeRepository:
    def __init__(self, db: AsyncSession):
        """保存当前请求使用的数据库会话，点赞关系读写都通过它执行。"""
        self.db = db

    async def create(self, video_id: int, account_id: int) -> Like:
        """向 likes 表插入一条点赞关系，唯一索引用来兜底防重复点赞。"""
        like = Like(video_id=video_id, account_id=account_id)
        self.db.add(like)
        await self.db.flush()
        await self.db.refresh(like)
        return like

    async def delete(self, video_id: int, account_id: int) -> bool:
        """删除某个用户对某个视频的点赞关系，返回是否真的删除了记录。"""
        stmt = delete(Like).where(Like.video_id == video_id, Like.account_id == account_id)
        result = await self.db.execute(stmt)
        return (result.rowcount or 0) > 0

    async def is_liked(self, video_id: int, account_id: int) -> bool:
        """判断用户是否已经点赞某视频，只查询主键字段降低无用数据加载。"""
        stmt = select(Like.id).where(Like.video_id == video_id, Like.account_id == account_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def batch_liked_video_ids(self, video_ids: list[int], account_id: int | None) -> set[int]:
        """批量查询用户点赞过的视频 ID，Feed 构造 is_liked 字段时复用。"""
        if account_id is None or not video_ids:
            return set()
        stmt = select(Like.video_id).where(Like.account_id == account_id, Like.video_id.in_(video_ids))
        result = await self.db.execute(stmt)
        return set(result.scalars().all())
