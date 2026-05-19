from pydantic import BaseModel, Field


class LikeRequest(BaseModel):
    video_id: int = Field(gt=0)


class IsLikedResponse(BaseModel):
    is_liked: bool
