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
    response = client.post(
        "/api/auth/register",
        json=test_user,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == test_user["email"]
    assert data["name"] == test_user["name"]
    assert data["role"] == test_user["role"]
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email(test_user):
    first_response = client.post(
        "/api/auth/register",
        json=test_user,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/auth/register",
        json=test_user,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email is already registered"


def test_login_successfully(test_user):
    register_response = client.post(
        "/api/auth/register",
        json=test_user,
    )

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

    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == test_user["email"]
    assert data["user"]["role"] == test_user["role"]


def test_login_with_wrong_password(test_user):
    register_response = client.post(
        "/api/auth/register",
        json=test_user,
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": test_user["email"],
            "password": "WrongPassword123!",
        },
    )

    assert login_response.status_code == 401
    assert login_response.json()["detail"] == "Invalid email or password"