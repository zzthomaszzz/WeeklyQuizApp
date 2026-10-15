from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class QuizCreate(BaseModel):
    week_number: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=200)
    material_url: str | None = None
    opens_at: datetime | None = None
    closes_at: datetime | None = None
    max_attempts: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def closes_after_it_opens(self):
        if self.opens_at and self.closes_at and self.closes_at <= self.opens_at:
            raise ValueError("closes_at must be after opens_at")
        return self


class QuizCreated(BaseModel):
    id: int
    course_id: int
    week_number: int
    title: str
    status: str
    max_attempts: int | None


class OptionCreate(BaseModel):
    text: str = Field(min_length=1)
    is_correct: bool = False


class QuestionCreate(BaseModel):
    text: str = Field(min_length=1)
    topic_tag: str | None = Field(default=None, max_length=100)
    # Two is the fewest that makes a choice; six is a practical ceiling for a
    # single-choice question.
    options: list[OptionCreate] = Field(min_length=2, max_length=6)

    @model_validator(mode="after")
    def exactly_one_correct_option(self):
        correct = sum(1 for option in self.options if option.is_correct)
        if correct != 1:
            raise ValueError(
                "A question must have exactly one correct option"
            )
        return self


class OptionCreated(BaseModel):
    """What the lecturer gets back. Correctness is included here because the
    lecturer authored it; the student-facing schema omits it entirely."""

    id: int
    text: str
    is_correct: bool
    position: int


class QuestionCreated(BaseModel):
    id: int
    quiz_id: int
    text: str
    topic_tag: str | None
    position: int
    options: list[OptionCreated]
