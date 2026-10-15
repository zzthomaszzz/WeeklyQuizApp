"""Integration tests for who may read quizzes and questions.

The PATCH endpoint was given an ownership check early on. The two GET
endpoints were not, and were readable with no session at all — including
draft quizzes. These tests pin the access rules down.
"""

import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from app.main import app


async def build_course(lecturer_id: int, student_id: int):
    """One course with a published quiz and a draft quiz, and the student
    enrolled in it."""
    async with engine.begin() as connection:
        course_id = (
            await connection.execute(
                text(
                    """
                    INSERT INTO courses (code, name, lecturer_id, enrol_code)
                    VALUES ('ACC101', 'Access Test Course', :lecturer_id,
                            :enrol_code)
                    RETURNING id
                    """
                ),
                {"lecturer_id": lecturer_id, "enrol_code": f"ACC-{uuid4()}"},
            )
        ).scalar_one()

        published_id = (
            await connection.execute(
                text(
                    """
                    INSERT INTO quizzes (course_id, week_number, title, status,
                                         opens_at, closes_at)
                    VALUES (:course_id, 1, 'Published quiz', 'published',
                            CURRENT_TIMESTAMP - INTERVAL '1 day', NULL)
                    RETURNING id
                    """
                ),
                {"course_id": course_id},
            )
        ).scalar_one()

        draft_id = (
            await connection.execute(
                text(
                    """
                    INSERT INTO quizzes (course_id, week_number, title, status)
                    VALUES (:course_id, 2, 'Draft quiz', 'draft')
                    RETURNING id
                    """
                ),
                {"course_id": course_id},
            )
        ).scalar_one()

        question_id = (
            await connection.execute(
                text(
                    """
                    INSERT INTO questions (quiz_id, text, topic_tag, position)
                    VALUES (:quiz_id, 'Which is a black-box technique?',
                            'Testing', 1)
                    RETURNING id
                    """
                ),
                {"quiz_id": published_id},
            )
        ).scalar_one()

        await connection.execute(
            text(
                """
                INSERT INTO options (question_id, text, is_correct, position)
                VALUES (:question_id, 'Boundary value analysis', TRUE, 1),
                       (:question_id, 'Statement coverage', FALSE, 2)
                """
            ),
            {"question_id": question_id},
        )

        await connection.execute(
            text(
                """
                INSERT INTO enrolments (student_id, course_id)
                VALUES (:student_id, :course_id)
                ON CONFLICT (student_id, course_id) DO NOTHING
                """
            ),
            {"student_id": student_id, "course_id": course_id},
        )

    return course_id, published_id, draft_id


async def tear_down(course_id: int, emails: list[str]):
    async with engine.begin() as connection:
        await connection.execute(
            text("DELETE FROM courses WHERE id = :course_id"),
            {"course_id": course_id},
        )
        await connection.execute(
            text("DELETE FROM users WHERE email = ANY(:emails)"),
            {"emails": emails},
        )


async def user_id_for(email: str) -> int:
    async with engine.begin() as connection:
        return (
            await connection.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email},
            )
        ).scalar_one()


def register(client: TestClient, email: str, role: str):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "name": f"Access {role}",
            "password": "TestPass123!",
            "role": role,
        },
    )
    assert response.status_code == 201


@pytest.fixture
def access():
    lecturer_email = f"access-lecturer-{uuid4()}@example.com"
    student_email = f"access-student-{uuid4()}@example.com"
    outsider_email = f"access-outsider-{uuid4()}@example.com"

    lecturer = TestClient(app)
    student = TestClient(app)
    outsider = TestClient(app)
    anonymous = TestClient(app)

    register(lecturer, lecturer_email, "lecturer")
    register(student, student_email, "student")
    register(outsider, outsider_email, "student")

    lecturer_id = asyncio.run(user_id_for(lecturer_email))
    student_id = asyncio.run(user_id_for(student_email))

    course_id, published_id, draft_id = asyncio.run(
        build_course(lecturer_id, student_id)
    )

    try:
        yield {
            "lecturer": lecturer,
            "student": student,
            "outsider": outsider,
            "anonymous": anonymous,
            "course_id": course_id,
            "published_id": published_id,
            "draft_id": draft_id,
        }
    finally:
        asyncio.run(
            tear_down(
                course_id,
                [lecturer_email, student_email, outsider_email],
            )
        )
        for client in (lecturer, student, outsider, anonymous):
            client.close()


def test_reading_questions_requires_a_session(access):
    response = access["anonymous"].get(
        f"/api/quizzes/{access['published_id']}/questions"
    )

    assert response.status_code == 401


def test_listing_course_quizzes_requires_a_session(access):
    response = access["anonymous"].get(
        f"/api/courses/{access['course_id']}/quizzes"
    )

    assert response.status_code == 401


def test_student_not_enrolled_cannot_read_questions(access):
    response = access["outsider"].get(
        f"/api/quizzes/{access['published_id']}/questions"
    )

    # 404 rather than 403: the response must not confirm the quiz exists.
    assert response.status_code == 404


def test_student_cannot_read_a_draft_quiz(access):
    response = access["student"].get(
        f"/api/quizzes/{access['draft_id']}/questions"
    )

    assert response.status_code == 404


def test_enrolled_student_reads_published_questions_with_options(access):
    response = access["student"].get(
        f"/api/quizzes/{access['published_id']}/questions"
    )

    assert response.status_code == 200

    questions = response.json()
    assert len(questions) == 1

    options = questions[0]["options"]
    assert len(options) == 2
    assert [option["text"] for option in options] == [
        "Boundary value analysis",
        "Statement coverage",
    ]


def test_student_never_receives_correctness_before_submitting(access):
    response = access["student"].get(
        f"/api/quizzes/{access['published_id']}/questions"
    )

    assert response.status_code == 200
    assert "is_correct" not in response.text

    for question in response.json():
        for option in question["options"]:
            assert "is_correct" not in option


def test_owning_lecturer_can_read_a_draft_quiz(access):
    response = access["lecturer"].get(
        f"/api/quizzes/{access['draft_id']}/questions"
    )

    assert response.status_code == 200


def test_student_only_sees_published_quizzes_in_the_course_list(access):
    response = access["student"].get(
        f"/api/courses/{access['course_id']}/quizzes"
    )

    assert response.status_code == 200

    titles = [quiz["title"] for quiz in response.json()]
    assert "Published quiz" in titles
    assert "Draft quiz" not in titles


def test_owning_lecturer_sees_drafts_in_the_course_list(access):
    response = access["lecturer"].get(
        f"/api/courses/{access['course_id']}/quizzes"
    )

    assert response.status_code == 200

    titles = [quiz["title"] for quiz in response.json()]
    assert "Draft quiz" in titles
