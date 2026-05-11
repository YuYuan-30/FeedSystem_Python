from app.core.auth import CurrentUser
from app.models.video import Video
from app.repositories.video_repo import VideoRepository


class VideoNotFoundError(Exception):
    pass


class VideoService:
    def __init__(self, repo: VideoRepository):
        """注入视频数据访问对象，让业务层专注处理视频规则。"""
        self.repo = repo

    async def publish(
        self,
        current_user: CurrentUser,
        title: str,
        description: str,
        play_url: str,
        cover_url: str,
    ) -> Video:
        """发布视频：使用登录用户作为作者，把视频元数据写入 MySQL。"""
        return await self.repo.create(
            author_id=current_user.id,
            username=current_user.username,
            title=title.strip(),
            description=description.strip(),
            play_url=play_url.strip(),
            cover_url=cover_url.strip(),
        )

    async def list_by_author_id(self, author_id: int) -> list[Video]:
        """查询某个作者的视频列表，业务层暂时只转发 Repository 的倒序结果。"""
        return await self.repo.list_by_author_id(author_id)

    async def get_detail(self, video_id: int) -> Video:
        """查询视频详情；如果视频不存在，抛出业务异常交给 API 层转成 404。"""
        video = await self.repo.get_by_id(video_id)
        if video is None:
            raise VideoNotFoundError
        return video
