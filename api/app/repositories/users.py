from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.errors import EmailAlreadyRegistered


class UserRepository:
    """All SQL that touches the users table. No business rules live here."""

    def __init__(self, session):
        self.session = session

    async def user_by_email(self, email):
        result = await self.session.execute(
            text(
                """
                SELECT id, email, name, password_hash, role
                FROM users
                WHERE email = :email
                """
            ),
            {"email": email},
        )
        return result.mappings().first()

    async def user_by_id(self, user_id):
        result = await self.session.execute(
            text(
                """
                SELECT id, email, name, role
                FROM users
                WHERE id = :user_id
                """
            ),
            {"user_id": user_id},
        )
        return result.mappings().first()

    async def create_user(self, email, name, password_hash, role):
        """Insert a user. The unique index on users.email is the real guard
        against duplicates, so a violation here is translated rather than
        allowed to surface as a database error."""
        try:
            result = await self.session.execute(
                text(
                    """
                    INSERT INTO users (email, name, password_hash, role)
                    VALUES (
                        :email, :name, :password_hash, CAST(:role AS user_role)
                    )
                    RETURNING id, email, name, role
                    """
                ),
                {
                    "email": email,
                    "name": name,
                    "password_hash": password_hash,
                    "role": role,
                },
            )
            user = result.mappings().one()
            await self.session.commit()
            return user
        except IntegrityError:
            await self.session.rollback()
            raise EmailAlreadyRegistered()

    async def rollback(self):
        await self.session.rollback()
