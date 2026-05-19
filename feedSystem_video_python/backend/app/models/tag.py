from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)


class VideoTag(Base):
    __tablename__ = "video_tags"
    __table_args__ = (
        UniqueConstraint("video_id", "tag_id", name="uq_video_tags_video_tag"),
        Index("ix_video_tags_video_id", "video_id"),
        Index("ix_video_tags_tag_id", "tag_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False)
