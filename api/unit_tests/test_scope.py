import sqlite3

import pytest
from app.repositories.dashboard import DashboardRepository


class Result:
    def __init__(self, rows):
        self.rows = [dict(row) for row in rows]
    def mappings(self):
        return self.rows


class SQLiteSession:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE courses (id INTEGER, code TEXT, name TEXT, lecturer_id INTEGER);
            CREATE TABLE enrolments (student_id INTEGER, course_id INTEGER);
            CREATE TABLE quizzes (id INTEGER, course_id INTEGER, week_number INTEGER,
                title TEXT, status TEXT, opens_at TEXT, closes_at TEXT);
            INSERT INTO courses VALUES (1, 'A', 'First', 10), (2, 'B', 'Second', 20);
            INSERT INTO enrolments VALUES (1, 1), (2, 2);
            INSERT INTO quizzes VALUES
                (1, 1, 1, 'Open', 'published', NULL, NULL),
                (2, 1, 2, 'Draft', 'draft', NULL, NULL),
                (3, 1, 3, 'Future', 'published', '2999-01-01', NULL),
                (4, 1, 4, 'Expired', 'published', NULL, '2000-01-01'),
                (5, 2, 1, 'Other course', 'published', NULL, NULL),
                (6, 1, 5, 'Closed', 'closed', NULL, NULL);
        """)

    async def execute(self, sql, params):
        return Result(self.db.execute(str(sql), params).fetchall())


@pytest.mark.asyncio
async def test_student_only_receives_enrolled_open_published_quizzes():
    repo = DashboardRepository(SQLiteSession())
    user = {"id": 1, "role": "student"}
    assert [c["id"] for c in await repo.courses_for(user)] == [1]
    assert [q["id"] for q in await repo.quizzes_for(user)] == [1]
    assert await repo.quizzes_for({"id": 99, "role": "student"}) == []


@pytest.mark.asyncio
async def test_lecturer_receives_own_courses_and_all_own_quizzes():
    repo = DashboardRepository(SQLiteSession())
    user = {"id": 10, "role": "lecturer"}
    assert [c["id"] for c in await repo.courses_for(user)] == [1]
    assert [q["id"] for q in await repo.quizzes_for(user)] == [1, 2, 3, 4, 6]
