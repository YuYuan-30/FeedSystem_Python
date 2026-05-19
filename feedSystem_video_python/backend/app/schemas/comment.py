from datetime import datetime

from pydantic import BaseModel, Field


class PublishCommentRequest(BaseModel):
    video_id: int = Field(gt=0)
    content: str = Field(min_length=1, max_length=500)


class DeleteCommentRequest(BaseModel):
    id: int = Field(gt=0)


class ListCommentsRequest(BaseModel):
    video_id: int = Field(gt=0)


class CommentPublic(BaseModel):
    id: int
    video_id: int
    author_id: int
    username: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
