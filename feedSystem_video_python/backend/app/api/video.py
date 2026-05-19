from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, get_optional_user
from app.database import get_db
from app.repositories.tag_repo import TagRepository
from app.repositories.video_repo import VideoRepository
from app.schemas.video import (
    GetVideoDetailRequest,
    ListByAuthorIDRequest,
    PublishVideoRequest,
    VideoPublic,
)
from app.services.video_service import VideoNotFoundError, VideoService


router = APIRouter(prefix="/video", tags=["video"])


def get_video_service(db: AsyncSession = Depends(get_db)) -> VideoService:
    """FastAPI 依赖函数：为视频查询接口组装 VideoService。"""
    return VideoService(VideoRepository(db), TagRepository(db))


@router.post("/publish", response_model=VideoPublic)
async def publish(
    req: PublishVideoRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> VideoPublic:
    """发布视频接口：必须登录，成功后把视频元数据写入 videos 表。"""
    service = VideoService(VideoRepository(db), TagRepository(db))
    video = await service.publish(
        current_user=current_user,
        title=req.title,
        description=req.description,
        play_url=req.play_url,
        cover_url=req.cover_url,
    )
    await db.commit()
    return VideoPublic.model_validate(video)


@router.post("/listByAuthorID", response_model=list[VideoPublic])
async def list_by_author_id(
    req: ListByAuthorIDRequest,
    service: VideoService = Depends(get_video_service),
) -> list[VideoPublic]:
    """作者视频列表接口：不需要登录，按作者 ID 返回该作者发布的视频。"""
    videos = await service.list_by_author_id(req.author_id)
    return [VideoPublic.model_validate(video) for video in videos]


@router.post("/getDetail", response_model=VideoPublic)
async def get_detail(
    req: GetVideoDetailRequest,
    _viewer: CurrentUser | None = Depends(get_optional_user),
    service: VideoService = Depends(get_video_service),
) -> VideoPublic:
    """视频详情接口：不带 token 可以访问，带了错误 token 会被软鉴权拒绝。"""
    try:
        detail = await service.get_detail(req.id)
    except VideoNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="video not found")
    return detail
