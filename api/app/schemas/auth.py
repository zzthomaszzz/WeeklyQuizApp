from typing import Literal

from pydantic import BaseModel, Field, field_validator


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