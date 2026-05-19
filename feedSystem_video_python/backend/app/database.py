from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.sql_echo,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """给每个请求提供一个独立的数据库会话，请求结束后自动关闭。"""
    async with AsyncSessionLocal() as session:
        yield session


async def init_models() -> None:
    """应用启动时创建已声明的数据库表，包含账号、视频、点赞、评论、关注和标签。"""
    import app.models.account  # noqa: F401
    import app.models.comment  # noqa: F401
    import app.models.like  # noqa: F401
    import app.models.social  # noqa: F401
    import app.models.tag  # noqa: F401
    import app.models.video  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
