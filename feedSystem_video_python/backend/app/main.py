from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.account import router as account_router
from app.api.comment import router as comment_router
from app.api.feed import router as feed_router
from app.api.like import router as like_router
from app.api.social import router as social_router
from app.api.video import router as video_router
from app.config import get_settings
from app.core.redis import close_redis
from app.database import init_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期钩子：启动时建表，关闭时释放 Redis 连接。"""
    await init_models()
    yield
    await close_redis()


settings = get_settings()

app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(account_router)
app.include_router(video_router)
app.include_router(like_router)
app.include_router(comment_router)
app.include_router(feed_router)
app.include_router(social_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """健康检查接口：用于确认后端进程已经正常响应 HTTP 请求。"""
    return {"status": "ok"}
