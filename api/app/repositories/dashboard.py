from sqlalchemy import text


class DashboardRepository:
    def __init__(self, session):
        self.session = session

    async def user_by_email(self, email):
        result = await self.session.execute(text(
            "SELECT id, email, name, password_hash, role FROM users WHERE email = :email"
        ), {"email": email})
        return result.mappings().first()

    async def user_by_id(self, user_id):
        result = await self.session.execute(text(
            "SELECT id, email, name, role FROM users WHERE id = :user_id"
        ), {"user_id": user_id})
        return result.mappings().first()

    async def courses_for(self, user):
        scope = ("c.lecturer_id = :user_id" if user["role"] == "lecturer" else
                 "EXISTS (SELECT 1 FROM enrolments e WHERE e.course_id = c.id AND e.student_id = :user_id)")
        result = await self.session.execute(text(
            f"SELECT c.id, c.code, c.name FROM courses c WHERE {scope} ORDER BY c.code, c.id"
        ), {"user_id": user["id"]})
        return [dict(row) for row in result.mappings()]

    async def quizzes_for(self, user):
        # Scope comes from the authenticated server-side role, never client input.
        scope = ("c.lecturer_id = :user_id" if user["role"] == "lecturer" else """
            EXISTS (SELECT 1 FROM enrolments e WHERE e.course_id = c.id AND e.student_id = :user_id)
            AND q.status = 'published'
            AND (q.opens_at IS NULL OR q.opens_at <= CURRENT_TIMESTAMP)
            AND (q.closes_at IS NULL OR q.closes_at > CURRENT_TIMESTAMP)
        """)
        result = await self.session.execute(text(f"""
            SELECT q.id, q.course_id, q.week_number, q.title, q.opens_at, q.closes_at
            FROM quizzes q JOIN courses c ON c.id = q.course_id
            WHERE {scope} ORDER BY q.week_number, q.id
        """), {"user_id": user["id"]})
        return [dict(row) for row in result.mappings()]
