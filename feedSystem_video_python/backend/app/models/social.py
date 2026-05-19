from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Social(Base):
    __tablename__ = "socials"
    __table_args__ = (
        UniqueConstraint("follower_id", "vlogger_id", name="uq_socials_follower_vlogger"),
        Index("ix_socials_follower_id", "follower_id"),
        Index("ix_socials_vlogger_id", "vlogger_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    follower_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    vlogger_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
