from __future__ import annotations

from fastapi.testclient import TestClient


def test_join_room_and_broadcast_messages(client: TestClient) -> None:
    with client.websocket_connect("/ws/rooms/retro-lounge?user=alice") as alice:
        first_message = alice.receive_json()
        assert first_message["type"] == "system"
        assert first_message["event"] == "joined"

        with client.websocket_connect("/ws/rooms/retro-lounge?user=bob") as bob:
            joined = bob.receive_json()
            assert joined["type"] == "system"
            assert joined["event"] == "joined"

            alice_message = alice.receive_json()
            assert alice_message["type"] == "system"
            assert alice_message["event"] == "user_joined"
            assert alice_message["user"] == "bob"

            bob.send_json({"type": "chat", "message": "hello retro crowd"})
            chat_message = alice.receive_json()
            assert chat_message["type"] == "chat"
            assert chat_message["message"] == "hello retro crowd"
            assert chat_message["user"] == "bob"

            status = bob.receive_json()
            assert status["type"] == "system"
            assert status["event"] == "room_status"
            assert "alice" in status["users"]
            assert "bob" in status["users"]
