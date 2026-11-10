from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import aircraft, health, work_orders
from app.core.config import settings
from app.core.database import Base, engine
from app import models  # noqa: F401 - registers SQLAlchemy models


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Temporary bootstrap for the first iteration. Alembic migrations replace this later.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Independent aviation maintenance and operations portfolio application.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(aircraft.router, prefix="/api/v1")
app.include_router(work_orders.router, prefix="/api/v1")
