import os
import shutil
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import settings
from app.domain.services.completeness_validator import CompletenessValidator
from app.infrastructure.connectors.csv_data_source import CsvDataSource
from app.infrastructure.db.models import ConstructionObject, User, UserRole
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/import", tags=["import"])
csv_source = CsvDataSource()
completeness = CompletenessValidator()


@router.post("/validate")
async def validate_import(file: UploadFile = File(...)):
    os.makedirs(settings.fact_import_dir, exist_ok=True)
    path = os.path.join(settings.fact_import_dir, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    df = csv_source.read_file(path)
    return csv_source.validate(df)


@router.post("/{scenario_id}")
async def import_data(
    scenario_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin, UserRole.budget_analyst)),
):
    os.makedirs(settings.fact_import_dir, exist_ok=True)
    path = os.path.join(settings.fact_import_dir, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    objects = db.query(ConstructionObject).all()
    code_map = {o.code: o.id for o in objects}
    return csv_source.import_to_scenario(db, scenario_id, path, code_map)


@router.get("/completeness/{scenario_id}")
def check_completeness(scenario_id: UUID, db: Session = Depends(get_db)):
    return completeness.validate_scenario(db, scenario_id)


@router.get("/completeness/{scenario_id}/indicators")
def completeness_indicators(scenario_id: UUID, db: Session = Depends(get_db)):
    return completeness.get_fill_indicators(db, scenario_id)
