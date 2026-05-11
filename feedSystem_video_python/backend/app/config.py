from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "feedSystem Video Python"
    database_url: str = "mysql+asyncmy://root:123456@127.0.0.1:3306/feedsystem"
    redis_url: str = "redis://127.0.0.1:6379/0"
    jwt_secret: str = "feedsystem-dev-secret-key-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    sql_echo: bool = False

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """读取并缓存项目配置，避免每次依赖注入时重复解析环境变量。"""
    return Settings()
