from app.core.auth import CurrentUser
from app.core.redis import (
    delete_cache_prefix,
    get_json_cache,
    set_json_cache,
    video_detail_cache_key,
)
from app.core.tags import extract_tags
from app.models.video import Video
from app.repositories.tag_repo import TagRepository
from app.repositories.video_repo import VideoRepository
from app.schemas.video import VideoPublic


class VideoNotFoundError(Exception):
    pass


class VideoService:
    def __init__(self, repo: VideoRepository, tag_repo: TagRepository):
        """注入视频和标签数据访问对象，让业务层专注处理视频发布规则。"""
        self.repo = repo
        self.tag_repo = tag_repo

    async def publish(
        self,
        current_user: CurrentUser,
        title: str,
        description: str,
        play_url: str,
        cover_url: str,
    ) -> Video:
        """发布视频：写入视频元数据，提取 #标签，并清理最新 Feed 短缓存。"""
        video = await self.repo.create(
            author_id=current_user.id,
            username=current_user.username,
            title=title.strip(),
            description=description.strip(),
            play_url=play_url.strip(),
            cover_url=cover_url.strip(),
        )
        tag_names = extract_tags(f"{video.title} {video.description}")
        if tag_names:
            await self.tag_repo.attach_tags(video.id, tag_names)
        await delete_cache_prefix("v1:feed:latest:")
        return video

    async def list_by_author_id(self, author_id: int) -> list[Video]:
        """查询某个作者的视频列表，业务层暂时只转发 Repository 的倒序结果。"""
        return await self.repo.list_by_author_id(author_id)

    async def get_detail(self, video_id: int) -> VideoPublic:
        """查询视频详情：先读 Redis，缓存未命中再查 MySQL 并回填缓存。"""
        cache_key = video_detail_cache_key(video_id)
        cached = await get_json_cache(cache_key)
        if cached is not None:
            return VideoPublic.model_validate(cached)

        video = await self.repo.get_by_id(video_id)
        if video is None:
            raise VideoNotFoundError
        public = VideoPublic.model_validate(video)
        await set_json_cache(cache_key, public.model_dump(mode="json"), ttl_seconds=300)
        return public
