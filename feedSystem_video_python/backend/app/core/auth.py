from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import secrets

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.redis import cache_access_token, get_cached_access_token
from app.database import get_db
from app.repositories.account_repo import AccountRepository


settings = get_settings()
bearer_scheme = HTTPBearer(auto_error=False)


class TokenInvalidError(Exception):
    pass


@dataclass(frozen=True)
class TokenPayload:
    account_id: int
    username: str


@dataclass(frozen=True)
class CurrentUser:
    id: int
    username: str


def create_access_token(account_id: int, username: str) -> str:
    """生成短时有效的 JWT access token，把用户身份放进 payload 并用密钥签名。"""
    now = datetime.now(UTC)
    payload = {
        "sub": str(account_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token() -> str:
    """生成长时有效的 refresh token；它是不透明随机字符串，只在服务端保存和校验。"""
    return secrets.token_urlsafe(48)


def parse_access_token(token: str) -> TokenPayload:
    """解析并校验 JWT access token，签名或过期时间不合法时抛出统一异常。"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        account_id = int(payload["sub"])
        username = str(payload["username"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise TokenInvalidError from exc
    return TokenPayload(account_id=account_id, username=username)


def _unauthorized() -> HTTPException:
    """构造统一的 401 响应，告诉前端需要重新登录或刷新 token。"""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _resolve_user_from_token(token: str, db: AsyncSession) -> CurrentUser:
    """完成 token 认证链路：先验 JWT，再查 Redis，缓存未命中时回源 MySQL。"""
    try:
        payload = parse_access_token(token)
    except TokenInvalidError:
        raise _unauthorized()

    cached_token = await get_cached_access_token(payload.account_id)
    if cached_token is not None:
        if cached_token != token:
            raise _unauthorized()
        return CurrentUser(id=payload.account_id, username=payload.username)

    repo = AccountRepository(db)
    account = await repo.find_by_id(payload.account_id)
    if account is None or account.token != token:
        raise _unauthorized()

    await cache_access_token(account.id, token)
    return CurrentUser(id=account.id, username=account.username)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """硬鉴权依赖：没有 token 或 token 不合法时直接拒绝请求。"""
    if credentials is None:
        raise _unauthorized()
    return await _resolve_user_from_token(credentials.credentials, db)


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser | None:
    """软鉴权依赖：不带 token 可以继续访问，但带了坏 token 就拒绝。"""
    if credentials is None:
        return None
    return await _resolve_user_from_token(credentials.credentials, db)
