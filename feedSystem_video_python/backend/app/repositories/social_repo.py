from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.social import Social


class SocialRepository:
    def __init__(self, db: AsyncSession):
        """保存当前请求使用的数据库会话，关注关系的 SQL 都从这里发出。"""
        self.db = db

    async def follow(self, follower_id: int, vlogger_id: int) -> Social:
        """插入一条关注关系，唯一约束会兜底防止重复关注。"""
        relation = Social(follower_id=follower_id, vlogger_id=vlogger_id)
        self.db.add(relation)
        await self.db.flush()
        await self.db.refresh(relation)
        return relation

    async def unfollow(self, follower_id: int, vlogger_id: int) -> bool:
        """删除一条关注关系，返回是否真的删到了数据。"""
        stmt = delete(Social).where(
            Social.follower_id == follower_id,
            Social.vlogger_id == vlogger_id,
        )
        result = await self.db.execute(stmt)
        return result.rowcount > 0

    async def is_followed(self, follower_id: int, vlogger_id: int) -> bool:
        """判断 follower_id 是否已经关注 vlogger_id。"""
        stmt = select(Social.id).where(
            Social.follower_id == follower_id,
            Social.vlogger_id == vlogger_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_followers(self, vlogger_id: int) -> list[Account]:
        """查询某个作者的粉丝账号列表。"""
        stmt = (
            select(Account)
            .join(Social, Social.follower_id == Account.id)
            .where(Social.vlogger_id == vlogger_id)
            .order_by(Social.created_at.desc(), Social.id.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_vloggers(self, follower_id: int) -> list[Account]:
        """查询某个用户正在关注的作者账号列表。"""
        stmt = (
            select(Account)
            .join(Social, Social.vlogger_id == Account.id)
            .where(Social.follower_id == follower_id)
            .order_by(Social.created_at.desc(), Social.id.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_followers(self, vlogger_id: int) -> int:
        """统计某个作者的粉丝数。"""
        stmt = select(func.count()).select_from(Social).where(Social.vlogger_id == vlogger_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())

    async def count_vloggers(self, follower_id: int) -> int:
        """统计某个用户关注了多少作者。"""
        stmt = select(func.count()).select_from(Social).where(Social.follower_id == follower_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
