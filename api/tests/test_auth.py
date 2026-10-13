"""Integration tests: these hit the real test database."""

import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from app.main import app

client = TestClient(app)


async def delete_test_user(email: str):
    async with engine.begin() as connection:
        await connection.execute(
            text("DELETE FROM users WHERE email = :email"),
            {"email": email},
        )


@pytest.fixture
def test_user():
    email = f"auth-test-{uuid4()}@example.com"

    user = {
        "email": email,
        "name": "Auth Test User",
        "password": "TestPass123!",
        "role": "student",
    }

    yield user

    asyncio.run(delete_test_user(email))


def test_register_user_successfully(test_user):
    response = client.post("/api/auth/register", json=test_user)

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == test_user["email"]
    assert data["name"] == test_user["name"]
    assert data["role"] == test_user["role"]
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(test_user):
    first_response = client.post("/api/auth/register", json=test_user)

    assert first_response.status_code == 201

    second_response = client.post("/api/auth/register", json=test_user)

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email is already registered"


def test_login_successfully(test_user):
    register_response = client.post("/api/auth/register", json=test_user)

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert data["email"] == test_user["email"]
    assert data["role"] == test_user["role"]
    assert "password_hash" not in data

    # The session is a cookie, never a token handed to JavaScript.
    assert "access_token" not in data
    assert "HttpOnly" in login_response.headers["set-cookie"]


def test_login_with_wrong_password(test_user):
    register_response = client.post("/api/auth/register", json=test_user)

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": "WrongPassword123!",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Email or password is incorrect"


def test_stored_password_is_hashed(test_user):
    register_response = client.post("/api/auth/register", json=test_user)

    assert register_response.status_code == 201

    async def read_hash():
        async with engine.begin() as connection:
            result = await connection.execute(
                text("SELECT password_hash FROM users WHERE email = :email"),
                {"email": test_user["email"]},
            )
            return result.scalar_one()

    password_hash = asyncio.run(read_hash())

    assert password_hash != test_user["password"]
    assert password_hash.startswith("$2")


def test_me_requires_a_session(test_user):
    anonymous = TestClient(app)

    assert anonymous.get("/api/auth/me").status_code == 401


def test_me_returns_the_signed_in_user(test_user):
    session = TestClient(app)

    register_response = session.post("/api/auth/register", json=test_user)
    assert register_response.status_code == 201

    me_response = session.get("/api/auth/me")

    assert me_response.status_code == 200
    assert me_response.json()["email"] == test_user["email"]
