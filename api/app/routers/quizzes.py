from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.routers.auth import current_user
from app.schemas.quizzes import QuizUpdate

router = APIRouter(
    prefix="/api",
    tags=["quizzes"],
)


@router.get("/courses/{course_id}/quizzes")
async def get_course_quizzes(
    course_id: int,
    user: Annotated[dict, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Quizzes in a course, scoped to what the caller may see.

    A lecturer sees every quiz in a course they own. A student sees only
    published quizzes inside their open window, in a course they are
    enrolled in. Anyone else gets 404 rather than 403, so the response
    cannot be used to confirm the course exists.
    """
    if user["role"] == "lecturer":
        visible_course = """
            SELECT id FROM courses
            WHERE id = :course_id AND lecturer_id = :user_id
        """
        quiz_filter = ""
    else:
        visible_course = """
            SELECT c.id FROM courses c
            JOIN enrolments e ON e.course_id = c.id
                             AND e.student_id = :user_id
            WHERE c.id = :course_id
        """
        quiz_filter = """
            AND status = 'published'
            AND (opens_at IS NULL OR opens_at <= CURRENT_TIMESTAMP)
            AND (closes_at IS NULL OR closes_at > CURRENT_TIMESTAMP)
        """

    course_result = await db.execute(
        text(visible_course),
        {"course_id": course_id, "user_id": user["id"]},
    )

    if course_result.first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    quiz_result = await db.execute(
        text(
            f"""
            SELECT
                id,
                course_id,
                week_number,
                title,
                material_url,
                status,
                opens_at,
                closes_at
            FROM quizzes
            WHERE course_id = :course_id
            {quiz_filter}
            ORDER BY week_number ASC
            """
        ),
        {"course_id": course_id},
    )

    return [
        dict(row)
        for row in quiz_result.mappings().all()
    ]


@router.patch("/quizzes/{quiz_id}")
async def update_quiz(
    quiz_id: int,
    quiz_update: QuizUpdate,
    user: Annotated[dict, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if user["role"] != "lecturer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only lecturers can update quizzes",
        )

    quiz_result = await db.execute(
        text(
            """
            SELECT
                q.id,
                q.course_id,
                q.week_number,
                q.title,
                q.material_url,
                q.status,
                q.opens_at,
                q.closes_at,
                c.lecturer_id
            FROM quizzes AS q
            JOIN courses AS c
                ON c.id = q.course_id
            WHERE q.id = :quiz_id
            """
        ),
        {
            "quiz_id": quiz_id,
        },
    )

    existing_quiz = quiz_result.mappings().first()

    if existing_quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    if existing_quiz["lecturer_id"] != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this quiz",
        )

    update_data = quiz_update.model_dump(
        exclude_unset=True
    )

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No quiz fields provided to update",
        )

    final_opens_at = update_data.get(
        "opens_at",
        existing_quiz["opens_at"],
    )

    final_closes_at = update_data.get(
        "closes_at",
        existing_quiz["closes_at"],
    )

    if (
        final_opens_at is not None
        and final_closes_at is not None
        and final_closes_at <= final_opens_at
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Quiz closing time must be "
                "after opening time"
            ),
        )

    if update_data.get("status") == "published":
        question_count = await db.execute(
            text(
                """
                SELECT COUNT(*) FROM questions
                WHERE quiz_id = :quiz_id
                """
            ),
            {"quiz_id": quiz_id},
        )

        if question_count.scalar_one() == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "A quiz needs at least one question "
                    "before it can be published"
                ),
            )

    allowed_fields = {
        "week_number",
        "title",
        "material_url",
        "status",
        "opens_at",
        "closes_at",
        "max_attempts",
    }

    set_clauses = []

    for field in update_data:
        if field in allowed_fields:
            set_clauses.append(
                f"{field} = :{field}"
            )

    update_data["quiz_id"] = quiz_id

    result = await db.execute(
        text(
            f"""
            UPDATE quizzes
            SET {", ".join(set_clauses)}
            WHERE id = :quiz_id
            RETURNING
                id,
                course_id,
                week_number,
                title,
                material_url,
                status,
                opens_at,
                closes_at
            """
        ),
        update_data,
    )

    updated_quiz = result.mappings().first()

    await db.commit()

    return dict(updated_quiz)


@router.get("/quizzes/{quiz_id}/questions")
async def get_quiz_questions(
    quiz_id: int,
    user: Annotated[dict, Depends(current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Questions and their answer options for one quiz.

    Correctness is deliberately absent from the response: the selected
    column list below never includes options.is_correct, so it cannot be
    returned by accident. Grading happens server-side on submission.
    """
    if user["role"] == "lecturer":
        visible_quiz = """
            SELECT q.id FROM quizzes q
            JOIN courses c ON c.id = q.course_id
            WHERE q.id = :quiz_id AND c.lecturer_id = :user_id
        """
    else:
        visible_quiz = """
            SELECT q.id FROM quizzes q
            JOIN courses c ON c.id = q.course_id
            JOIN enrolments e ON e.course_id = c.id
                             AND e.student_id = :user_id
            WHERE q.id = :quiz_id
              AND q.status = 'published'
              AND (q.opens_at IS NULL OR q.opens_at <= CURRENT_TIMESTAMP)
              AND (q.closes_at IS NULL OR q.closes_at > CURRENT_TIMESTAMP)
        """

    quiz_result = await db.execute(
        text(visible_quiz),
        {"quiz_id": quiz_id, "user_id": user["id"]},
    )

    if quiz_result.first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    question_result = await db.execute(
        text(
            """
            SELECT
                id,
                quiz_id,
                text,
                topic_tag,
                position
            FROM questions
            WHERE quiz_id = :quiz_id
            ORDER BY position ASC
            """
        ),
        {"quiz_id": quiz_id},
    )

    questions = [dict(row) for row in question_result.mappings().all()]

    if not questions:
        return []

    option_result = await db.execute(
        text(
            """
            SELECT
                id,
                question_id,
                text,
                position
            FROM options
            WHERE question_id = ANY(:question_ids)
            ORDER BY question_id, position ASC
            """
        ),
        {"question_ids": [question["id"] for question in questions]},
    )

    options_by_question: dict[int, list[dict]] = {}
    for option in option_result.mappings().all():
        options_by_question.setdefault(
            option["question_id"], []
        ).append(dict(option))

    for question in questions:
        question["options"] = options_by_question.get(question["id"], [])

    return questions
