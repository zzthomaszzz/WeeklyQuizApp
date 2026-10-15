import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.auth import current_user
from app.routers.authoring import authoring_repository
from app.services.authoring import (
    AuthoringService,
    CourseNotAvailable,
    QuizNotAvailable,
)

LECTURER = {"id": 9, "email": "lecturer@example.test", "name": "Lecturer", "role": "lecturer"}
OTHER_LECTURER = {"id": 10, "email": "other@example.test", "name": "Other", "role": "lecturer"}
STUDENT = {"id": 1, "email": "student@example.test", "name": "Student", "role": "student"}

VALID_QUIZ = {"week_number": 3, "title": "Week 3 — Test Design"}

VALID_QUESTION = {
    "text": "Which of these is a black-box technique?",
    "topic_tag": "Testing",
    "options": [
        {"text": "Boundary value analysis", "is_correct": True},
        {"text": "Statement coverage", "is_correct": False},
    ],
}


class FakeRepository:
    """Course 7 belongs to lecturer 9. Quiz 20 is in course 7."""

    def __init__(self):
        self.created_quizzes = []
        self.created_questions = []
        self.next_position = 1

    async def course_owned_by(self, course_id, lecturer_id):
        if course_id == 7 and lecturer_id == 9:
            return {"id": 7, "code": "ENSE707"}
        return None

    async def quiz_owned_by(self, quiz_id, lecturer_id):
        if quiz_id == 20 and lecturer_id == 9:
            return {"id": 20, "course_id": 7}
        return None

    async def create_quiz(self, course_id, **fields):
        quiz = {"id": 50, "course_id": course_id, "status": "draft", **fields}
        self.created_quizzes.append(quiz)
        return quiz

    async def next_question_position(self, quiz_id):
        return self.next_position

    async def create_question(self, quiz_id, question_text, topic_tag, position, options):
        question = {
            "id": 60,
            "quiz_id": quiz_id,
            "text": question_text,
            "topic_tag": topic_tag,
            "position": position,
            "options": [
                {
                    "id": 100 + index,
                    "text": option["text"],
                    "is_correct": option["is_correct"],
                    "position": index + 1,
                }
                for index, option in enumerate(options)
            ],
        }
        self.created_questions.append(question)
        return question


def build_client(repo, user=LECTURER):
    app.dependency_overrides[authoring_repository] = lambda: repo
    app.dependency_overrides[current_user] = lambda: user
    return TestClient(app)


@pytest.fixture
def repo():
    repository = FakeRepository()
    yield repository
    app.dependency_overrides.clear()


# --------------------------------------------------------------- creating a quiz


def test_lecturer_creates_a_quiz_in_their_own_course(repo):
    client = build_client(repo)

    response = client.post("/api/courses/7/quizzes", json=VALID_QUIZ)

    assert response.status_code == 201

    body = response.json()
    assert body["course_id"] == 7
    assert body["week_number"] == 3
    assert body["title"] == "Week 3 — Test Design"


def test_a_new_quiz_starts_as_a_draft(repo):
    client = build_client(repo)

    response = client.post("/api/courses/7/quizzes", json=VALID_QUIZ)

    assert response.json()["status"] == "draft"


def test_a_quiz_can_set_an_attempt_limit(repo):
    client = build_client(repo)

    response = client.post(
        "/api/courses/7/quizzes", json={**VALID_QUIZ, "max_attempts": 2}
    )

    assert response.status_code == 201
    assert response.json()["max_attempts"] == 2


def test_a_student_cannot_create_a_quiz(repo):
    client = build_client(repo, user=STUDENT)

    response = client.post("/api/courses/7/quizzes", json=VALID_QUIZ)

    assert response.status_code == 403
    assert repo.created_quizzes == []


def test_a_lecturer_cannot_create_a_quiz_in_another_course(repo):
    client = build_client(repo, user=OTHER_LECTURER)

    response = client.post("/api/courses/7/quizzes", json=VALID_QUIZ)

    # 404 rather than 403: the response must not confirm the course exists.
    assert response.status_code == 404
    assert repo.created_quizzes == []


def test_a_quiz_needs_a_positive_week_number(repo):
    client = build_client(repo)

    response = client.post(
        "/api/courses/7/quizzes", json={**VALID_QUIZ, "week_number": 0}
    )

    assert response.status_code == 422


def test_a_quiz_cannot_close_before_it_opens(repo):
    client = build_client(repo)

    response = client.post(
        "/api/courses/7/quizzes",
        json={
            **VALID_QUIZ,
            "opens_at": "2026-03-10T09:00:00Z",
            "closes_at": "2026-03-09T09:00:00Z",
        },
    )

    assert response.status_code == 422


# ------------------------------------------------------------ adding a question


def test_lecturer_adds_a_question_with_its_options(repo):
    client = build_client(repo)

    response = client.post("/api/quizzes/20/questions", json=VALID_QUESTION)

    assert response.status_code == 201

    body = response.json()
    assert body["text"] == VALID_QUESTION["text"]
    assert [option["text"] for option in body["options"]] == [
        "Boundary value analysis",
        "Statement coverage",
    ]


def test_question_positions_are_assigned_by_the_server(repo):
    repo.next_position = 4
    client = build_client(repo)

    response = client.post("/api/quizzes/20/questions", json=VALID_QUESTION)

    assert response.json()["position"] == 4


def test_option_positions_follow_the_order_they_were_given(repo):
    client = build_client(repo)

    response = client.post("/api/quizzes/20/questions", json=VALID_QUESTION)

    assert [option["position"] for option in response.json()["options"]] == [1, 2]


def test_a_question_needs_exactly_one_correct_option(repo):
    client = build_client(repo)

    two_correct = {
        **VALID_QUESTION,
        "options": [
            {"text": "First", "is_correct": True},
            {"text": "Second", "is_correct": True},
        ],
    }

    response = client.post("/api/quizzes/20/questions", json=two_correct)

    assert response.status_code == 422
    assert repo.created_questions == []


def test_a_question_cannot_have_no_correct_option(repo):
    client = build_client(repo)

    none_correct = {
        **VALID_QUESTION,
        "options": [
            {"text": "First", "is_correct": False},
            {"text": "Second", "is_correct": False},
        ],
    }

    response = client.post("/api/quizzes/20/questions", json=none_correct)

    assert response.status_code == 422
    assert repo.created_questions == []


def test_a_question_needs_at_least_two_options(repo):
    client = build_client(repo)

    one_option = {
        **VALID_QUESTION,
        "options": [{"text": "Only choice", "is_correct": True}],
    }

    response = client.post("/api/quizzes/20/questions", json=one_option)

    assert response.status_code == 422
    assert repo.created_questions == []


def test_a_student_cannot_add_a_question(repo):
    client = build_client(repo, user=STUDENT)

    response = client.post("/api/quizzes/20/questions", json=VALID_QUESTION)

    assert response.status_code == 403
    assert repo.created_questions == []


def test_a_lecturer_cannot_add_a_question_to_another_quiz(repo):
    client = build_client(repo, user=OTHER_LECTURER)

    response = client.post("/api/quizzes/20/questions", json=VALID_QUESTION)

    assert response.status_code == 404
    assert repo.created_questions == []


# ------------------------------------------------------------------- the service


@pytest.mark.asyncio
async def test_service_refuses_a_course_the_lecturer_does_not_own():
    service = AuthoringService(FakeRepository())

    with pytest.raises(CourseNotAvailable):
        await service.create_quiz(course_id=7, lecturer_id=99, fields=VALID_QUIZ)


@pytest.mark.asyncio
async def test_service_refuses_a_quiz_the_lecturer_does_not_own():
    service = AuthoringService(FakeRepository())

    with pytest.raises(QuizNotAvailable):
        await service.add_question(
            quiz_id=20,
            lecturer_id=99,
            text="Anything",
            topic_tag=None,
            options=VALID_QUESTION["options"],
        )
