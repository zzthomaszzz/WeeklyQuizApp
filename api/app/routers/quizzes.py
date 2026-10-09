from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.quizzes import QuizUpdate


router = APIRouter(prefix="/api", tags=["quizzes"])


@router.get("/courses/{course_id}/quizzes")
async def get_course_quizzes(
    course_id: int,
    db: AsyncSession = Depends(get_db),
):
    course_result = await db.execute(
        text(
            """
            SELECT id
            FROM courses
            WHERE id = :course_id
            """
        ),
        {"course_id": course_id},
    )

    if course_result.first() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    quiz_result = await db.execute(
        text(
            """
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
            ORDER BY week_number ASC
            """
        ),
        {"course_id": course_id},
    )

    return [dict(row) for row in quiz_result.mappings().all()]


@router.patch("/quizzes/{quiz_id}")
async def update_quiz(
    quiz_id: int,
    quiz_update: QuizUpdate,
    db: AsyncSession = Depends(get_db),
):
    quiz_result = await db.execute(
        text(
            """
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
            WHERE id = :quiz_id
            """
        ),
        {"quiz_id": quiz_id},
    )

    existing_quiz = quiz_result.mappings().first()

    if existing_quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    update_data = quiz_update.model_dump(exclude_unset=True)

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
            detail="Quiz closing time must be after opening time",
        )

    allowed_fields = {
        "week_number",
        "title",
        "material_url",
        "status",
        "opens_at",
        "closes_at",
    }

    set_clauses = []

    for field in update_data:
        if field in allowed_fields:
            set_clauses.append(f"{field} = :{field}")

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
    db: AsyncSession = Depends(get_db),
):
    quiz_result = await db.execute(
        text(
            """
            SELECT id
            FROM quizzes
            WHERE id = :quiz_id
            """
        ),
        {"quiz_id": quiz_id},
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

    return [dict(row) for row in question_result.mappings().all()]