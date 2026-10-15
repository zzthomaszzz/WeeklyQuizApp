from pydantic import BaseModel, Field


class AnswerSubmission(BaseModel):
    question_id: int
    selected_option_id: int


class AttemptSubmission(BaseModel):
    answers: list[AnswerSubmission] = Field(min_length=1)


class GradedAnswer(BaseModel):
    """Correctness is allowed here: the student has submitted. Before
    submission it must not appear at all — see CLAUDE.md."""

    question_id: int
    selected_option_id: int
    is_correct: bool


class AttemptResult(BaseModel):
    attempt_id: int
    score: int
    max_score: int
    answers: list[GradedAnswer]
