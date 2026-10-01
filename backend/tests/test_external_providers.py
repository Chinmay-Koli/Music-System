from __future__ import annotations

import pytest
from jose import jwt

from app.core.config import settings
from app.models.song import Song
from app.models.user import User


def _auth_headers(user: User, role: str | None = None) -> dict[str, str]:
    token = jwt.encode(
        {"sub": str(user.id), "role": role or user.role, "exp": 9999999999},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_admin_can_attach_external_link(client, db_session) -> None:
    user = User(
        name="Admin Linker",
        email="provider.admin@example.com",
        password_hash="placeholder",
        role="admin",
        is_active=True,
    )
    song = Song(
        title="Mera Naam Joker",
        slug="mera-naam-joker",
        movie_name="Mera Naam Joker",
        release_year=1970,
        language="Hindi",
        duration_seconds=220,
        description="Classic single",
        is_featured=False,
        is_published=True,
    )
    db_session.add_all([user, song])
    await db_session.commit()

    payload = {
        "provider": "youtube",
        "external_id": "abc123youtube",
        "official_url": "https://youtu.be/abc123youtube",
        "provider_title": "Mera Naam Joker",
        "provider_artist": "Kishore Kumar",
        "provider_thumbnail_url": "https://img.example.com/thumb.jpg",
        "is_verified": True,
    }

    response = client.post(
        f"/api/v1/songs/{song.id}/external-links",
        json=payload,
        headers=_auth_headers(user),
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["provider"] == "youtube"

    response = client.get(f"/api/v1/songs/{song.id}/external-links", headers=_auth_headers(user))
    assert response.status_code == 200, response.text
    assert len(response.json()["data"]) == 1
    assert response.json()["data"][0]["provider"] == "youtube"


@pytest.mark.asyncio
async def test_duplicate_external_link_is_rejected(client, db_session) -> None:
    user = User(
        name="Provider User",
        email="provider.user@example.com",
        password_hash="placeholder",
        role="admin",
        is_active=True,
    )
    song = Song(
        title="Pyaar Kiye Ja",
        slug="pyaar-kiye-ja",
        movie_name="Pyaar Kiye Ja",
        release_year=1966,
        language="Hindi",
        duration_seconds=180,
        description="Classic track",
        is_featured=True,
        is_published=True,
    )
    db_session.add_all([user, song])
    await db_session.commit()

    client.post(
        f"/api/v1/songs/{song.id}/external-links",
        json={
            "provider": "spotify",
            "external_id": "track-42",
            "official_url": "https://open.spotify.com/track/42",
            "provider_title": "Pyaar Kiye Ja",
        },
        headers=_auth_headers(user),
    )

    response = client.post(
        f"/api/v1/songs/{song.id}/external-links",
        json={
            "provider": "spotify",
            "external_id": "track-42",
            "official_url": "https://open.spotify.com/track/42",
            "provider_title": "Pyaar Kiye Ja",
        },
        headers=_auth_headers(user),
    )
    assert response.status_code == 409, response.text
