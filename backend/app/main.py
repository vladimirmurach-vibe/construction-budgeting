from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.infrastructure.db import models  # noqa: F401
from app.infrastructure.db.seed import seed_database
from app.infrastructure.db.session import Base, SessionLocal, engine
from app.presentation.api.routers import (
    auth,
    cash_flow_lines,
    construction_objects,
    fact_loading,
    financial_results,
    import_data,
    reports,
    scenarios,
    users,
)
from app.scheduler import create_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    settings.imports_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    scheduler = create_scheduler()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "app_name": settings.app_name}


app.include_router(auth.router, prefix="/api")
app.include_router(construction_objects.router, prefix="/api")
app.include_router(scenarios.router, prefix="/api")
app.include_router(cash_flow_lines.router, prefix="/api")
app.include_router(financial_results.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(import_data.router, prefix="/api")
app.include_router(fact_loading.router, prefix="/api")
app.include_router(users.router, prefix="/api")
