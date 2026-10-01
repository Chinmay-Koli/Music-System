from collections import defaultdict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import admin_router, auth_router, catalog_router, library_router
from app.core.config import settings

ROOM_CONNECTIONS: dict[str, dict[str, WebSocket]] = defaultdict(dict)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Retro Mehfil retro Hindi music discovery backend",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.environment == "development" else ["localhost", "127.0.0.1"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


async def broadcast_room_status(room_name: str) -> None:
    room_users = ROOM_CONNECTIONS.get(room_name, {})
    payload = {
        "type": "system",
        "event": "room_status",
        "room": room_name,
        "users": sorted(room_users.keys()),
    }
    for websocket in room_users.values():
        await websocket.send_json(payload)


@app.websocket("/ws/rooms/{room_name}")
async def room_socket(websocket: WebSocket, room_name: str) -> None:
    user = websocket.query_params.get("user", "guest")
    await websocket.accept()

    room_users = ROOM_CONNECTIONS.setdefault(room_name, {})
    room_users[user] = websocket

    await websocket.send_json(
        {
            "type": "system",
            "event": "joined",
            "room": room_name,
            "user": user,
            "users": sorted(room_users.keys()),
        }
    )

    for other_user, other_socket in room_users.items():
        if other_user == user:
            continue
        await other_socket.send_json(
            {
                "type": "system",
                "event": "user_joined",
                "room": room_name,
                "user": user,
                "users": sorted(room_users.keys()),
            }
        )

    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")

            if message_type == "chat":
                payload = {
                    "type": "chat",
                    "room": room_name,
                    "user": user,
                    "message": data.get("message", ""),
                }
                for member_user, member_socket in room_users.items():
                    if member_user == user:
                        continue
                    await member_socket.send_json(payload)
                await broadcast_room_status(room_name)
    except WebSocketDisconnect:
        room_users = ROOM_CONNECTIONS.get(room_name, {})
        room_users.pop(user, None)
        if not room_users:
            ROOM_CONNECTIONS.pop(room_name, None)
        else:
            for other_user, other_socket in room_users.items():
                await other_socket.send_json(
                    {
                        "type": "system",
                        "event": "user_left",
                        "room": room_name,
                        "user": user,
                        "users": sorted(room_users.keys()),
                    }
                )
            await broadcast_room_status(room_name)


app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(catalog_router)
app.include_router(library_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Retro Mehfil API is running"}
