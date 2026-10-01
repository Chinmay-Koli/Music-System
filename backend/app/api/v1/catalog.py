from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.auth import require_admin
from app.core.database import get_db
from app.models.album import Album
from app.models.artist import Artist
from app.models.category import Category
from app.models.song import Song
from app.models.song_category import SongCategory

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])


class SongCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=220)
    artist_name: str | None = None
    album_title: str | None = None
    movie_name: str | None = None
    release_year: int | None = None
    language: str = "Hindi"
    duration_seconds: int | None = None
    description: str | None = None
    cover_url: str | None = None
    category_slugs: list[str] = []
    is_featured: bool = False


def serialize_song(song: Song) -> dict[str, Any]:
    return {
        "id": str(song.id),
        "title": song.title,
        "slug": song.slug,
        "artist_name": song.artist.name if song.artist else None,
        "album_title": song.album.title if song.album else None,
        "movie_name": song.movie_name,
        "release_year": song.release_year,
        "language": song.language,
        "duration_seconds": song.duration_seconds,
        "description": song.description,
        "cover_url": song.cover_url,
        "is_featured": song.is_featured,
        "is_published": song.is_published,
        "categories": [category.slug for category in song.categories],
    }


@router.get("/songs")
async def list_songs(
    language: str | None = Query(default=None),
    featured: bool | None = Query(default=None),
    category: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = (
        select(Song)
        .options(selectinload(Song.artist), selectinload(Song.album), selectinload(Song.categories))
        .order_by(Song.created_at.desc())
    )

    if language:
        query = query.where(Song.language == language)
    if featured is not None:
        query = query.where(Song.is_featured == featured)
    if category:
        query = query.join(SongCategory, Song.id == SongCategory.song_id).join(
            Category, SongCategory.category_id == Category.id
        ).where(Category.slug == category)

    result = await db.execute(query)
    songs = result.scalars().unique().all()
    return {"success": True, "data": [serialize_song(song) for song in songs]}


@router.post("/songs", status_code=status.HTTP_201_CREATED)
async def create_song(
    payload: SongCreateRequest,
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    del current_user
    slug = payload.slug.strip()
    result = await db.execute(select(Song).where(Song.slug == slug))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Song slug already exists")

    artist = None
    if payload.artist_name and payload.artist_name.strip():
        artist_name = payload.artist_name.strip()
        artist_result = await db.execute(select(Artist).where(Artist.name == artist_name))
        artist = artist_result.scalar_one_or_none()
        if artist is None:
            artist = Artist(name=artist_name)
            db.add(artist)
            await db.flush()

    album = None
    if payload.album_title and payload.album_title.strip():
        album_title = payload.album_title.strip()
        album_result = await db.execute(select(Album).where(Album.title == album_title))
        album = album_result.scalar_one_or_none()
        if album is None:
            album = Album(title=album_title, release_year=payload.release_year)
            db.add(album)
            await db.flush()

    category_objects: list[Category] = []
    for category_slug in payload.category_slugs:
        normalized = category_slug.strip()
        if not normalized:
            continue
        category_result = await db.execute(select(Category).where(Category.slug == normalized))
        category = category_result.scalar_one_or_none()
        if category is None:
            category = Category(name=normalized.replace("-", " ").title(), slug=normalized, description="")
            db.add(category)
            await db.flush()
        category_objects.append(category)

    song = Song(
        title=payload.title.strip(),
        slug=slug,
        artist_id=artist.id if artist else None,
        album_id=album.id if album else None,
        movie_name=payload.movie_name.strip() if payload.movie_name else None,
        release_year=payload.release_year,
        language=payload.language,
        duration_seconds=payload.duration_seconds,
        description=payload.description,
        cover_url=payload.cover_url,
        is_featured=payload.is_featured,
        is_published=True,
    )
    db.add(song)
    await db.flush()

    for category in category_objects:
        db.add(SongCategory(song_id=song.id, category_id=category.id))

    await db.commit()
    await db.refresh(song)
    await db.refresh(song, attribute_names=["artist", "album"])

    response_payload = {
        "id": str(song.id),
        "title": song.title,
        "slug": song.slug,
        "artist_name": song.artist.name if song.artist else None,
        "album_title": song.album.title if song.album else None,
        "movie_name": song.movie_name,
        "release_year": song.release_year,
        "language": song.language,
        "duration_seconds": song.duration_seconds,
        "description": song.description,
        "cover_url": song.cover_url,
        "is_featured": song.is_featured,
        "is_published": song.is_published,
        "categories": [category.slug for category in category_objects],
    }
    return {"success": True, "data": response_payload}
