from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class QuizUpdate(BaseModel):
    week_number: int | None = Field(default=None, gt=0)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    material_url: str | None = None
    status: Literal["draft", "published", "closed"] | None = None
    opens_at: datetime | None = None
    closes_at: datetime | None = None