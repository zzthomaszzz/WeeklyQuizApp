from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256
from starlette.concurrency import run_in_threadpool


TOKEN_ISSUER = "weekly-quiz"
SESSION_HOURS = 8

# bcrypt silently truncates anything past 72 bytes, so reject it instead.
MAX_PASSWORD_BYTES = 72

ALLOWED_ROLES = ("student", "lecturer")


class EmailAlreadyRegistered(Exception):
    """Raised when a registration reuses an existing email address."""


def verify_password(password, password_hash):
    try:
        if password_hash.startswith(("$2a$", "$2b$", "$2y$")):
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        if password_hash.startswith("$pbkdf2-sha256$"):
            return pbkdf2_sha256.verify(password, password_hash)
    except (ValueError, TypeError):
        pass
    return False


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def public_user(user):
    return {key: user[key] for key in ("id", "email", "name", "role")}


class AuthService:
    """Business rules for registering and signing in. Takes a repository so
    unit tests can supply a fake and run with no database."""

    def __init__(self, repository, secret):
        self.repository = repository
        self.secret = secret

    async def register(self, email, name, password, role):
        if await self.repository.user_by_email(email) is not None:
            raise EmailAlreadyRegistered()

        password_hash = await run_in_threadpool(hash_password, password)

        try:
            user = await self.repository.create_user(
                email=email,
                name=name,
                password_hash=password_hash,
                role=role,
            )
        except Exception:
            # A concurrent signup can win the race between the check above
            # and the insert; the unique index is the real guard.
            await self.repository.rollback()
            raise EmailAlreadyRegistered()

        return public_user(user)

    async def login(self, email, password):
        user = await self.repository.user_by_email(email.strip().lower())
        if user is None:
            return None

        password_matches = await run_in_threadpool(
            verify_password, password, user["password_hash"]
        )
        if not password_matches:
            return None

        if user["role"] not in ALLOWED_ROLES:
            return None

        return public_user(user)

    def token(self, user):
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                "sub": str(user["id"]),
                "iat": now,
                "exp": now + timedelta(hours=SESSION_HOURS),
                "iss": TOKEN_ISSUER,
            },
            self.secret,
            algorithm="HS256",
        )

    async def authenticate(self, token):
        try:
            claims = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                issuer=TOKEN_ISSUER,
                options={"require_exp": True, "require_sub": True},
            )
            user_id = int(claims["sub"])
        except (JWTError, ValueError, TypeError, KeyError):
            return None

        user = await self.repository.user_by_id(user_id)
        if user is None or user["role"] not in ALLOWED_ROLES:
            return None

        return public_user(user)
