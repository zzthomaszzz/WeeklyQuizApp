from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.services.auth import MAX_PASSWORD_BYTES


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
        if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError("Password is too long")

        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=1024)


class UserResponse(BaseModel):
    """What the client is allowed to see. password_hash is absent by
    construction, not filtered out after the fact."""

    id: int
    email: str
    name: str
    role: str
