from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse

from app.config import settings
from app.routers import attempts, auth, authoring, health, quizzes

app = FastAPI(title="Weekly Quiz API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(quizzes.router)
app.include_router(attempts.router)
app.include_router(authoring.router)


@app.exception_handler(SQLAlchemyError)
async def database_error(request, error):
    # Never surface driver internals to the client.
    return JSONResponse(
        status_code=503,
        content={"detail": "Database is temporarily unavailable"},
    )
