from app.core.config import settings
from app.db import check_database_connection
from fastapi import FastAPI, HTTPException, status

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}


@app.get("/health/db")
def database_health_check() -> dict[str, str]:
    """Report database readiness without exposing connection details."""

    if not check_database_connection():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        )
    return {"status": "ok", "database": "connected"}
