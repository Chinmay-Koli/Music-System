from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ListeningHistory(Base):
    __tablename__ = "listening_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    song_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("songs.id"), nullable=False, index=True)
    listened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    progress_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)

    user: Mapped["User"] = relationship(back_populates="listening_history")
    song: Mapped["Song"] = relationship(back_populates="history_entries")
