"""Integration tests for quiz authoring.

These run against the real database, so they also confirm that the schema
constraints the service relies on actually hold — in particular the partial
unique index that allows only one correct option per question.
"""

import asyncio
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from app.main import app


async def user_id_for(email: str) -> int:
    async with engine.begin() as connection:
        return (
            await connection.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email},
            )
        ).scalar_one()


async def make_course(lecturer_id: int) -> int:
    async with engine.begin() as connection:
        return (
            await connection.execute(
                text(
                    """
                    INSERT INTO courses (code, name, lecturer_id, enrol_code)
                    VALUES ('AUTH01', 'Authoring Test Course', :lecturer_id,
                            :enrol_code)
                    RETURNING id
                    """
                ),
                {"lecturer_id": lecturer_id, "enrol_code": f"AUTH-{uuid4()}"},
            )
        ).scalar_one()


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


@pytest.fixture
def authoring():
    lecturer_email = f"authoring-{uuid4()}@example.com"
    student_email = f"authoring-student-{uuid4()}@example.com"

    lecturer = TestClient(app)
    student = TestClient(app)

    for client, email, role in (
        (lecturer, lecturer_email, "lecturer"),
        (student, student_email, "student"),
    ):
        response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "name": f"Authoring {role}",
                "password": "TestPass123!",
                "role": role,
            },
        )
        assert response.status_code == 201

    lecturer_id = asyncio.run(user_id_for(lecturer_email))
    student_id = asyncio.run(user_id_for(student_email))
    course_id = asyncio.run(make_course(lecturer_id))

    try:
        yield {
            "lecturer": lecturer,
            "student": student,
            "student_id": student_id,
            "course_id": course_id,
        }
    finally:
        asyncio.run(tear_down(course_id, [lecturer_email, student_email]))
        lecturer.close()
        student.close()


def create_quiz(client, course_id, **overrides):
    return client.post(
        f"/api/courses/{course_id}/quizzes",
        json={"week_number": 1, "title": "Week 1 — Basics", **overrides},
    )


QUESTION = {
    "text": "Which of these is a black-box technique?",
    "topic_tag": "Testing",
    "options": [
        {"text": "Boundary value analysis", "is_correct": True},
        {"text": "Statement coverage", "is_correct": False},
    ],
}


def test_lecturer_creates_a_quiz_and_it_is_stored_as_a_draft(authoring):
    response = create_quiz(authoring["lecturer"], authoring["course_id"])

    assert response.status_code == 201

    quiz_id = response.json()["id"]

    async def read_status():
        async with engine.begin() as connection:
            return (
                await connection.execute(
                    text("SELECT status FROM quizzes WHERE id = :id"),
                    {"id": quiz_id},
                )
            ).scalar_one()

    assert asyncio.run(read_status()) == "draft"


def test_question_and_options_are_written_to_the_database(authoring):
    quiz_id = create_quiz(authoring["lecturer"], authoring["course_id"]).json()["id"]

    response = authoring["lecturer"].post(
        f"/api/quizzes/{quiz_id}/questions", json=QUESTION
    )

    assert response.status_code == 201

    question_id = response.json()["id"]

    async def read_options():
        async with engine.begin() as connection:
            rows = (
                await connection.execute(
                    text(
                        """
                        SELECT text, is_correct, position
                        FROM options
                        WHERE question_id = :id
                        ORDER BY position
                        """
                    ),
                    {"id": question_id},
                )
            ).mappings().all()
            return [dict(row) for row in rows]

    options = asyncio.run(read_options())

    assert [option["position"] for option in options] == [1, 2]
    assert [option["is_correct"] for option in options] == [True, False]


def test_questions_added_in_sequence_get_increasing_positions(authoring):
    quiz_id = create_quiz(authoring["lecturer"], authoring["course_id"]).json()["id"]

    first = authoring["lecturer"].post(
        f"/api/quizzes/{quiz_id}/questions", json=QUESTION
    )
    second = authoring["lecturer"].post(
        f"/api/quizzes/{quiz_id}/questions",
        json={**QUESTION, "text": "A second question"},
    )

    assert first.json()["position"] == 1
    assert second.json()["position"] == 2


def test_a_student_cannot_author_anything(authoring):
    response = create_quiz(authoring["student"], authoring["course_id"])

    assert response.status_code == 403


def test_the_new_quiz_is_invisible_to_students_until_published(authoring):
    quiz_id = create_quiz(authoring["lecturer"], authoring["course_id"]).json()["id"]

    authoring["lecturer"].post(f"/api/quizzes/{quiz_id}/questions", json=QUESTION)

    # The student is not enrolled, and the quiz is a draft: either alone is
    # enough to hide it.
    response = authoring["student"].get(f"/api/quizzes/{quiz_id}/questions")

    assert response.status_code == 404


def test_a_second_correct_option_is_refused_by_the_database(authoring):
    """The service rejects this at the schema layer, but the partial unique
    index is the real guard. This proves it is in place."""
    quiz_id = create_quiz(authoring["lecturer"], authoring["course_id"]).json()["id"]
    question_id = authoring["lecturer"].post(
        f"/api/quizzes/{quiz_id}/questions", json=QUESTION
    ).json()["id"]

    async def add_second_correct():
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    INSERT INTO options (question_id, text, is_correct, position)
                    VALUES (:question_id, 'Another correct one', TRUE, 3)
                    """
                ),
                {"question_id": question_id},
            )

    with pytest.raises(Exception) as raised:
        asyncio.run(add_second_correct())

    assert "uq_one_correct_option" in str(raised.value)


# ------------------------------------------------------------------ publishing


def publish(client, quiz_id):
    return client.patch(f"/api/quizzes/{quiz_id}", json={"status": "published"})


def test_publishing_an_empty_quiz_is_refused(authoring):
    quiz_id = create_quiz(authoring["lecturer"], authoring["course_id"]).json()["id"]

    response = publish(authoring["lecturer"], quiz_id)

    assert response.status_code == 422
    assert "question" in response.json()["detail"].lower()


def test_a_quiz_with_questions_can_be_published(authoring):
    quiz_id = create_quiz(authoring["lecturer"], authoring["course_id"]).json()["id"]
    authoring["lecturer"].post(f"/api/quizzes/{quiz_id}/questions", json=QUESTION)

    response = publish(authoring["lecturer"], quiz_id)

    assert response.status_code == 200
    assert response.json()["status"] == "published"


def test_a_published_quiz_becomes_visible_to_an_enrolled_student(authoring):
    quiz_id = create_quiz(authoring["lecturer"], authoring["course_id"]).json()["id"]
    authoring["lecturer"].post(f"/api/quizzes/{quiz_id}/questions", json=QUESTION)

    async def enrol():
        # Enrol this fixture's own student by id. Selecting the newest
        # student in the table instead would pick up another test run's
        # user whenever two suites share the database.
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    """
                    INSERT INTO enrolments (student_id, course_id)
                    VALUES (:student_id, :course_id)
                    ON CONFLICT (student_id, course_id) DO NOTHING
                    """
                ),
                {
                    "student_id": authoring["student_id"],
                    "course_id": authoring["course_id"],
                },
            )

    before = authoring["student"].get(f"/api/quizzes/{quiz_id}/questions")
    assert before.status_code == 404

    publish(authoring["lecturer"], quiz_id)
    asyncio.run(enrol())

    after = authoring["student"].get(f"/api/quizzes/{quiz_id}/questions")
    assert after.status_code == 200


def test_the_attempt_limit_can_be_changed_after_creation(authoring):
    quiz_id = create_quiz(authoring["lecturer"], authoring["course_id"]).json()["id"]

    response = authoring["lecturer"].patch(
        f"/api/quizzes/{quiz_id}", json={"max_attempts": 3}
    )

    assert response.status_code == 200

    async def read_limit():
        async with engine.begin() as connection:
            return (
                await connection.execute(
                    text("SELECT max_attempts FROM quizzes WHERE id = :id"),
                    {"id": quiz_id},
                )
            ).scalar_one()

    assert asyncio.run(read_limit()) == 3

