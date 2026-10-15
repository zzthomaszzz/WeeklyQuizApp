"""Integration tests for quiz API endpoints."""

import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from app.main import app


async def get_user_id(email: str) -> int:
    async with engine.begin() as connection:
        result = await connection.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE email = :email
                """
            ),
            {"email": email},
        )
        return result.scalar_one()


async def create_quiz_data(lecturer_id: int):
    course_code = f"QA{uuid4().hex[:6].upper()}"
    enrol_code = uuid4().hex[:8].upper()

    async with engine.begin() as connection:
        course_result = await connection.execute(
            text(
                """
                INSERT INTO courses (
                    code,
                    name,
                    lecturer_id,
                    enrol_code
                )
                VALUES (
                    :code,
                    :name,
                    :lecturer_id,
                    :enrol_code
                )
                RETURNING id
                """
            ),
            {
                "code": course_code,
                "name": "Quiz API Test Course",
                "lecturer_id": lecturer_id,
                "enrol_code": enrol_code,
            },
        )

        course_id = course_result.scalar_one()

        quiz_result = await connection.execute(
            text(
                """
                INSERT INTO quizzes (
                    course_id,
                    week_number,
                    title,
                    status
                )
                VALUES (
                    :course_id,
                    :week_number,
                    :title,
                    :status
                )
                RETURNING id
                """
            ),
            {
                "course_id": course_id,
                "week_number": 1,
                "title": "Quiz API Test Quiz",
                "status": "draft",
            },
        )

        quiz_id = quiz_result.scalar_one()

        question_result = await connection.execute(
            text(
                """
                INSERT INTO questions (
                    quiz_id,
                    text,
                    topic_tag,
                    position
                )
                VALUES (
                    :quiz_id,
                    :text,
                    :topic_tag,
                    :position
                )
                RETURNING id
                """
            ),
            {
                "quiz_id": quiz_id,
                "text": "What is software quality?",
                "topic_tag": "testing",
                "position": 1,
            },
        )

        question_id = question_result.scalar_one()

        await connection.execute(
            text(
                """
                INSERT INTO options (
                    question_id,
                    text,
                    is_correct,
                    position
                )
                VALUES (
                    :question_id,
                    :text,
                    :is_correct,
                    :position
                )
                """
            ),
            {
                "question_id": question_id,
                "text": "Meeting defined quality requirements",
                "is_correct": True,
                "position": 1,
            },
        )

    return course_id, quiz_id, question_id


async def delete_quiz_data(
    course_id: int,
    quiz_id: int,
    question_id: int,
    owner_email: str,
    other_email: str,
):
    async with engine.begin() as connection:
        await connection.execute(
            text(
                """
                DELETE FROM options
                WHERE question_id = :question_id
                """
            ),
            {"question_id": question_id},
        )

        await connection.execute(
            text(
                """
                DELETE FROM questions
                WHERE quiz_id = :quiz_id
                """
            ),
            {"quiz_id": quiz_id},
        )

        await connection.execute(
            text(
                """
                DELETE FROM quizzes
                WHERE id = :quiz_id
                """
            ),
            {"quiz_id": quiz_id},
        )

        await connection.execute(
            text(
                """
                DELETE FROM courses
                WHERE id = :course_id
                """
            ),
            {"course_id": course_id},
        )

        await connection.execute(
            text(
                """
                DELETE FROM users
                WHERE email = :owner_email
                   OR email = :other_email
                """
            ),
            {
                "owner_email": owner_email,
                "other_email": other_email,
            },
        )


@pytest.fixture
def quiz_setup():
    owner_email = f"quiz-owner-{uuid4()}@example.com"
    other_email = f"quiz-other-{uuid4()}@example.com"

    owner_client = TestClient(app)
    other_client = TestClient(app)

    owner_user = {
        "email": owner_email,
        "name": "Quiz Owner Lecturer",
        "password": "TestPass123!",
        "role": "lecturer",
    }

    other_user = {
        "email": other_email,
        "name": "Other Lecturer",
        "password": "TestPass123!",
        "role": "lecturer",
    }

    owner_response = owner_client.post(
        "/api/auth/register",
        json=owner_user,
    )

    assert owner_response.status_code == 201

    other_response = other_client.post(
        "/api/auth/register",
        json=other_user,
    )

    assert other_response.status_code == 201

    owner_id = asyncio.run(get_user_id(owner_email))

    course_id, quiz_id, question_id = asyncio.run(
        create_quiz_data(owner_id)
    )

    try:
        yield {
            "owner_client": owner_client,
            "other_client": other_client,
            "course_id": course_id,
            "quiz_id": quiz_id,
            "question_id": question_id,
        }
    finally:
        asyncio.run(
            delete_quiz_data(
                course_id,
                quiz_id,
                question_id,
                owner_email,
                other_email,
            )
        )

        owner_client.close()
        other_client.close()


def test_non_owner_lecturer_cannot_update_quiz(quiz_setup):
    response = quiz_setup["other_client"].patch(
        f"/api/quizzes/{quiz_setup['quiz_id']}",
        json={
            "title": "Unauthorised Quiz Change",
        },
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You are not authorized to update this quiz"
    )


def test_questions_response_does_not_expose_is_correct(quiz_setup):
    response = quiz_setup["owner_client"].get(
        f"/api/quizzes/{quiz_setup['quiz_id']}/questions"
    )

    assert response.status_code == 200

    questions = response.json()

    assert len(questions) == 1
    assert questions[0]["text"] == "What is software quality?"
    assert "is_correct" not in questions[0]


def test_get_quizzes_for_missing_course_returns_404():
    client = TestClient(app)

    response = client.get(
        "/api/courses/2147483647/quizzes"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Course not found"

    client.close()