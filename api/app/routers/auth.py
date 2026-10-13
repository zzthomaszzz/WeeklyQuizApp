from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.config import MINIMUM_SECRET_LENGTH, settings
from app.database import get_db
from app.repositories.dashboard import DashboardRepository
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from app.services.auth import AuthService, EmailAlreadyRegistered

router = APIRouter(prefix="/api", tags=["auth"])

COOKIE = "weekly_quiz_session"
SESSION_MAX_AGE = 8 * 60 * 60


def user_repository(session=Depends(get_db)):
    return UserRepository(session)


def dashboard_repository(session=Depends(get_db)):
    return DashboardRepository(session)


def auth_service(repo=Depends(user_repository)):
    if len(settings.session_secret) < MINIMUM_SECRET_LENGTH:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Login is not configured on the server",
        )
    return AuthService(repo, settings.session_secret)


async def current_user(request: Request, service=Depends(auth_service)):
    token = request.cookies.get(COOKIE)
    user = await service.authenticate(token) if token else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please sign in")
    return user


def start_session(response: Response, service, user):
    response.set_cookie(
        COOKIE,
        service.token(user),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/api",
    )
    response.headers["Cache-Control"] = "no-store"


@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    response: Response,
    service=Depends(auth_service),
):
    try:
        user = await service.register(
            email=body.email,
            name=body.name,
            password=body.password,
            role=body.role,
        )
    except EmailAlreadyRegistered:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Email is already registered",
        )

    start_session(response, service, user)
    return user


@router.post("/auth/login", response_model=UserResponse)
async def login(
    body: LoginRequest,
    response: Response,
    service=Depends(auth_service),
):
    user = await service.login(body.email, body.password)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Email or password is incorrect",
        )

    start_session(response, service, user)
    return user


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(COOKIE, path="/api")
    response.headers["Cache-Control"] = "no-store"


@router.get("/auth/me", response_model=UserResponse)
async def me(response: Response, user=Depends(current_user)):
    response.headers["Cache-Control"] = "no-store"
    return user


@router.get("/dashboard")
async def dashboard(
    response: Response,
    user=Depends(current_user),
    repo=Depends(dashboard_repository),
):
    response.headers["Cache-Control"] = "no-store"
    return {
        "user": user,
        "courses": await repo.courses_for(user),
        "quizzes": await repo.quizzes_for(user),
    }
