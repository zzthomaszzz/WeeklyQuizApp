from fastapi import APIRouter, HTTPException, status

from app.database import check_database_connection


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}
