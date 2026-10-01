from __future__ import annotations

import pytest
from jose import jwt

from app.core.config import settings
from app.models.album import Album
from app.models.artist import Artist
from app.models.song import Song
from app.models.user import User


def _auth_headers(user: User) -> dict[str, str]:
    token = jwt.encode(
        {"sub": str(user.id), "role": user.role, "exp": 9999999999},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_playlist_and_add_song(client, db_session) -> None:
    user = User(name="Playlist User", email="library.user@example.com", password_hash="placeholder", role="user", is_active=True)
    artist = Artist(name="Lata Mangeshkar")
    album = Album(title="Guide", release_year=1965)
    song = Song(
        title="Tere Mere Sapne",
        slug="tere-mere-sapne",
        artist_id=None,
        album_id=None,
        movie_name="Guide",
        release_year=1965,
        language="Hindi",
        duration_seconds=220,
        description="Classic melody",
        is_featured=True,
        is_published=True,
    )

    db_session.add_all([user, artist, album, song])
    await db_session.flush()
    song.artist_id = artist.id
    song.album_id = album.id
    await db_session.commit()

    response = client.post(
        "/api/v1/playlists",
        json={"title": "Late Night Classics", "description": "Soft melodies after dark", "is_public": True},
        headers=_auth_headers(user),
    )
    assert response.status_code == 201, response.text
    playlist_id = response.json()["data"]["id"]

    response = client.post(
        f"/api/v1/playlists/{playlist_id}/songs",
        json={"song_id": str(song.id)},
        headers=_auth_headers(user),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["song_count"] == 1

    response = client.get(f"/api/v1/playlists/{playlist_id}", headers=_auth_headers(user))
    assert response.status_code == 200, response.text
    assert response.json()["data"]["songs"][0]["title"] == "Tere Mere Sapne"


@pytest.mark.asyncio
async def test_favorites_and_history_are_user_scoped(client, db_session) -> None:
    user = User(name="History User", email="history.user@example.com", password_hash="placeholder", role="user", is_active=True)
    song = Song(
        title="Aaj Phir Jeene Ki Tamanna Hai",
        slug="aaj-phir-jeene-ki-tamanna-hai",
        movie_name="Guide",
        release_year=1965,
        language="Hindi",
        duration_seconds=246,
        description="A nostalgic favorite",
        is_featured=False,
        is_published=True,
    )
    db_session.add_all([user, song])
    await db_session.commit()

    response = client.post(f"/api/v1/favorites/{song.id}", headers=_auth_headers(user))
    assert response.status_code == 201, response.text
    assert response.json()["data"]["is_favorite"] is True

    response = client.get("/api/v1/favorites", headers=_auth_headers(user))
    assert response.status_code == 200, response.text
    assert len(response.json()["data"]) == 1

    response = client.post(
        "/api/v1/history",
        json={"song_id": str(song.id), "progress_seconds": 120},
        headers=_auth_headers(user),
    )
    assert response.status_code == 201, response.text

    response = client.get("/api/v1/history", headers=_auth_headers(user))
    assert response.status_code == 200, response.text
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["song_title"] == "Aaj Phir Jeene Ki Tamanna Hai"
