import os
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import settings
from app.infrastructure.connectors.csv_data_source import CsvDataSource
from app.infrastructure.db.models import ConstructionObject, FactLoadLog, User, UserRole
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/fact-loading", tags=["fact-loading"])
csv_source = CsvDataSource()


@router.post("/trigger")
def trigger_fact_load(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
):
    import_dir = Path(settings.fact_import_dir)
    import_dir.mkdir(parents=True, exist_ok=True)
    files = list(import_dir.glob("fact_*.csv")) + list(import_dir.glob("fact_*.xlsx"))
    if not files:
        log = FactLoadLog(status="error", records_loaded=0, message="No fact files found")
        db.add(log)
        db.commit()
        return {"status": log.status, "records_loaded": 0, "message": log.message}

    objects = db.query(ConstructionObject).all()
    code_map = {o.code: o.id for o in objects}
    log = csv_source.load_fact_data(db, str(files[0]), code_map)
    return {
        "status": log.status,
        "records_loaded": log.records_loaded,
        "timestamp": log.timestamp.isoformat(),
        "message": log.message,
    }


@router.get("/log")
def fact_load_log(db: Session = Depends(get_db), _: User = Depends(require_roles(UserRole.admin))):
    logs = db.query(FactLoadLog).order_by(FactLoadLog.timestamp.desc()).limit(50).all()
    return [
        {
            "id": str(l.id),
            "status": l.status,
            "records_loaded": l.records_loaded,
            "message": l.message,
            "timestamp": l.timestamp.isoformat(),
        }
        for l in logs
    ]
