import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.attempts import attempt_repository
from app.routers.auth import current_user
from app.services.attempts import (
    AttemptService,
    InvalidSubmission,
    QuizNotAvailable,
)

STUDENT = {"id": 1, "email": "student@example.test", "name": "Student", "role": "student"}
LECTURER = {"id": 9, "email": "lecturer@example.test", "name": "Lecturer", "role": "lecturer"}

# Quiz 5 has two questions. Question 40's correct option is 101,
# question 41's correct option is 103.
GRADING_KEY = [
    {"question_id": 40, "option_id": 101, "is_correct": True},
    {"question_id": 40, "option_id": 102, "is_correct": False},
    {"question_id": 41, "option_id": 103, "is_correct": True},
    {"question_id": 41, "option_id": 104, "is_correct": False},
]


class FakeRepository:
    def __init__(self, quiz_available=True):
        self.quiz_available = quiz_available
        self.saved = None

    async def quiz_open_for_student(self, quiz_id, student_id):
        if not self.quiz_available:
            return None
        return {"id": quiz_id, "title": "Week 3"}

    async def grading_key(self, quiz_id):
        return list(GRADING_KEY)

    async def save_attempt(self, quiz_id, student_id, score, max_score, graded):
        self.saved = {
            "quiz_id": quiz_id,
            "student_id": student_id,
            "score": score,
            "max_score": max_score,
            "graded": graded,
        }
        return 77


def build_client(repo, user=STUDENT):
    app.dependency_overrides[attempt_repository] = lambda: repo
    app.dependency_overrides[current_user] = lambda: user
    return TestClient(app)


@pytest.fixture
def repo():
    repository = FakeRepository()
    yield repository
    app.dependency_overrides.clear()


def submit(client, answers, quiz_id=5):
    return client.post(f"/api/quizzes/{quiz_id}/attempts", json={"answers": answers})


def test_scores_a_fully_correct_submission(repo):
    client = build_client(repo)

    response = submit(
        client,
        [
            {"question_id": 40, "selected_option_id": 101},
            {"question_id": 41, "selected_option_id": 103},
        ],
    )

    assert response.status_code == 201

    body = response.json()
    assert body["score"] == 2
    assert body["max_score"] == 2
    assert body["attempt_id"] == 77
    assert all(answer["is_correct"] for answer in body["answers"])


def test_scores_a_partially_correct_submission(repo):
    client = build_client(repo)

    response = submit(
        client,
        [
            {"question_id": 40, "selected_option_id": 101},
            {"question_id": 41, "selected_option_id": 104},
        ],
    )

    assert response.status_code == 201

    body = response.json()
    assert body["score"] == 1
    assert body["max_score"] == 2

    by_question = {answer["question_id"]: answer["is_correct"] for answer in body["answers"]}
    assert by_question == {40: True, 41: False}


def test_persists_the_attempt_with_the_graded_answers(repo):
    client = build_client(repo)

    submit(
        client,
        [
            {"question_id": 40, "selected_option_id": 102},
            {"question_id": 41, "selected_option_id": 103},
        ],
    )

    assert repo.saved["quiz_id"] == 5
    assert repo.saved["student_id"] == STUDENT["id"]
    assert repo.saved["score"] == 1
    assert repo.saved["max_score"] == 2
    assert len(repo.saved["graded"]) == 2


def test_rejects_a_lecturer(repo):
    client = build_client(repo, user=LECTURER)

    response = submit(client, [{"question_id": 40, "selected_option_id": 101}])

    assert response.status_code == 403
    assert repo.saved is None


def test_rejects_a_quiz_that_is_not_open_to_this_student():
    repository = FakeRepository(quiz_available=False)
    client = build_client(repository)

    response = submit(
        client,
        [
            {"question_id": 40, "selected_option_id": 101},
            {"question_id": 41, "selected_option_id": 103},
        ],
    )

    # 404 rather than 403: a student should not learn that a quiz they
    # cannot reach exists.
    assert response.status_code == 404
    assert repository.saved is None

    app.dependency_overrides.clear()


def test_rejects_a_submission_that_misses_a_question(repo):
    client = build_client(repo)

    response = submit(client, [{"question_id": 40, "selected_option_id": 101}])

    assert response.status_code == 400
    assert "every question" in response.json()["detail"].lower()
    assert repo.saved is None


def test_rejects_an_option_belonging_to_another_question(repo):
    client = build_client(repo)

    response = submit(
        client,
        [
            {"question_id": 40, "selected_option_id": 103},
            {"question_id": 41, "selected_option_id": 103},
        ],
    )

    assert response.status_code == 400
    assert repo.saved is None


def test_rejects_two_answers_for_the_same_question(repo):
    client = build_client(repo)

    response = submit(
        client,
        [
            {"question_id": 40, "selected_option_id": 101},
            {"question_id": 40, "selected_option_id": 102},
        ],
    )

    assert response.status_code == 400
    assert repo.saved is None


def test_rejects_an_unknown_question(repo):
    client = build_client(repo)

    response = submit(
        client,
        [
            {"question_id": 40, "selected_option_id": 101},
            {"question_id": 999, "selected_option_id": 103},
        ],
    )

    assert response.status_code == 400
    assert repo.saved is None


def test_rejects_an_empty_submission(repo):
    client = build_client(repo)

    response = submit(client, [])

    assert response.status_code == 422
    assert repo.saved is None


@pytest.mark.asyncio
async def test_service_raises_when_the_quiz_is_not_available():
    service = AttemptService(FakeRepository(quiz_available=False))

    with pytest.raises(QuizNotAvailable):
        await service.submit(
            quiz_id=5,
            student_id=1,
            answers=[{"question_id": 40, "selected_option_id": 101}],
        )


@pytest.mark.asyncio
async def test_service_raises_on_an_incomplete_submission():
    service = AttemptService(FakeRepository())

    with pytest.raises(InvalidSubmission):
        await service.submit(
            quiz_id=5,
            student_id=1,
            answers=[{"question_id": 40, "selected_option_id": 101}],
        )
