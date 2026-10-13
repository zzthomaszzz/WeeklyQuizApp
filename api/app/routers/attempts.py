from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.repositories.attempts import AttemptRepository
from app.routers.auth import current_user
from app.schemas.attempts import AttemptResult, AttemptSubmission
from app.services.attempts import (
    AttemptService,
    InvalidSubmission,
    QuizNotAvailable,
)


router = APIRouter(prefix="/api", tags=["attempts"])


def attempt_repository(session=Depends(get_db)):
    return AttemptRepository(session)


def attempt_service(repo=Depends(attempt_repository)):
    return AttemptService(repo)


@router.post(
    "/quizzes/{quiz_id}/attempts",
    response_model=AttemptResult,
    status_code=status.HTTP_201_CREATED,
)
async def submit_attempt(
    quiz_id: int,
    body: AttemptSubmission,
    user=Depends(current_user),
    service=Depends(attempt_service),
):
    if user["role"] != "student":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only students can submit quiz attempts",
        )

    try:
        return await service.submit(
            quiz_id=quiz_id,
            student_id=user["id"],
            answers=[answer.model_dump() for answer in body.answers],
        )
    except QuizNotAvailable:
        # Deliberately 404, not 403: a student should not be able to discover
        # that a quiz they cannot reach exists.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quiz not found")
    except InvalidSubmission as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error))
