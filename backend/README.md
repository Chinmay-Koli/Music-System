# Retro Mehfil API

This project provides the backend API for the Retro Mehfil retro Hindi music discovery platform.

## Stage 1

The project skeleton, environment configuration, Docker setup, and health endpoint are in place.

## Completed stages

- Stage 1: project skeleton, configuration, and health endpoints
- Stage 2: models, Alembic, and seed data
- Stage 3: auth and protected-route logic with tests
- Stage 4: catalog APIs and admin safeguards
- Stage 5: playlists, favorites, and listening history
- Stage 6: external provider link support
- Stage 7: WebSocket room support for live music chat
- Stage 8: final docs and verification

## Runtime and verification

Run the backend locally with:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Run the verification suite with:

```bash
cd backend
.venv\Scripts\python.exe -m pytest -q
```

## API highlights

- Auth: register, login, token refresh, admin checks
- Catalog: song listing and admin creation
- Library: playlists, favorites, history, provider links
- Realtime: WebSocket room chat at `/ws/rooms/{room_name}`

## Current status

The backend is production-ready for the current milestone: validated auth, catalog, library, external providers, and WebSocket room behavior with passing automated tests.
