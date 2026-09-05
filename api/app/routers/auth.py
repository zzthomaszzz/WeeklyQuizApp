from fastapi import APIRouter, HTTPException, status

from app.database import check_database_connection


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/health/database")
async def database_health():
    try:
        await check_database_connection()
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        ) from error

    return {
        "status": "ok",
        "database": "connected",
    }