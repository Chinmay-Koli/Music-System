from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SongCategory(Base):
    __tablename__ = "song_categories"

    song_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("songs.id"), primary_key=True)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id"), primary_key=True)
