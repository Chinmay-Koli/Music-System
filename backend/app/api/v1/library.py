from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.auth import get_current_user, require_admin
from app.core.database import get_db
from app.models.external_link import ExternalMusicLink
from app.models.favorite import Favorite
from app.models.listening_history import ListeningHistory
from app.models.playlist import Playlist
from app.models.playlist_song import PlaylistSong
from app.models.song import Song
from app.models.user import User

router = APIRouter(prefix="/api/v1", tags=["library"])


class PlaylistCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=180)
    description: str | None = None
    cover_url: str | None = None
    is_public: bool = False


class PlaylistSongAddRequest(BaseModel):
    song_id: str = Field(..., min_length=1)


class FavoriteCreateRequest(BaseModel):
    song_id: str = Field(..., min_length=1)


class ListeningHistoryCreateRequest(BaseModel):
    song_id: str = Field(..., min_length=1)
    progress_seconds: int | None = Field(default=0, ge=0)


class ExternalLinkCreateRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=40)
    external_id: str = Field(..., min_length=1, max_length=200)
    official_url: str = Field(..., min_length=1, max_length=500)
    provider_title: str | None = Field(default=None, max_length=250)
    provider_artist: str | None = Field(default=None, max_length=180)
    provider_thumbnail_url: str | None = Field(default=None, max_length=500)
    is_verified: bool = False


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "playlist"


def _serialize_playlist(playlist: Playlist, song_count: int | None = None) -> dict[str, Any]:
    return {
        "id": str(playlist.id),
        "title": playlist.title,
        "slug": playlist.slug,
        "description": playlist.description,
        "cover_url": playlist.cover_url,
        "is_public": playlist.is_public,
        "created_by": str(playlist.created_by),
        "song_count": song_count if song_count is not None else len(playlist.songs),
        "created_at": playlist.created_at.isoformat(),
    }


def _serialize_playlist_detail(playlist: Playlist) -> dict[str, Any]:
    songs = []
    for entry in sorted(playlist.songs, key=lambda item: item.position):
        song = entry.song
        songs.append(
            {
                "id": str(song.id),
                "title": song.title,
                "slug": song.slug,
                "artist_name": song.artist.name if song.artist else None,
                "album_title": song.album.title if song.album else None,
                "duration_seconds": song.duration_seconds,
            }
        )
    return {
        "id": str(playlist.id),
        "title": playlist.title,
        "slug": playlist.slug,
        "description": playlist.description,
        "cover_url": playlist.cover_url,
        "is_public": playlist.is_public,
        "created_by": str(playlist.created_by),
        "song_count": len(songs),
        "songs": songs,
        "created_at": playlist.created_at.isoformat(),
    }


@router.post("/playlists", status_code=status.HTTP_201_CREATED)
async def create_playlist(
    payload: PlaylistCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    title = payload.title.strip()
    slug = _slugify(title)
    unique_slug = slug
    suffix = 1
    while True:
        existing = await db.scalar(select(Playlist).where(Playlist.slug == unique_slug))
        if existing is None:
            break
        unique_slug = f"{slug}-{suffix}"
        suffix += 1

    playlist = Playlist(
        title=title,
        slug=unique_slug,
        description=payload.description.strip() if payload.description else None,
        cover_url=payload.cover_url,
        is_public=payload.is_public,
        created_by=current_user.id,
    )
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)
    return {"success": True, "data": _serialize_playlist(playlist, 0)}


@router.get("/playlists/{playlist_id}")
async def get_playlist(
    playlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(Playlist)
        .options(selectinload(Playlist.songs).selectinload(PlaylistSong.song).selectinload(Song.artist), selectinload(Playlist.songs).selectinload(PlaylistSong.song).selectinload(Song.album))
        .where(Playlist.id == playlist_id)
    )
    playlist = result.scalar_one_or_none()
    if playlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    if playlist.created_by != current_user.id and not playlist.is_public:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this playlist")
    return {"success": True, "data": _serialize_playlist_detail(playlist)}


@router.post("/playlists/{playlist_id}/songs", status_code=status.HTTP_201_CREATED)
async def add_song_to_playlist(
    playlist_id: uuid.UUID,
    payload: PlaylistSongAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    playlist_result = await db.execute(select(Playlist).where(Playlist.id == playlist_id))
    playlist = playlist_result.scalar_one_or_none()
    if playlist is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not found")
    if playlist.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the playlist owner can add songs")

    song_id = uuid.UUID(payload.song_id)
    song = await db.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    existing = await db.scalar(
        select(PlaylistSong).where(PlaylistSong.playlist_id == playlist.id, PlaylistSong.song_id == song.id)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Song already exists in playlist")

    song_count = await db.scalar(
        select(func.count(PlaylistSong.song_id)).where(PlaylistSong.playlist_id == playlist.id)
    )

    playlist_song = PlaylistSong(playlist_id=playlist.id, song_id=song.id, position=int(song_count or 0))
    db.add(playlist_song)
    await db.commit()
    return {
        "success": True,
        "data": {"playlist_id": str(playlist.id), "song_id": str(song.id), "song_count": int(song_count or 0) + 1},
    }


@router.get("/favorites")
async def list_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(Favorite)
        .options(selectinload(Favorite.song))
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )
    favorites = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(favorite.id),
                "song_id": str(favorite.song_id),
                "song_title": favorite.song.title,
                "slug": favorite.song.slug,
                "artist_name": favorite.song.artist.name if favorite.song.artist else None,
            }
            for favorite in favorites
        ],
    }


@router.post("/favorites/{song_id}", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    song_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    song = await db.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    favorite = await db.scalar(select(Favorite).where(Favorite.user_id == current_user.id, Favorite.song_id == song.id))
    if favorite is not None:
        return {"success": True, "data": {"song_id": str(song.id), "is_favorite": True}}

    db.add(Favorite(user_id=current_user.id, song_id=song.id))
    await db.commit()
    return {"success": True, "data": {"song_id": str(song.id), "is_favorite": True}}


@router.post("/history", status_code=status.HTTP_201_CREATED)
async def add_history_entry(
    payload: ListeningHistoryCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    song_id = uuid.UUID(payload.song_id)
    song = await db.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    entry = ListeningHistory(user_id=current_user.id, song_id=song.id, progress_seconds=payload.progress_seconds or 0)
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return {
        "success": True,
        "data": {
            "id": str(entry.id),
            "song_id": str(song.id),
            "song_title": song.title,
            "progress_seconds": entry.progress_seconds,
            "listened_at": entry.listened_at.isoformat(),
        },
    }


@router.get("/history")
async def list_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(
        select(ListeningHistory)
        .options(selectinload(ListeningHistory.song))
        .where(ListeningHistory.user_id == current_user.id)
        .order_by(ListeningHistory.listened_at.desc())
    )
    entries = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(entry.id),
                "song_id": str(entry.song_id),
                "song_title": entry.song.title,
                "progress_seconds": entry.progress_seconds,
                "listened_at": entry.listened_at.isoformat(),
            }
            for entry in entries
        ],
    }


@router.get("/songs/{song_id}/external-links")
async def list_external_links(
    song_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    del current_user
    song = await db.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    result = await db.execute(
        select(ExternalMusicLink)
        .where(ExternalMusicLink.song_id == song.id)
        .order_by(ExternalMusicLink.created_at.desc())
    )
    links = result.scalars().all()
    return {
        "success": True,
        "data": [
            {
                "id": str(link.id),
                "song_id": str(link.song_id),
                "provider": link.provider,
                "external_id": link.external_id,
                "official_url": link.official_url,
                "provider_title": link.provider_title,
                "provider_artist": link.provider_artist,
                "provider_thumbnail_url": link.provider_thumbnail_url,
                "is_verified": link.is_verified,
                "created_at": link.created_at.isoformat(),
            }
            for link in links
        ],
    }


@router.post("/songs/{song_id}/external-links", status_code=status.HTTP_201_CREATED)
async def add_external_link(
    song_id: uuid.UUID,
    payload: ExternalLinkCreateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    del current_user
    song = await db.get(Song, song_id)
    if song is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    existing = await db.scalar(
        select(ExternalMusicLink).where(
            ExternalMusicLink.song_id == song.id,
            ExternalMusicLink.provider == payload.provider,
            ExternalMusicLink.external_id == payload.external_id,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="External link already exists")

    link = ExternalMusicLink(
        song_id=song.id,
        provider=payload.provider.strip().lower(),
        external_id=payload.external_id.strip(),
        official_url=payload.official_url.strip(),
        provider_title=payload.provider_title.strip() if payload.provider_title else None,
        provider_artist=payload.provider_artist.strip() if payload.provider_artist else None,
        provider_thumbnail_url=payload.provider_thumbnail_url.strip() if payload.provider_thumbnail_url else None,
        is_verified=payload.is_verified,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return {
        "success": True,
        "data": {
            "id": str(link.id),
            "song_id": str(link.song_id),
            "provider": link.provider,
            "external_id": link.external_id,
            "official_url": link.official_url,
            "provider_title": link.provider_title,
            "provider_artist": link.provider_artist,
            "provider_thumbnail_url": link.provider_thumbnail_url,
            "is_verified": link.is_verified,
            "created_at": link.created_at.isoformat(),
        },
    }
