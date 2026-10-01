from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_user(client: TestClient) -> None:
    payload = {
        "name": "Rafi",
        "email": "rafi@example.com",
        "password": "StrongPassword123!",
    }

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "rafi@example.com"


def test_login_user(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"name": "Rafi", "email": "login@example.com", "password": "StrongPassword123!"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "StrongPassword123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "access_token" in body["data"]


def test_invalid_login(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register",
        json={"name": "Rafi", "email": "badlogin@example.com", "password": "StrongPassword123!"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "badlogin@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401


def test_duplicate_email(client: TestClient) -> None:
    payload = {"name": "Asha", "email": "dup@example.com", "password": "StrongPassword123!"}
    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_protected_route_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_admin_only_route(client: TestClient) -> None:
    register = client.post(
        "/api/v1/auth/register",
        json={"name": "User", "email": "user@example.com", "password": "StrongPassword123!"},
    )
    token = register.json()["data"]["access_token"]

    response = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
