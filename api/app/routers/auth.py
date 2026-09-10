from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.config import settings
from app.database import get_db
from app.repositories.dashboard import DashboardRepository
from app.services.auth import AuthService

router = APIRouter(prefix="/api", tags=["account"])
COOKIE = "weekly_quiz_session"


class LoginInput(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=1024)


def repository(session=Depends(get_db)):
    return DashboardRepository(session)


def auth_service(repo=Depends(repository)):
    if len(settings.session_secret) < 32:
        raise HTTPException(503, "Login is not configured on the server")
    return AuthService(repo, settings.session_secret)


async def current_user(request: Request, service=Depends(auth_service)):
    token = request.cookies.get(COOKIE)
    user = await service.authenticate(token) if token else None
    if user is None:
        raise HTTPException(401, "Please sign in")
    return user


@router.post("/auth/login")
async def login(body: LoginInput, response: Response, service=Depends(auth_service)):
    user = await service.login(body.email, body.password)
    if user is None:
        raise HTTPException(401, "Email or password is incorrect")
    response.set_cookie(COOKIE, service.token(user), max_age=8 * 60 * 60,
                        httponly=True, secure=settings.cookie_secure, samesite="strict", path="/api")
    response.headers["Cache-Control"] = "no-store"
    return user


@router.get("/auth/me")
async def me(response: Response, user=Depends(current_user)):
    response.headers["Cache-Control"] = "no-store"
    return user


@router.get("/dashboard")
async def dashboard(response: Response, user=Depends(current_user), repo=Depends(repository)):
    response.headers["Cache-Control"] = "no-store"
    return {"user": user, "courses": await repo.courses_for(user),
            "quizzes": await repo.quizzes_for(user)}
