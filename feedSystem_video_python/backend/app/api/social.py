from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.ratelimit import rate_limit_by_account
from app.database import get_db
from app.repositories.account_repo import AccountRepository
from app.repositories.social_repo import SocialRepository
from app.schemas.account import AccountPublic
from app.schemas.common import MessageResponse
from app.schemas.social import (
    FollowRequest,
    GetAllFollowersRequest,
    GetAllFollowersResponse,
    GetAllVloggersRequest,
    GetAllVloggersResponse,
    SocialCountsResponse,
    UnfollowRequest,
)
from app.services.social_service import (
    AccountNotFoundError,
    AlreadyFollowedError,
    CannotFollowSelfError,
    NotFollowedError,
    SocialService,
)


router = APIRouter(prefix="/social", tags=["social"])


def get_social_service(db: AsyncSession = Depends(get_db)) -> SocialService:
    """FastAPI 依赖函数：组装关注 Service，统一注入关系仓储和账号仓储。"""
    return SocialService(SocialRepository(db), AccountRepository(db))


@router.post(
    "/follow",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit_by_account("social_write", limit=30, window_seconds=60))],
)
async def follow(
    req: FollowRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """关注接口：必须登录，成功后在 socials 表插入 follower/vlogger 关系。"""
    service = SocialService(SocialRepository(db), AccountRepository(db))
    try:
        await service.follow(current_user, req.vlogger_id)
        await db.commit()
    except AccountNotFoundError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    except CannotFollowSelfError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="cannot follow yourself")
    except AlreadyFollowedError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="already followed")
    return MessageResponse(message="followed")


@router.post(
    "/unfollow",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit_by_account("social_write", limit=30, window_seconds=60))],
)
async def unfollow(
    req: UnfollowRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """取关接口：必须登录，成功后删除 socials 表中的关注关系。"""
    service = SocialService(SocialRepository(db), AccountRepository(db))
    try:
        await service.unfollow(current_user, req.vlogger_id)
        await db.commit()
    except AccountNotFoundError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    except NotFollowedError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="not followed")
    return MessageResponse(message="unfollowed")


@router.post("/getAllFollowers", response_model=GetAllFollowersResponse)
async def get_all_followers(
    req: GetAllFollowersRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SocialService = Depends(get_social_service),
) -> GetAllFollowersResponse:
    """粉丝列表接口：必须登录，不传 vlogger_id 时查询自己的粉丝。"""
    try:
        followers, count = await service.get_all_followers(current_user, req.vlogger_id)
    except AccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    return GetAllFollowersResponse(
        followers=[AccountPublic.model_validate(account) for account in followers],
        follower_count=count,
    )


@router.post("/getAllVloggers", response_model=GetAllVloggersResponse)
async def get_all_vloggers(
    req: GetAllVloggersRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: SocialService = Depends(get_social_service),
) -> GetAllVloggersResponse:
    """关注列表接口：必须登录，不传 follower_id 时查询自己关注了谁。"""
    try:
        vloggers, count = await service.get_all_vloggers(current_user, req.follower_id)
    except AccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="account not found")
    return GetAllVloggersResponse(
        vloggers=[AccountPublic.model_validate(account) for account in vloggers],
        vlogger_count=count,
    )


@router.post("/getCounts", response_model=SocialCountsResponse)
async def get_counts(
    current_user: CurrentUser = Depends(get_current_user),
    service: SocialService = Depends(get_social_service),
) -> SocialCountsResponse:
    """关注统计接口：返回当前用户粉丝数和关注数。"""
    follower_count, vlogger_count = await service.get_counts(current_user)
    return SocialCountsResponse(follower_count=follower_count, vlogger_count=vlogger_count)
