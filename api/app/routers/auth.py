from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)


router = APIRouter(prefix="/api", tags=["auth"])

password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    existing_user = await db.execute(
        text(
            """
            SELECT id
            FROM users
            WHERE email = :email
            """
        ),
        {
            "email": request.email,
        },
    )

    if existing_user.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    password_hash = password_context.hash(
        request.password
    )

    try:
        result = await db.execute(
            text(
                """
                INSERT INTO users (
                    email,
                    name,
                    password_hash,
                    role
                )
                VALUES (
                    :email,
                    :name,
                    :password_hash,
                    CAST(:role AS user_role)
                )
                RETURNING
                    id,
                    email,
                    name,
                    role
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
    "/auth/login",
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
            SELECT
                id,
                email,
                name,
                password_hash,
                role
            FROM users
            WHERE email = :email
            """
        ),
        {
            "email": email,
        },
    )

    user = result.mappings().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    password_is_valid = password_context.verify(
        request.password,
        user["password_hash"],
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(hours=1)
    )

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
