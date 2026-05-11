from datetime import datetime

from pydantic import BaseModel, Field


class PublishVideoRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=255)
    play_url: str = Field(min_length=1, max_length=512)
    cover_url: str = Field(min_length=1, max_length=512)


class ListByAuthorIDRequest(BaseModel):
    author_id: int = Field(gt=0)


class GetVideoDetailRequest(BaseModel):
    id: int = Field(gt=0)


class VideoPublic(BaseModel):
    id: int
    author_id: int
    username: str
    title: str
    description: str
    play_url: str
    cover_url: str
    likes_count: int
    popularity: int
    create_time: datetime

    model_config = {"from_attributes": True}
