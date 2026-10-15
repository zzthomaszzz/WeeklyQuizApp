from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.repositories.authoring import AuthoringRepository
from app.routers.auth import current_user
from app.schemas.authoring import (
    QuestionCreate,
    QuestionCreated,
    QuizCreate,
    QuizCreated,
)
from app.services.authoring import (
    AuthoringService,
    CourseNotAvailable,
    QuizNotAvailable,
)

router = APIRouter(prefix="/api", tags=["authoring"])


def authoring_repository(session=Depends(get_db)):
    return AuthoringRepository(session)


def authoring_service(repo=Depends(authoring_repository)):
    return AuthoringService(repo)


def require_lecturer(user):
    if user["role"] != "lecturer":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only lecturers can create quiz content",
        )


@router.post(
    "/courses/{course_id}/quizzes",
    response_model=QuizCreated,
    status_code=status.HTTP_201_CREATED,
)
async def create_quiz(
    course_id: int,
    body: QuizCreate,
    user: Annotated[dict, Depends(current_user)],
    service=Depends(authoring_service),
):
    require_lecturer(user)

    try:
        return await service.create_quiz(
            course_id=course_id,
            lecturer_id=user["id"],
            fields=body.model_dump(),
        )
    except CourseNotAvailable:
        # 404, not 403: a lecturer should not learn that another lecturer's
        # course exists.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Course not found")


@router.post(
    "/quizzes/{quiz_id}/questions",
    response_model=QuestionCreated,
    status_code=status.HTTP_201_CREATED,
)
async def add_question(
    quiz_id: int,
    body: QuestionCreate,
    user: Annotated[dict, Depends(current_user)],
    service=Depends(authoring_service),
):
    require_lecturer(user)

    try:
        return await service.add_question(
            quiz_id=quiz_id,
            lecturer_id=user["id"],
            text=body.text,
            topic_tag=body.topic_tag,
            options=[option.model_dump() for option in body.options],
        )
    except QuizNotAvailable:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quiz not found")
