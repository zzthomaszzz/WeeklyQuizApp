from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class QuizUpdate(BaseModel):
    week_number: int | None = Field(
        default=None,
        gt=0,
    )
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    material_url: str | None = None
    max_attempts: int | None = Field(
        default=None,
        gt=0,
    )
    status: Literal[
        "draft",
        "published",
        "closed",
    ] | None = None
    opens_at: datetime | None = None
    closes_at: datetime | None = None

    @field_validator(
        "week_number",
        "title",
        "status",
        mode="before",
    )
    @classmethod
    def required_fields_cannot_be_null(
        cls,
        value,
        info,
    ):
        if value is None:
            raise ValueError(
                f"{info.field_name} cannot be null"
            )

        return value

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        title = value.strip()

        if not title:
            raise ValueError("Title cannot be blank")

        return title