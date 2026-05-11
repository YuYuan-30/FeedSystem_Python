from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class FindByIDRequest(BaseModel):
    id: int = Field(gt=0)


class FindByUsernameRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=256)


class AccountPublic(BaseModel):
    id: int
    username: str
    avatar_url: str = ""
    bio: str = ""

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    token: str
    refresh_token: str
    account_id: int
    username: str
