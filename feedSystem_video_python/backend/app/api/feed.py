from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, get_optional_user
from app.database import get_db
from app.repositories.feed_repo import FeedRepository
from app.repositories.like_repo import LikeRepository
from app.schemas.feed import (
    ListLatestRequest,
    ListLatestResponse,
    ListByFollowingRequest,
    ListByFollowingResponse,
    ListByTagRequest,
    ListByTagResponse,
    ListLikesCountRequest,
    ListLikesCountResponse,
)
from app.services.feed_service import FeedService


router = APIRouter(prefix="/feed", tags=["feed"])


def get_feed_service(db: AsyncSession = Depends(get_db)) -> FeedService:
    """FastAPI 依赖函数：组装 FeedService，复用 Feed 和 Like 查询能力。"""
    return FeedService(FeedRepository(db), LikeRepository(db))


@router.post("/listLatest", response_model=ListLatestResponse)
async def list_latest(
    req: ListLatestRequest,
    viewer: CurrentUser | None = Depends(get_optional_user),
    service: FeedService = Depends(get_feed_service),
) -> ListLatestResponse:
    """最新 Feed 接口：软鉴权，使用 create_time 毫秒游标分页。"""
    return await service.list_latest(req.limit, req.latest_time, viewer)


@router.post("/listLikesCount", response_model=ListLikesCountResponse)
async def list_likes_count(
    req: ListLikesCountRequest,
    viewer: CurrentUser | None = Depends(get_optional_user),
    service: FeedService = Depends(get_feed_service),
) -> ListLikesCountResponse:
    """点赞榜 Feed 接口：软鉴权，使用 likes_count + id 复合游标分页。"""
    return await service.list_likes_count(
        limit=req.limit,
        likes_count_before=req.likes_count_before,
        id_before=req.id_before,
        viewer=viewer,
    )


@router.post("/listByFollowing", response_model=ListByFollowingResponse)
async def list_by_following(
    req: ListByFollowingRequest,
    viewer: CurrentUser = Depends(get_current_user),
    service: FeedService = Depends(get_feed_service),
) -> ListByFollowingResponse:
    """关注 Feed 接口：必须登录，只看自己关注作者发布的视频。"""
    return await service.list_by_following(req.limit, req.latest_time, viewer)


@router.post("/listByTag", response_model=ListByTagResponse)
async def list_by_tag(
    req: ListByTagRequest,
    viewer: CurrentUser | None = Depends(get_optional_user),
    service: FeedService = Depends(get_feed_service),
) -> ListByTagResponse:
    """标签 Feed 接口：软鉴权，按 #tag 查询视频列表。"""
    return await service.list_by_tag(req.tag_name, req.limit, req.latest_time, viewer)
