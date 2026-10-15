from sqlalchemy import text


class AttemptRepository:
    """All SQL for submitting and storing quiz attempts."""

    def __init__(self, session):
        self.session = session

    async def quiz_open_for_student(self, quiz_id, student_id):
        """The quiz, but only if this student is enrolled in its course and
        the quiz is published and inside its open window. Returns None
        otherwise, so the caller cannot tell 'not yours' from 'not there'."""
        result = await self.session.execute(
            text(
                """
                SELECT q.id, q.title, q.max_attempts
                FROM quizzes q
                JOIN courses c ON c.id = q.course_id
                JOIN enrolments e
                    ON e.course_id = c.id
                   AND e.student_id = :student_id
                WHERE q.id = :quiz_id
                  AND q.status = 'published'
                  AND (q.opens_at IS NULL OR q.opens_at <= CURRENT_TIMESTAMP)
                  AND (q.closes_at IS NULL OR q.closes_at > CURRENT_TIMESTAMP)
                """
            ),
            {"quiz_id": quiz_id, "student_id": student_id},
        )
        return result.mappings().first()

    async def grading_key(self, quiz_id):
        """Every option in the quiz with the flag that decides scoring. This
        never leaves the server: the student response is built from it."""
        result = await self.session.execute(
            text(
                """
                SELECT
                    qu.id AS question_id,
                    o.id AS option_id,
                    o.is_correct
                FROM questions qu
                JOIN options o ON o.question_id = qu.id
                WHERE qu.quiz_id = :quiz_id
                ORDER BY qu.position, o.position
                """
            ),
            {"quiz_id": quiz_id},
        )
        return [dict(row) for row in result.mappings()]

    async def save_attempt(self, quiz_id, student_id, score, max_score, graded):
        attempt_result = await self.session.execute(
            text(
                """
                INSERT INTO attempts (
                    quiz_id, student_id, submitted_at, score, max_score
                )
                VALUES (
                    :quiz_id, :student_id, CURRENT_TIMESTAMP, :score, :max_score
                )
                RETURNING id
                """
            ),
            {
                "quiz_id": quiz_id,
                "student_id": student_id,
                "score": score,
                "max_score": max_score,
            },
        )
        attempt_id = attempt_result.scalar_one()

        await self.session.execute(
            text(
                """
                INSERT INTO answers (
                    attempt_id, question_id, selected_option_id, is_correct
                )
                VALUES (
                    :attempt_id, :question_id, :selected_option_id, :is_correct
                )
                """
            ),
            [
                {
                    "attempt_id": attempt_id,
                    "question_id": answer["question_id"],
                    "selected_option_id": answer["selected_option_id"],
                    "is_correct": answer["is_correct"],
                }
                for answer in graded
            ],
        )

        await self.session.commit()
        return attempt_id

    async def attempts_taken(self, quiz_id, student_id):
        """Submitted attempts so far. Not enforced yet — quizzes.max_attempts
        does not exist in the schema. See CLAUDE.md."""
        result = await self.session.execute(
            text(
                """
                SELECT COUNT(*) FROM attempts
                WHERE quiz_id = :quiz_id
                  AND student_id = :student_id
                  AND submitted_at IS NOT NULL
                """
            ),
            {"quiz_id": quiz_id, "student_id": student_id},
        )
        return result.scalar_one()

    async def rollback(self):
        await self.session.rollback()
