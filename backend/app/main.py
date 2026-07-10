import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import (
    auth,
    cash_flow_lines,
    compare,
    construction_objects,
    fact_loading,
    financial_results,
    import_data,
    reports,
    scenarios,
    users,
)
from app.core.config import settings
from app.infrastructure.db.seed import seed_database
from app.infrastructure.db.session import Base, engine

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_database()
    logger.info("Application started")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.api_prefix

app.include_router(auth.router, prefix=prefix)
app.include_router(compare.router, prefix=prefix)
app.include_router(construction_objects.router, prefix=prefix)
app.include_router(scenarios.router, prefix=prefix)
app.include_router(cash_flow_lines.router, prefix=prefix)
app.include_router(financial_results.router, prefix=prefix)
app.include_router(reports.router, prefix=prefix)
app.include_router(import_data.router, prefix=prefix)
app.include_router(fact_loading.router, prefix=prefix)
app.include_router(users.router, prefix=prefix)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"app": settings.app_name, "docs": "/docs"}
