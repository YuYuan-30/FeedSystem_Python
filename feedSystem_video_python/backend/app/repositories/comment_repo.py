from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment


class CommentRepository:
    def __init__(self, db: AsyncSession):
        """保存当前请求使用的数据库会话，评论模块所有 SQL 都通过它执行。"""
        self.db = db

    async def create(self, video_id: int, author_id: int, username: str, content: str) -> Comment:
        """向 comments 表插入一条评论，并刷新出数据库生成的自增 ID。"""
        comment = Comment(video_id=video_id, author_id=author_id, username=username, content=content)
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def get_by_id(self, comment_id: int) -> Comment | None:
        """根据评论 ID 查询评论；删除评论前需要先校验作者归属。"""
        return await self.db.get(Comment, comment_id)

    async def delete_by_id(self, comment_id: int) -> bool:
        """按评论 ID 删除评论，返回是否真的删除了记录。"""
        stmt = delete(Comment).where(Comment.id == comment_id)
        result = await self.db.execute(stmt)
        return (result.rowcount or 0) > 0

    async def list_by_video_id(self, video_id: int) -> list[Comment]:
        """查询某个视频下的全部评论，按发布时间倒序返回。"""
        stmt = (
            select(Comment)
            .where(Comment.video_id == video_id)
            .order_by(Comment.created_at.desc(), Comment.id.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
