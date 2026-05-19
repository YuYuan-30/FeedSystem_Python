from sqlalchemy.exc import IntegrityError

from app.core.auth import CurrentUser
from app.core.redis import delete_cache_key, video_detail_cache_key
from app.repositories.like_repo import LikeRepository
from app.repositories.video_repo import VideoRepository


class VideoNotFoundError(Exception):
    pass


class AlreadyLikedError(Exception):
    pass


class NotLikedError(Exception):
    pass


class LikeService:
    def __init__(self, like_repo: LikeRepository, video_repo: VideoRepository):
        """注入点赞关系和视频数据访问对象，保证点赞关系和计数字段一起处理。"""
        self.like_repo = like_repo
        self.video_repo = video_repo

    async def like(self, current_user: CurrentUser, video_id: int) -> None:
        """点赞业务：校验视频存在，插入点赞关系，并增加视频冗余计数。"""
        if not await self.video_repo.exists(video_id):
            raise VideoNotFoundError
        if await self.like_repo.is_liked(video_id, current_user.id):
            raise AlreadyLikedError

        try:
            await self.like_repo.create(video_id=video_id, account_id=current_user.id)
        except IntegrityError as exc:
            raise AlreadyLikedError from exc
        await self.video_repo.increment_like_counters(video_id)
        await delete_cache_key(video_detail_cache_key(video_id))

    async def unlike(self, current_user: CurrentUser, video_id: int) -> None:
        """取消点赞业务：删除点赞关系，并用 SQL 表达式安全减少视频计数。"""
        if not await self.video_repo.exists(video_id):
            raise VideoNotFoundError
        deleted = await self.like_repo.delete(video_id=video_id, account_id=current_user.id)
        if not deleted:
            raise NotLikedError
        await self.video_repo.decrement_like_counters(video_id)
        await delete_cache_key(video_detail_cache_key(video_id))

    async def is_liked(self, current_user: CurrentUser, video_id: int) -> bool:
        """查询当前用户是否点赞了某个视频，用于详情页和 Feed 个性化字段。"""
        if not await self.video_repo.exists(video_id):
            raise VideoNotFoundError
        return await self.like_repo.is_liked(video_id, current_user.id)
