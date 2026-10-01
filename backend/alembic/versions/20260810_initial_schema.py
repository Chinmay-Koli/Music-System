"""Initial Retro Mehfil schema

Revision ID: 20260810_initial
Revises: 
Create Date: 2026-08-10 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260810_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

    op.create_table(
        "artists",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_artists_name"), "artists", ["name"], unique=False)

    op.create_table(
        "albums",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("release_year", sa.Integer(), nullable=True),
        sa.Column("cover_url", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_albums_title"), "albums", ["title"], unique=False)
    op.create_index(op.f("ix_albums_release_year"), "albums", ["release_year"], unique=False)

    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=False)
    op.create_index(op.f("ix_categories_slug"), "categories", ["slug"], unique=False)

    op.create_table(
        "songs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("artist_id", sa.Uuid(), nullable=True),
        sa.Column("album_id", sa.Uuid(), nullable=True),
        sa.Column("movie_name", sa.String(length=180), nullable=True),
        sa.Column("release_year", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=80), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.String(length=500), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["album_id"], ["albums.id"], name="fk_songs_album_id_albums"),
        sa.ForeignKeyConstraint(["artist_id"], ["artists.id"], name="fk_songs_artist_id_artists"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_songs_slug"),
    )
    op.create_index(op.f("ix_songs_title"), "songs", ["title"], unique=False)
    op.create_index(op.f("ix_songs_slug"), "songs", ["slug"], unique=False)
    op.create_index(op.f("ix_songs_artist_id"), "songs", ["artist_id"], unique=False)
    op.create_index(op.f("ix_songs_album_id"), "songs", ["album_id"], unique=False)
    op.create_index(op.f("ix_songs_release_year"), "songs", ["release_year"], unique=False)

    op.create_table(
        "song_categories",
        sa.Column("song_id", sa.Uuid(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], name="fk_song_categories_category_id_categories"),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], name="fk_song_categories_song_id_songs"),
        sa.PrimaryKeyConstraint("song_id", "category_id"),
    )

    op.create_table(
        "playlists",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_url", sa.String(length=500), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name="fk_playlists_created_by_users"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_playlists_slug"),
    )
    op.create_index(op.f("ix_playlists_title"), "playlists", ["title"], unique=False)
    op.create_index(op.f("ix_playlists_slug"), "playlists", ["slug"], unique=False)
    op.create_index(op.f("ix_playlists_created_by"), "playlists", ["created_by"], unique=False)

    op.create_table(
        "playlist_songs",
        sa.Column("playlist_id", sa.Uuid(), nullable=False),
        sa.Column("song_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["playlist_id"], ["playlists.id"], name="fk_playlist_songs_playlist_id_playlists"),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], name="fk_playlist_songs_song_id_songs"),
        sa.PrimaryKeyConstraint("playlist_id", "song_id"),
    )

    op.create_table(
        "favorites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("song_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], name="fk_favorites_song_id_songs"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_favorites_user_id_users"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "song_id", name="uq_favorites_user_song"),
    )
    op.create_index(op.f("ix_favorites_user_id"), "favorites", ["user_id"], unique=False)
    op.create_index(op.f("ix_favorites_song_id"), "favorites", ["song_id"], unique=False)

    op.create_table(
        "listening_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("song_id", sa.Uuid(), nullable=False),
        sa.Column("listened_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("progress_seconds", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], name="fk_listening_history_song_id_songs"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_listening_history_user_id_users"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_listening_history_user_id"), "listening_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_listening_history_song_id"), "listening_history", ["song_id"], unique=False)
    op.create_index(op.f("ix_listening_history_listened_at"), "listening_history", ["listened_at"], unique=False)

    op.create_table(
        "external_music_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("song_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("external_id", sa.String(length=200), nullable=False),
        sa.Column("official_url", sa.String(length=500), nullable=False),
        sa.Column("provider_title", sa.String(length=250), nullable=True),
        sa.Column("provider_artist", sa.String(length=180), nullable=True),
        sa.Column("provider_thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], name="fk_external_music_links_song_id_songs"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "external_id", name="uq_external_provider_song_id"),
    )
    op.create_index(op.f("ix_external_music_links_song_id"), "external_music_links", ["song_id"], unique=False)
    op.create_index(op.f("ix_external_music_links_provider"), "external_music_links", ["provider"], unique=False)
    op.create_index(op.f("ix_external_music_links_external_id"), "external_music_links", ["external_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_external_music_links_external_id"), table_name="external_music_links")
    op.drop_index(op.f("ix_external_music_links_provider"), table_name="external_music_links")
    op.drop_index(op.f("ix_external_music_links_song_id"), table_name="external_music_links")
    op.drop_table("external_music_links")
    op.drop_index(op.f("ix_listening_history_listened_at"), table_name="listening_history")
    op.drop_index(op.f("ix_listening_history_song_id"), table_name="listening_history")
    op.drop_index(op.f("ix_listening_history_user_id"), table_name="listening_history")
    op.drop_table("listening_history")
    op.drop_index(op.f("ix_favorites_song_id"), table_name="favorites")
    op.drop_index(op.f("ix_favorites_user_id"), table_name="favorites")
    op.drop_table("favorites")
    op.drop_index(op.f("ix_playlist_songs_song_id"), table_name="playlist_songs")
    op.drop_table("playlist_songs")
    op.drop_index(op.f("ix_playlists_created_by"), table_name="playlists")
    op.drop_index(op.f("ix_playlists_slug"), table_name="playlists")
    op.drop_index(op.f("ix_playlists_title"), table_name="playlists")
    op.drop_table("playlists")
    op.drop_table("song_categories")
    op.drop_index(op.f("ix_songs_release_year"), table_name="songs")
    op.drop_index(op.f("ix_songs_album_id"), table_name="songs")
    op.drop_index(op.f("ix_songs_artist_id"), table_name="songs")
    op.drop_index(op.f("ix_songs_slug"), table_name="songs")
    op.drop_index(op.f("ix_songs_title"), table_name="songs")
    op.drop_table("songs")
    op.drop_index(op.f("ix_categories_slug"), table_name="categories")
    op.drop_index(op.f("ix_categories_name"), table_name="categories")
    op.drop_table("categories")
    op.drop_index(op.f("ix_albums_release_year"), table_name="albums")
    op.drop_index(op.f("ix_albums_title"), table_name="albums")
    op.drop_table("albums")
    op.drop_index(op.f("ix_artists_name"), table_name="artists")
    op.drop_table("artists")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
