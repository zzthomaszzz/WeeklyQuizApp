from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from starlette.responses import JSONResponse

from app.database import check_database_connection
from app.config import settings
from app.routers import auth, health

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


@app.exception_handler(SQLAlchemyError)
async def database_error(request, error):
    return JSONResponse(status_code=503, content={"detail": "Database is temporarily unavailable"})


@app.get("/api/health/database")
async def database_health():
    try:
        await check_database_connection()
    except Exception as error:
        raise HTTPException(503, "Database connection failed") from error
    return {"status": "ok", "database": "connected"}
