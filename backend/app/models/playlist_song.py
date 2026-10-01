from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PlaylistSong(Base):
    __tablename__ = "playlist_songs"

    playlist_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("playlists.id"), primary_key=True)
    song_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("songs.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    playlist: Mapped["Playlist"] = relationship(back_populates="songs")
    song: Mapped["Song"] = relationship(back_populates="playlists")
