from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Video(Base):
    __tablename__ = "videos"
    __table_args__ = (
        Index("ix_videos_author_id_create_time", "author_id", "create_time"),
        Index("ix_videos_create_time", "create_time"),
        Index("ix_videos_likes_count_id", "likes_count", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    play_url: Mapped[str] = mapped_column(String(512), nullable=False)
    cover_url: Mapped[str] = mapped_column(String(512), nullable=False)
    likes_count: Mapped[int] = mapped_column(default=0, nullable=False)
    popularity: Mapped[int] = mapped_column(default=0, nullable=False)
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
