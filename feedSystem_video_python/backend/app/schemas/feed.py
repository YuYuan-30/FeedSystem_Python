from pydantic import BaseModel, Field


class FeedAuthor(BaseModel):
    id: int
    username: str


class FeedVideoItem(BaseModel):
    id: int
    author: FeedAuthor
    title: str
    description: str
    play_url: str
    cover_url: str
    create_time: int
    likes_count: int
    is_liked: bool


class ListLatestRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    latest_time: int = Field(default=0, ge=0)


class ListLatestResponse(BaseModel):
    video_list: list[FeedVideoItem]
    next_time: int
    has_more: bool


class ListByFollowingRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    latest_time: int = Field(default=0, ge=0)


class ListByFollowingResponse(BaseModel):
    video_list: list[FeedVideoItem]
    next_time: int
    has_more: bool


class ListByTagRequest(BaseModel):
    tag_name: str = Field(min_length=1, max_length=100)
    limit: int = Field(default=10, ge=1, le=50)
    latest_time: int = Field(default=0, ge=0)


class ListByTagResponse(BaseModel):
    video_list: list[FeedVideoItem]
    next_time: int
    has_more: bool


class ListLikesCountRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)
    likes_count_before: int | None = Field(default=None, ge=0)
    id_before: int | None = Field(default=None, gt=0)


class ListLikesCountResponse(BaseModel):
    video_list: list[FeedVideoItem]
    next_likes_count_before: int | None = None
    next_id_before: int | None = None
    has_more: bool
