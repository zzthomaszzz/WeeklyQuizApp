from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db


router = APIRouter(prefix="/api/auth", tags=["auth"])

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterRequest(BaseModel):
    email: str
    name: str = Field(min_length=1, max_length=150)
    password: str = Field(min_length=8)
    role: Literal["student", "lecturer"]

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()

        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("Invalid email address")

        if len(email) > 255:
            raise ValueError("Email is too long")

        return email

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password is too long")

        return value


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    existing_user = await db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": request.email},
    )

    if existing_user.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    password_hash = password_context.hash(request.password)

    try:
        result = await db.execute(
            text(
                """
                INSERT INTO users (email, name, password_hash, role)
                VALUES (:email, :name, :password_hash, CAST(:role AS user_role))
                RETURNING id, email, name, role
                """
            ),
            {
                "email": request.email,
                "name": request.name,
                "password_hash": password_hash,
                "role": request.role,
            },
        )

        user = result.mappings().one()
        await db.commit()

    except IntegrityError as error:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from error

    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "role": str(user["role"]),
    }


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    email = request.email.strip().lower()

    result = await db.execute(
        text(
            """
            SELECT id, email, name, password_hash, role
            FROM users
            WHERE email = :email
            """
        ),
        {"email": email},
    )

    user = result.mappings().first()

    if not user or not password_context.verify(
        request.password,
        user["password_hash"],
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    access_token = jwt.encode(
        {
            "sub": str(user["id"]),
            "role": str(user["role"]),
            "exp": expires_at,
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "role": str(user["role"]),
        },
    }
