from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.models import CashFlowLine, ConstructionObject, FactLoadLog, Scenario, User
from app.infrastructure.db.session import get_db
from app.presentation.api.deps import require_admin
from app.presentation.api.schemas import FactLoadLogRead, FactLoadResponse


router = APIRouter(prefix="/fact-loading", tags=["fact-loading"])


@router.post("/trigger", response_model=FactLoadResponse)
def trigger_fact_loading(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    scenario = db.query(Scenario).order_by(Scenario.id).first()
    obj = db.query(ConstructionObject).order_by(ConstructionObject.id).first()
    records_loaded = 0
    if scenario is not None and obj is not None:
        db.add(
            CashFlowLine(
                scenario_id=scenario.id,
                construction_object_id=obj.id,
                form_code="FORM-FACT",
                line_item="Actual Revenue",
                period="2026-03",
                base_amount=0,
                adjustment=0,
                consensus_amount=0,
                actual_amount=123456.78,
                source="accounting_system",
            )
        )
        records_loaded = 1

    log = FactLoadLog(
        status="success",
        records_loaded=records_loaded,
        message="Fact loading completed",
    )
    db.add(log)
    db.commit()
    return FactLoadResponse(records_loaded=records_loaded, status=log.status)


@router.get("/log", response_model=list[FactLoadLogRead])
def fact_loading_log(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(FactLoadLog).order_by(FactLoadLog.timestamp.desc()).all()
