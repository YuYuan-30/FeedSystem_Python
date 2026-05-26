from app.core.auth import CurrentUser
from app.core.events import EventPublisher
from app.core.redis import delete_cache_key, video_detail_cache_key
from app.models.comment import Comment
from app.repositories.comment_repo import CommentRepository
from app.repositories.video_repo import VideoRepository


class CommentNotFoundError(Exception):
    pass


class CommentForbiddenError(Exception):
    pass


class VideoNotFoundError(Exception):
    pass


class CommentService:
    def __init__(
        self,
        comment_repo: CommentRepository,
        video_repo: VideoRepository,
        publisher: EventPublisher | None = None,
    ):
        """注入评论、视频 Repository 和事件发布器，预留评论异步化扩展点。"""
        self.comment_repo = comment_repo
        self.video_repo = video_repo
        self.publisher = publisher or EventPublisher()

    async def publish(self, current_user: CurrentUser, video_id: int, content: str) -> Comment:
        """发布评论：校验视频存在，写入评论，并增加视频热度。"""
        content = content.strip()
        if not await self.video_repo.exists(video_id):
            raise VideoNotFoundError
        await self.publisher.publish_comment(current_user.id, video_id, content)
        comment = await self.comment_repo.create(
            video_id=video_id,
            author_id=current_user.id,
            username=current_user.username,
            content=content,
        )
        await self.video_repo.increment_popularity(video_id)
        await delete_cache_key(video_detail_cache_key(video_id))
        return comment

    async def delete(self, current_user: CurrentUser, comment_id: int) -> None:
        """删除评论：只有评论作者本人可以删除，删除后降低视频热度。"""
        comment = await self.comment_repo.get_by_id(comment_id)
        if comment is None:
            raise CommentNotFoundError
        if comment.author_id != current_user.id:
            raise CommentForbiddenError
        deleted = await self.comment_repo.delete_by_id(comment_id)
        if not deleted:
            raise CommentNotFoundError
        await self.video_repo.decrement_popularity(comment.video_id)
        await delete_cache_key(video_detail_cache_key(comment.video_id))

    async def list_all(self, video_id: int) -> list[Comment]:
        """查询视频评论列表：先校验视频存在，再返回该视频下的评论。"""
        if not await self.video_repo.exists(video_id):
            raise VideoNotFoundError
        return await self.comment_repo.list_by_video_id(video_id)
