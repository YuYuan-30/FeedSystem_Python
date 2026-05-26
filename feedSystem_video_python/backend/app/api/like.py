from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.ratelimit import rate_limit_by_account
from app.database import get_db
from app.repositories.like_repo import LikeRepository
from app.repositories.video_repo import VideoRepository
from app.schemas.common import MessageResponse
from app.schemas.like import IsLikedResponse, LikeRequest
from app.services.like_service import (
    AlreadyLikedError,
    LikeService,
    NotLikedError,
    VideoNotFoundError,
)


router = APIRouter(prefix="/like", tags=["like"])


def get_like_service(db: AsyncSession = Depends(get_db)) -> LikeService:
    """FastAPI 依赖函数：组装点赞 Service，便于查询接口复用。"""
    return LikeService(LikeRepository(db), VideoRepository(db))


@router.post(
    "/like",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit_by_account("like_write", limit=60, window_seconds=60))],
)
async def like_video(
    req: LikeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """点赞接口：必须登录，成功后写 likes 表并增加 videos.likes_count。"""
    service = LikeService(LikeRepository(db), VideoRepository(db))
    try:
        await service.like(current_user, req.video_id)
        await db.commit()
    except VideoNotFoundError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="video not found")
    except AlreadyLikedError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user has liked this video")
    return MessageResponse(message="video liked")


@router.post(
    "/unlike",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit_by_account("like_write", limit=60, window_seconds=60))],
)
async def unlike_video(
    req: LikeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """取消点赞接口：必须登录，成功后删除 likes 记录并安全减少计数。"""
    service = LikeService(LikeRepository(db), VideoRepository(db))
    try:
        await service.unlike(current_user, req.video_id)
        await db.commit()
    except VideoNotFoundError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="video not found")
    except NotLikedError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="user has not liked this video")
    return MessageResponse(message="video unliked")


@router.post("/isLiked", response_model=IsLikedResponse)
async def is_liked(
    req: LikeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: LikeService = Depends(get_like_service),
) -> IsLikedResponse:
    """是否点赞接口：必须登录，用于详情页或 Feed 个性化状态。"""
    try:
        liked = await service.is_liked(current_user, req.video_id)
    except VideoNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="video not found")
    return IsLikedResponse(is_liked=liked)
