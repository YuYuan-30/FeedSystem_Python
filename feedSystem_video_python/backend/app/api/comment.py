from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.database import get_db
from app.repositories.comment_repo import CommentRepository
from app.repositories.video_repo import VideoRepository
from app.schemas.comment import (
    CommentPublic,
    DeleteCommentRequest,
    ListCommentsRequest,
    PublishCommentRequest,
)
from app.schemas.common import MessageResponse
from app.services.comment_service import (
    CommentForbiddenError,
    CommentNotFoundError,
    CommentService,
    VideoNotFoundError,
)


router = APIRouter(prefix="/comment", tags=["comment"])


def get_comment_service(db: AsyncSession = Depends(get_db)) -> CommentService:
    """FastAPI 依赖函数：组装评论 Service，供只读接口复用。"""
    return CommentService(CommentRepository(db), VideoRepository(db))


@router.post("/publish", response_model=CommentPublic)
async def publish_comment(
    req: PublishCommentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommentPublic:
    """发布评论接口：必须登录，成功后写 comments 表并提高视频热度。"""
    service = CommentService(CommentRepository(db), VideoRepository(db))
    try:
        comment = await service.publish(current_user, req.video_id, req.content)
        await db.commit()
    except VideoNotFoundError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="video not found")
    return CommentPublic.model_validate(comment)


@router.post("/delete", response_model=MessageResponse)
async def delete_comment(
    req: DeleteCommentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """删除评论接口：必须登录，且只能删除自己发布的评论。"""
    service = CommentService(CommentRepository(db), VideoRepository(db))
    try:
        await service.delete(current_user, req.id)
        await db.commit()
    except CommentNotFoundError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="comment not found")
    except CommentForbiddenError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="cannot delete others comment")
    return MessageResponse(message="comment deleted")


@router.post("/listAll", response_model=list[CommentPublic])
async def list_comments(
    req: ListCommentsRequest,
    service: CommentService = Depends(get_comment_service),
) -> list[CommentPublic]:
    """评论列表接口：不需要登录，按视频 ID 返回该视频下的评论。"""
    try:
        comments = await service.list_all(req.video_id)
    except VideoNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="video not found")
    return [CommentPublic.model_validate(comment) for comment in comments]
