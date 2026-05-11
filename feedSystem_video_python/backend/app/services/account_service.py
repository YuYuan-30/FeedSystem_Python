from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from app.core.auth import create_access_token, create_refresh_token
from app.core.redis import cache_access_token, delete_cached_access_token
from app.core.security import hash_password, verify_password
from app.models.account import Account
from app.repositories.account_repo import AccountRepository


class UsernameAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


@dataclass(frozen=True)
class LoginResult:
    token: str
    refresh_token: str
    account: Account


class AccountService:
    def __init__(self, repo: AccountRepository):
        """注入账号数据访问对象，让业务层通过 Repository 读写数据库。"""
        self.repo = repo

    async def register(self, username: str, password: str) -> Account:
        """处理注册业务：用户名去空格、查重、密码哈希、创建账号。"""
        username = username.strip()
        existing = await self.repo.find_by_username(username)
        if existing is not None:
            raise UsernameAlreadyExistsError

        password_hash = hash_password(password)
        try:
            return await self.repo.create(username=username, password_hash=password_hash)
        except IntegrityError as exc:
            raise UsernameAlreadyExistsError from exc

    async def login(self, username: str, password: str) -> LoginResult:
        """处理登录业务：查账号、校验密码、生成 JWT access token 和 refresh token。"""
        account = await self.repo.find_by_username(username.strip())
        if account is None:
            raise InvalidCredentialsError

        if not verify_password(password, account.password_hash):
            raise InvalidCredentialsError

        token = create_access_token(account.id, account.username)
        refresh_token = create_refresh_token()
        await self.repo.save_tokens(account, token, refresh_token)
        await cache_access_token(account.id, token)
        return LoginResult(token=token, refresh_token=refresh_token, account=account)

    async def refresh_access_token(self, refresh_token: str) -> LoginResult:
        """使用 refresh token 换取新的 access token，并同步更新 MySQL 与 Redis。"""
        account = await self.repo.find_by_refresh_token(refresh_token)
        if account is None:
            raise InvalidRefreshTokenError

        token = create_access_token(account.id, account.username)
        await self.repo.save_access_token(account, token)
        await cache_access_token(account.id, token)
        return LoginResult(token=token, refresh_token=refresh_token, account=account)

    async def logout(self, account_id: int) -> None:
        """主动登出：清空 MySQL token，并删除 Redis 里的当前 access token 缓存。"""
        account = await self.repo.find_by_id(account_id)
        if account is None:
            return
        await self.repo.clear_tokens(account)
        await delete_cached_access_token(account_id)

    async def find_by_id(self, account_id: int) -> Account | None:
        """给查询接口使用：按 ID 获取账号，业务层暂时只转发 Repository 结果。"""
        return await self.repo.find_by_id(account_id)

    async def find_by_username(self, username: str) -> Account | None:
        """给查询接口使用：按用户名获取账号，并统一做去空格处理。"""
        return await self.repo.find_by_username(username.strip())
