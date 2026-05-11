from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.repositories.account_repo import AccountRepository
from app.schemas.account import (
    AccountPublic,
    FindByIDRequest,
    FindByUsernameRequest,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RegisterRequest,
)
from app.schemas.common import MessageResponse
from app.services.account_service import (
    AccountService,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    UsernameAlreadyExistsError,
)

router = APIRouter(prefix="/account", tags=["account"])


def get_account_service(db: AsyncSession = Depends(get_db)) -> AccountService:
    """FastAPI 依赖函数：为查询类接口组装 AccountService。"""
    return AccountService(AccountRepository(db))


@router.post("/register", response_model=MessageResponse)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """注册接口：接收用户名和密码，调用业务层创建账号，成功后提交事务。"""
    service = AccountService(AccountRepository(db))
    try:
        await service.register(req.username, req.password)
        await db.commit()
    except UsernameAlreadyExistsError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username already exists",
        )
    return MessageResponse(message="account created")


@router.post("/login", response_model=LoginResponse)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """登录接口：校验用户名密码，成功后返回 access token、refresh token 和用户信息。"""
    service = AccountService(AccountRepository(db))
    try:
        result = await service.login(req.username, req.password)
        await db.commit()
    except InvalidCredentialsError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password",
        )

    return LoginResponse(
        token=result.token,
        refresh_token=result.refresh_token,
        account_id=result.account.id,
        username=result.account.username,
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    """刷新接口：用 refresh token 换取新的 access token，避免用户频繁重新登录。"""
    service = AccountService(AccountRepository(db))
    try:
        result = await service.refresh_access_token(req.refresh_token)
        await db.commit()
    except InvalidRefreshTokenError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid refresh token",
        )

    return LoginResponse(
        token=result.token,
        refresh_token=result.refresh_token,
        account_id=result.account.id,
        username=result.account.username,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """登出接口：必须携带 access token，服务端会清空 token 让它主动失效。"""
    service = AccountService(AccountRepository(db))
    await service.logout(current_user.id)
    await db.commit()
    return MessageResponse(message="account logged out")


@router.post("/me", response_model=AccountPublic)
async def me(
    current_user: CurrentUser = Depends(get_current_user),
    service: AccountService = Depends(get_account_service),
) -> AccountPublic:
    """当前用户接口：用硬鉴权拿到登录用户，再返回数据库中的公开账号信息。"""
    account = await service.find_by_id(current_user.id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    return AccountPublic.model_validate(account)


@router.post("/findByID", response_model=AccountPublic)
async def find_by_id(
    req: FindByIDRequest,
    service: AccountService = Depends(get_account_service),
) -> AccountPublic:
    """按 ID 查询账号：只返回公开字段，不暴露密码哈希和 token。"""
    account = await service.find_by_id(req.id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    return AccountPublic.model_validate(account)


@router.post("/findByUsername", response_model=AccountPublic)
async def find_by_username(
    req: FindByUsernameRequest,
    service: AccountService = Depends(get_account_service),
) -> AccountPublic:
    """按用户名查询账号：供登录前检查、用户搜索等场景复用。"""
    account = await service.find_by_username(req.username)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    return AccountPublic.model_validate(account)
