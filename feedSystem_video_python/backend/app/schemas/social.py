from pydantic import BaseModel, Field

from app.schemas.account import AccountPublic


class FollowRequest(BaseModel):
    vlogger_id: int = Field(gt=0)


class UnfollowRequest(BaseModel):
    vlogger_id: int = Field(gt=0)


class GetAllFollowersRequest(BaseModel):
    vlogger_id: int | None = Field(default=None, gt=0)


class GetAllVloggersRequest(BaseModel):
    follower_id: int | None = Field(default=None, gt=0)


class GetAllFollowersResponse(BaseModel):
    followers: list[AccountPublic]
    follower_count: int


class GetAllVloggersResponse(BaseModel):
    vloggers: list[AccountPublic]
    vlogger_count: int


class SocialCountsResponse(BaseModel):
    follower_count: int
    vlogger_count: int
