from app.core.config import settings
from fastapi import FastAPI

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}
