from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account


class AccountRepository:
    def __init__(self, db: AsyncSession):
        """保存当前请求使用的数据库会话，后续所有账号查询都通过它执行。"""
        self.db = db

    async def create(self, username: str, password_hash: str) -> Account:
        """向 accounts 表插入新用户，并刷新出数据库生成的自增 ID。"""
        account = Account(username=username, password_hash=password_hash)
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account

    async def find_by_id(self, account_id: int) -> Account | None:
        """根据主键 ID 查询账号；找不到时返回 None。"""
        return await self.db.get(Account, account_id)

    async def find_by_username(self, username: str) -> Account | None:
        """根据唯一用户名查询账号；注册查重和登录都会复用它。"""
        stmt = select(Account).where(Account.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def save_tokens(self, account: Account, token: str, refresh_token: str) -> None:
        """登录成功后同时保存 access token 和 refresh token，作为服务端登录态真相。"""
        account.token = token
        account.refresh_token = refresh_token
        self.db.add(account)
        await self.db.flush()

    async def save_access_token(self, account: Account, token: str) -> None:
        """刷新 access token 时只替换短 token，refresh token 保持不变。"""
        account.token = token
        self.db.add(account)
        await self.db.flush()

    async def find_by_refresh_token(self, refresh_token: str) -> Account | None:
        """根据 refresh token 查账号，用于换取新的 access token。"""
        stmt = select(Account).where(Account.refresh_token == refresh_token)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def clear_tokens(self, account: Account) -> None:
        """登出时清空服务端保存的 token，让旧 access token 主动失效。"""
        account.token = ""
        account.refresh_token = ""
        self.db.add(account)
        await self.db.flush()
