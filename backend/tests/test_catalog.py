from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.models.album import Album
from app.models.artist import Artist
from app.models.category import Category
from app.models.song import Song
from app.models.song_category import SongCategory
from app.models.user import User


@pytest.mark.asyncio
async def test_list_catalog_songs_with_filters(client: TestClient, db_session) -> None:
    artist = Artist(name="Mohammed Rafi")
    album = Album(title="Kohra", release_year=1964)
    category = Category(name="Melody Classics", slug="melody-classics", description="Classic melodies")
    db_session.add_all([artist, album, category])
    await db_session.flush()

    song = Song(
        title="Kya Hua Tera Wada",
        slug="kya-hua-tera-wada",
        artist_id=artist.id,
        album_id=album.id,
        movie_name="Kohra",
        release_year=1964,
        language="Hindi",
        duration_seconds=252,
        description="A classic melody.",
        cover_url="https://example.com/cover.jpg",
        is_featured=True,
        is_published=True,
    )
    db_session.add(song)
    await db_session.flush()
    db_session.add(SongCategory(song_id=song.id, category_id=category.id))
    await db_session.commit()

    response = client.get("/api/v1/catalog/songs?language=Hindi&featured=true&category=melody-classics")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["slug"] == "kya-hua-tera-wada"


@pytest.mark.asyncio
async def test_admin_can_create_catalog_song(client: TestClient, db_session) -> None:
    user = User(name="Admin", email="admin.catalog@example.com", password_hash="placeholder", role="admin", is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = jwt.encode({"sub": str(user.id), "role": user.role, "exp": 9999999999}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    payload = {
        "title": "Main Kya Karoon",
        "slug": "main-kya-karoon",
        "artist_name": "Lata Mangeshkar",
        "album_title": "Sangam",
        "movie_name": "Sangam",
        "release_year": 1964,
        "language": "Hindi",
        "duration_seconds": 240,
        "description": "A well-loved classic",
        "category_slugs": ["melody-classics"],
        "is_featured": True,
    }

    response = client.post(
        "/api/v1/catalog/songs",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["slug"] == "main-kya-karoon"


@pytest.mark.asyncio
async def test_non_admin_cannot_create_catalog_song(client: TestClient, db_session) -> None:
    user = User(name="User", email="user.catalog@example.com", password_hash="placeholder", role="user", is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = jwt.encode({"sub": str(user.id), "role": user.role, "exp": 9999999999}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    response = client.post(
        "/api/v1/catalog/songs",
        json={
            "title": "Test Song",
            "slug": "test-song",
            "artist_name": "Test Artist",
            "album_title": "Test Album",
            "movie_name": "Test Movie",
            "language": "Hindi",
            "duration_seconds": 180,
            "category_slugs": ["melody-classics"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
