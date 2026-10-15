from sqlalchemy import text


class AuthoringRepository:
    """SQL for creating quiz content. No business rules live here."""

    def __init__(self, session):
        self.session = session

    async def course_owned_by(self, course_id, lecturer_id):
        result = await self.session.execute(
            text(
                """
                SELECT id, code
                FROM courses
                WHERE id = :course_id AND lecturer_id = :lecturer_id
                """
            ),
            {"course_id": course_id, "lecturer_id": lecturer_id},
        )
        return result.mappings().first()

    async def quiz_owned_by(self, quiz_id, lecturer_id):
        result = await self.session.execute(
            text(
                """
                SELECT q.id, q.course_id
                FROM quizzes q
                JOIN courses c ON c.id = q.course_id
                WHERE q.id = :quiz_id AND c.lecturer_id = :lecturer_id
                """
            ),
            {"quiz_id": quiz_id, "lecturer_id": lecturer_id},
        )
        return result.mappings().first()

    async def create_quiz(
        self,
        course_id,
        week_number,
        title,
        material_url=None,
        opens_at=None,
        closes_at=None,
        max_attempts=None,
    ):
        result = await self.session.execute(
            text(
                """
                INSERT INTO quizzes (
                    course_id, week_number, title, material_url,
                    status, opens_at, closes_at, max_attempts
                )
                VALUES (
                    :course_id, :week_number, :title, :material_url,
                    'draft', :opens_at, :closes_at, :max_attempts
                )
                RETURNING id, course_id, week_number, title, status, max_attempts
                """
            ),
            {
                "course_id": course_id,
                "week_number": week_number,
                "title": title,
                "material_url": material_url,
                "opens_at": opens_at,
                "closes_at": closes_at,
                "max_attempts": max_attempts,
            },
        )
        quiz = dict(result.mappings().one())
        await self.session.commit()
        return quiz

    async def next_question_position(self, quiz_id):
        """Positions are unique per quiz, so the server assigns them rather
        than trusting a client to pick one that is free."""
        result = await self.session.execute(
            text(
                """
                SELECT COALESCE(MAX(position), 0) + 1
                FROM questions
                WHERE quiz_id = :quiz_id
                """
            ),
            {"quiz_id": quiz_id},
        )
        return result.scalar_one()

    async def create_question(self, quiz_id, question_text, topic_tag, position, options):
        question_result = await self.session.execute(
            text(
                """
                INSERT INTO questions (quiz_id, text, topic_tag, position)
                VALUES (:quiz_id, :text, :topic_tag, :position)
                RETURNING id, quiz_id, text, topic_tag, position
                """
            ),
            {
                "quiz_id": quiz_id,
                "text": question_text,
                "topic_tag": topic_tag,
                "position": position,
            },
        )
        question = dict(question_result.mappings().one())

        created_options = []
        for index, option in enumerate(options, start=1):
            option_result = await self.session.execute(
                text(
                    """
                    INSERT INTO options (question_id, text, is_correct, position)
                    VALUES (:question_id, :text, :is_correct, :position)
                    RETURNING id, text, is_correct, position
                    """
                ),
                {
                    "question_id": question["id"],
                    "text": option["text"],
                    "is_correct": option["is_correct"],
                    "position": index,
                },
            )
            created_options.append(dict(option_result.mappings().one()))

        await self.session.commit()

        question["options"] = created_options
        return question

    async def rollback(self):
        await self.session.rollback()
