from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ExternalMusicLink(Base):
    __tablename__ = "external_music_links"

    __table_args__ = (UniqueConstraint("provider", "external_id", name="uq_external_provider_external_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    song_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("songs.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    official_url: Mapped[str] = mapped_column(String(500), nullable=False)
    provider_title: Mapped[str | None] = mapped_column(String(250), nullable=True)
    provider_artist: Mapped[str | None] = mapped_column(String(180), nullable=True)
    provider_thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    song: Mapped["Song"] = relationship(back_populates="external_links")
