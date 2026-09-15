from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.redis_client import redis_client
from app.routers.auth import router as auth_router
from app.routers.projects import router as project_router
from app.routers.tasks import router as task_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis_client.aclose()

app = FastAPI(title=settings.app_title, lifespan=lifespan)

app.include_router(auth_router)
app.include_router(task_router)
app.include_router(project_router)


@app.get("/health", tags=["service"])
def health():
    return {"status": "ok"}
