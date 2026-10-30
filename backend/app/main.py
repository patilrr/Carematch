from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import appointments, auth, providers
from app.core.config import settings
from app.db.session import Base, engine
from app import models  # noqa: F401 — registers SQLAlchemy models
from app import models

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Local-development convenience only. Use Alembic migrations for a deployed environment.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", description="Healthcare provider matching and appointment scheduling prototype", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(providers.router, prefix="/api/v1")
app.include_router(appointments.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}
