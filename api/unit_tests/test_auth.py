from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.routers.auth import repository, COOKIE
from app.services.auth import AuthService

SECRET = "unit-test-secret-that-is-at-least-32-characters"
HASH = bcrypt.hashpw(b"test-password", bcrypt.gensalt(rounds=4)).decode()


class FakeRepository:
    def __init__(self):
        self.user = {"id": 1, "email": "student@example.test", "name": "Student",
                     "role": "student", "password_hash": HASH}
    async def user_by_email(self, email):
        return self.user if email == self.user["email"] else None
    async def user_by_id(self, user_id):
        return self.user if self.user and user_id == self.user["id"] else None
    async def courses_for(self, user):
        return [{"id": 11, "code": "TEST", "name": "Test course"}]
    async def quizzes_for(self, user):
        return []


@pytest.fixture
def client():
    repo = FakeRepository()
    app.dependency_overrides[repository] = lambda: repo
    with TestClient(app) as client:
        yield client, repo
    app.dependency_overrides.clear()


def test_login_cookie_and_private_dashboard(client):
    client, repo = client
    assert client.get("/api/dashboard").status_code == 401
    response = client.post("/api/auth/login", json={"email": repo.user["email"], "password": "test-password"})
    assert response.status_code == 200
    assert "password_hash" not in response.json()
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]
    response = client.get("/api/dashboard?student_id=999&role=lecturer")
    assert response.status_code == 200
    assert response.json()["user"]["id"] == 1
    assert response.json()["user"]["role"] == "student"
    assert "password_hash" not in response.text


def test_wrong_password_does_not_authenticate(client):
    client, repo = client
    response = client.post("/api/auth/login", json={"email": repo.user["email"], "password": "wrong"})
    assert response.status_code == 401
    assert COOKIE not in client.cookies
    assert client.get("/api/dashboard").status_code == 401


@pytest.mark.asyncio
async def test_invalid_expired_and_deleted_user_sessions():
    repo = FakeRepository()
    service = AuthService(repo, SECRET)
    assert await service.authenticate("tampered") is None
    expired = jwt.encode({"sub": "1", "iss": "weekly-quiz",
                          "exp": datetime.now(timezone.utc) - timedelta(seconds=10)}, SECRET, algorithm="HS256")
    assert await service.authenticate(expired) is None
    token = service.token(repo.user)
    repo.user["role"] = "lecturer"
    assert (await service.authenticate(token))["role"] == "lecturer"
    repo.user = None
    assert await service.authenticate(token) is None


def test_existing_health_endpoint_and_cors_methods(client):
    client, _ = client
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    response = client.options("/api/dashboard", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "PATCH",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    response = client.options("/api/dashboard", headers={
        "Origin": "https://untrusted.example",
        "Access-Control-Request-Method": "GET",
    })
    assert "access-control-allow-origin" not in response.headers
