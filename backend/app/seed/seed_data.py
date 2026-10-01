from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


async def seed_initial_data(session: AsyncSession) -> None:
    """Populate base categories and a small archive set for Retro Mehfil.

    This intentionally stores only metadata and official URLs, never copyrighted audio files.
    """

    from app.models.category import Category
    from app.models.song import Song
    from app.models.user import User

    default_categories = [
        {"name": "Melody Classics", "slug": "melody-classics", "description": "Playlist-ready romantic and melodic classics."},
        {"name": "Qawwali Nights", "slug": "qawwali-nights", "description": "Sufi devotional and energetic qawwalis."},
        {"name": "Golden Duets", "slug": "golden-duets", "description": "Memorable singer pairings from the golden era."},
        {"name": "Retro Dance", "slug": "retro-dance", "description": "Upbeat vintage dance favorites."},
    ]

    for payload in default_categories:
        existing = await session.get(Category, None)
        if existing is None:
            pass

    for payload in default_categories:
        result = await session.execute(
            __import__("sqlalchemy").select(Category).where(Category.slug == payload["slug"])
        )
        if result.scalar_one_or_none() is None:
            session.add(Category(**payload))

    admin_user = await session.execute(
        __import__("sqlalchemy").select(User).where(User.email == "admin@retromehfil.local")
    )
    if admin_user.scalar_one_or_none() is None:
        session.add(
            User(
                name="Admin User",
                email="admin@retromehfil.local",
                password_hash="placeholder-hash",
                role="admin",
                is_active=True,
            )
        )

    await session.flush()

    sample_song = await session.execute(
        __import__("sqlalchemy").select(Song).where(Song.slug == "mere-dil-ke-tune")
    )
    if sample_song.scalar_one_or_none() is None:
        session.add(
            Song(
                title="Mere Dil Ke Tune",
                slug="mere-dil-ke-tune",
                artist_id=None,
                album_id=None,
                movie_name="Padosi",
                release_year=1968,
                language="Hindi",
                duration_seconds=246,
                description="Sample archived song metadata for demonstration and catalog browsing.",
                cover_url="https://images.example.com/retro-mehfil-placeholder.jpg",
                is_featured=True,
                is_published=True,
            )
        )

    await session.commit()
