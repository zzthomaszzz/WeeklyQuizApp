from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.routers.auth import COOKIE, dashboard_repository, user_repository
from app.services.auth import AuthService, EmailAlreadyRegistered

SECRET = "unit-test-secret-that-is-at-least-32-characters"
HASH = bcrypt.hashpw(b"test-password", bcrypt.gensalt(rounds=4)).decode()


class FakeRepository:
    def __init__(self):
        self.user = {
            "id": 1,
            "email": "student@example.test",
            "name": "Student",
            "role": "student",
            "password_hash": HASH,
        }
        self.created = []

    async def user_by_email(self, email):
        return self.user if self.user and email == self.user["email"] else None

    async def user_by_id(self, user_id):
        return self.user if self.user and user_id == self.user["id"] else None

    async def create_user(self, email, name, password_hash, role):
        created = {
            "id": 2,
            "email": email,
            "name": name,
            "role": role,
            "password_hash": password_hash,
        }
        self.created.append(created)
        return created

    async def rollback(self):
        pass

    async def courses_for(self, user):
        return [{"id": 11, "code": "TEST", "name": "Test course"}]

    async def quizzes_for(self, user):
        return []


@pytest.fixture
def client():
    repo = FakeRepository()
    app.dependency_overrides[user_repository] = lambda: repo
    app.dependency_overrides[dashboard_repository] = lambda: repo
    with TestClient(app) as test_client:
        yield test_client, repo
    app.dependency_overrides.clear()


def test_login_sets_httponly_cookie_and_opens_dashboard(client):
    test_client, repo = client

    assert test_client.get("/api/dashboard").status_code == 401

    response = test_client.post(
        "/api/auth/login",
        json={"email": repo.user["email"], "password": "test-password"},
    )

    assert response.status_code == 200
    assert "password_hash" not in response.json()
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]

    # Query parameters must never widen what the session is allowed to see.
    response = test_client.get("/api/dashboard?student_id=999&role=lecturer")
    assert response.status_code == 200
    assert response.json()["user"]["id"] == 1
    assert response.json()["user"]["role"] == "student"
    assert "password_hash" not in response.text


def test_login_does_not_return_a_token_in_the_body(client):
    test_client, repo = client

    response = test_client.post(
        "/api/auth/login",
        json={"email": repo.user["email"], "password": "test-password"},
    )

    body = response.json()
    assert "access_token" not in body
    assert "token" not in body


def test_wrong_password_does_not_authenticate(client):
    test_client, repo = client

    response = test_client.post(
        "/api/auth/login",
        json={"email": repo.user["email"], "password": "wrong"},
    )

    assert response.status_code == 401
    assert COOKIE not in test_client.cookies
    assert test_client.get("/api/dashboard").status_code == 401


def test_register_creates_a_user_and_signs_them_in(client):
    test_client, repo = client

    response = test_client.post(
        "/api/auth/register",
        json={
            "email": "New.Person@Example.test",
            "name": "New Person",
            "password": "long-enough-password",
            "role": "lecturer",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["email"] == "new.person@example.test"
    assert body["role"] == "lecturer"
    assert "password" not in body
    assert "password_hash" not in body
    assert "HttpOnly" in response.headers["set-cookie"]

    # The stored hash must never be the plain password.
    assert repo.created[0]["password_hash"] != "long-enough-password"


def test_register_rejects_an_existing_email(client):
    test_client, repo = client

    response = test_client.post(
        "/api/auth/register",
        json={
            "email": repo.user["email"],
            "name": "Duplicate",
            "password": "long-enough-password",
            "role": "student",
        },
    )

    assert response.status_code == 409


def test_register_rejects_a_short_password(client):
    test_client, _ = client

    response = test_client.post(
        "/api/auth/register",
        json={
            "email": "short@example.test",
            "name": "Short",
            "password": "tiny",
            "role": "student",
        },
    )

    assert response.status_code == 422


def test_register_rejects_an_unknown_role(client):
    test_client, _ = client

    response = test_client.post(
        "/api/auth/register",
        json={
            "email": "admin@example.test",
            "name": "Admin",
            "password": "long-enough-password",
            "role": "admin",
        },
    )

    assert response.status_code == 422


def test_logout_clears_the_session(client):
    test_client, repo = client

    test_client.post(
        "/api/auth/login",
        json={"email": repo.user["email"], "password": "test-password"},
    )
    assert test_client.get("/api/dashboard").status_code == 200

    assert test_client.post("/api/auth/logout").status_code == 204
    assert test_client.get("/api/dashboard").status_code == 401


@pytest.mark.asyncio
async def test_invalid_expired_and_deleted_user_sessions():
    repo = FakeRepository()
    service = AuthService(repo, SECRET)

    assert await service.authenticate("tampered") is None

    expired = jwt.encode(
        {
            "sub": "1",
            "iss": "weekly-quiz",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=10),
        },
        SECRET,
        algorithm="HS256",
    )
    assert await service.authenticate(expired) is None

    token = service.token(repo.user)
    repo.user["role"] = "lecturer"
    assert (await service.authenticate(token))["role"] == "lecturer"

    repo.user = None
    assert await service.authenticate(token) is None


@pytest.mark.asyncio
async def test_register_raises_when_email_is_taken():
    repo = FakeRepository()
    service = AuthService(repo, SECRET)

    with pytest.raises(EmailAlreadyRegistered):
        await service.register(
            email=repo.user["email"],
            name="Duplicate",
            password="long-enough-password",
            role="student",
        )


def test_existing_health_endpoint_and_cors_methods(client):
    test_client, _ = client

    response = test_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    response = test_client.options(
        "/api/dashboard",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

    response = test_client.options(
        "/api/dashboard",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in response.headers
