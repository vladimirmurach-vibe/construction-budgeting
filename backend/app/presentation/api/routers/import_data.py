from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.connectors.csv_data_source import CsvDataSource
from app.infrastructure.db.models import CashFlowLine, User
from app.infrastructure.db.session import get_db
from app.presentation.api.deps import get_current_user
from app.presentation.api.schemas import ImportRequest, ImportValidateRequest


router = APIRouter(prefix="/import", tags=["import"])


@router.post("/validate")
def validate_import(
    payload: ImportValidateRequest,
    _: User = Depends(get_current_user),
):
    ok, missing = CsvDataSource().validate(payload.file_path)
    return {"valid": ok, "missing_columns": missing}


@router.post("/import")
def import_cash_flow_lines(
    payload: ImportRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    connector = CsvDataSource()
    ok, missing = connector.validate(payload.file_path)
    if not ok:
        raise HTTPException(status_code=422, detail={"missing_columns": missing})
    records_loaded = 0
    for record in connector.read(payload.file_path):
        line = CashFlowLine(
            scenario_id=payload.scenario_id,
            construction_object_id=int(record["construction_object_id"]),
            form_code=str(record["form_code"]),
            line_item=str(record["line_item"]),
            period=str(record["period"]),
            base_amount=float(record.get("base_amount", 0) or 0),
            adjustment=float(record.get("adjustment", 0) or 0),
            consensus_amount=float(record.get("base_amount", 0) or 0)
            + float(record.get("adjustment", 0) or 0),
            actual_amount=float(record.get("actual_amount", 0) or 0),
            source="import",
        )
        db.add(line)
        records_loaded += 1
    db.commit()
    return {"records_loaded": records_loaded}
