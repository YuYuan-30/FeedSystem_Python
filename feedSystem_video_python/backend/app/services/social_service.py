from sqlalchemy.exc import IntegrityError

from app.core.auth import CurrentUser
from app.models.account import Account
from app.repositories.account_repo import AccountRepository
from app.repositories.social_repo import SocialRepository


class AccountNotFoundError(Exception):
    pass


class AlreadyFollowedError(Exception):
    pass


class CannotFollowSelfError(Exception):
    pass


class NotFollowedError(Exception):
    pass


class SocialService:
    def __init__(self, social_repo: SocialRepository, account_repo: AccountRepository):
        """注入关注关系仓储和账号仓储，让业务层同时校验账号与关系规则。"""
        self.social_repo = social_repo
        self.account_repo = account_repo

    async def follow(self, current_user: CurrentUser, vlogger_id: int) -> None:
        """关注作者：不能关注自己，作者必须存在，同一关系不能重复创建。"""
        if current_user.id == vlogger_id:
            raise CannotFollowSelfError
        if await self.account_repo.find_by_id(vlogger_id) is None:
            raise AccountNotFoundError
        if await self.social_repo.is_followed(current_user.id, vlogger_id):
            raise AlreadyFollowedError
        try:
            await self.social_repo.follow(current_user.id, vlogger_id)
        except IntegrityError as exc:
            raise AlreadyFollowedError from exc

    async def unfollow(self, current_user: CurrentUser, vlogger_id: int) -> None:
        """取消关注：作者必须存在，且当前用户已经关注过该作者。"""
        if await self.account_repo.find_by_id(vlogger_id) is None:
            raise AccountNotFoundError
        deleted = await self.social_repo.unfollow(current_user.id, vlogger_id)
        if not deleted:
            raise NotFollowedError

    async def get_all_followers(self, current_user: CurrentUser, vlogger_id: int | None) -> tuple[list[Account], int]:
        """查询粉丝列表：不传 vlogger_id 时默认查当前登录用户的粉丝。"""
        target_id = vlogger_id or current_user.id
        if await self.account_repo.find_by_id(target_id) is None:
            raise AccountNotFoundError
        followers = await self.social_repo.list_followers(target_id)
        count = await self.social_repo.count_followers(target_id)
        return followers, count

    async def get_all_vloggers(self, current_user: CurrentUser, follower_id: int | None) -> tuple[list[Account], int]:
        """查询关注列表：不传 follower_id 时默认查当前登录用户关注了谁。"""
        target_id = follower_id or current_user.id
        if await self.account_repo.find_by_id(target_id) is None:
            raise AccountNotFoundError
        vloggers = await self.social_repo.list_vloggers(target_id)
        count = await self.social_repo.count_vloggers(target_id)
        return vloggers, count

    async def get_counts(self, current_user: CurrentUser) -> tuple[int, int]:
        """查询当前用户的粉丝数和关注数，方便前端账号区域展示。"""
        follower_count = await self.social_repo.count_followers(current_user.id)
        vlogger_count = await self.social_repo.count_vloggers(current_user.id)
        return follower_count, vlogger_count
