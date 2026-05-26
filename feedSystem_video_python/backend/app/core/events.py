from dataclasses import dataclass


@dataclass(slots=True)
class EventPublisher:
    """事件发布扩展点；当前不接 MQ，所有方法返回 False 让业务走同步 MySQL。"""

    async def publish_like(self, account_id: int, video_id: int) -> bool:
        """预留点赞事件发布；未来接 RabbitMQ 后成功发布可返回 True。"""
        return False

    async def publish_unlike(self, account_id: int, video_id: int) -> bool:
        """预留取消点赞事件发布；当前 MVP 不做异步消费。"""
        return False

    async def publish_comment(self, account_id: int, video_id: int, content: str) -> bool:
        """预留评论事件发布；当前接口仍同步写库以便直接返回评论对象。"""
        return False

    async def publish_follow(self, follower_id: int, vlogger_id: int) -> bool:
        """预留关注事件发布；未来可由 worker 异步写 socials 表。"""
        return False

    async def publish_unfollow(self, follower_id: int, vlogger_id: int) -> bool:
        """预留取关事件发布；当前 MVP 仍同步删除关注关系。"""
        return False
