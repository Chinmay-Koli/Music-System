from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    artist_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("artists.id"), nullable=True, index=True)
    album_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("albums.id"), nullable=True, index=True)
    movie_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    release_year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    language: Mapped[str] = mapped_column(String(80), nullable=False, default="Hindi")
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    artist: Mapped["Artist"] = relationship(back_populates="songs")
    album: Mapped["Album"] = relationship(back_populates="songs")
    categories: Mapped[list["Category"]] = relationship(back_populates="songs", secondary="song_categories")
    external_links: Mapped[list["ExternalMusicLink"]] = relationship(back_populates="song", cascade="all, delete-orphan")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="song", cascade="all, delete-orphan")
    history_entries: Mapped[list["ListeningHistory"]] = relationship(back_populates="song", cascade="all, delete-orphan")
    playlists: Mapped[list["PlaylistSong"]] = relationship(back_populates="song", cascade="all, delete-orphan")
