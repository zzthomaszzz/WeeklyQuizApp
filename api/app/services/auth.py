from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256
from starlette.concurrency import run_in_threadpool


def verify_password(password, password_hash):
    try:
        if password_hash.startswith(("$2a$", "$2b$", "$2y$")):
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        if password_hash.startswith("$pbkdf2-sha256$"):
            return pbkdf2_sha256.verify(password, password_hash)
    except (ValueError, TypeError):
        pass
    return False


def public_user(user):
    return {key: user[key] for key in ("id", "email", "name", "role")}


class AuthService:
    def __init__(self, repository, secret):
        self.repository = repository
        self.secret = secret

    async def login(self, email, password):
        user = await self.repository.user_by_email(email.strip())
        if not user or not await run_in_threadpool(verify_password, password, user["password_hash"]):
            return None
        if user["role"] not in ("student", "lecturer"):
            return None
        return public_user(user)

    def token(self, user):
        now = datetime.now(timezone.utc)
        return jwt.encode({"sub": str(user["id"]), "iat": now,
                           "exp": now + timedelta(hours=8), "iss": "weekly-quiz"},
                          self.secret, algorithm="HS256")

    async def authenticate(self, token):
        try:
            claims = jwt.decode(token, self.secret, algorithms=["HS256"],
                                issuer="weekly-quiz", options={"require_exp": True, "require_sub": True})
            user_id = int(claims["sub"])
        except (JWTError, ValueError, TypeError, KeyError):
            return None
        user = await self.repository.user_by_id(user_id)
        if not user or user["role"] not in ("student", "lecturer"):
            return None
        return public_user(user)
