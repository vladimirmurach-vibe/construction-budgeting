from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.models import FinancialResult, User
from app.infrastructure.db.session import get_db
from app.presentation.api.deps import get_current_user
from app.presentation.api.schemas import FinancialResultRead


router = APIRouter(prefix="/financial-results", tags=["financial-results"])


@router.get("", response_model=list[FinancialResultRead])
def list_results(
    scenario_id: int,
    construction_object_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(FinancialResult).filter(
        FinancialResult.scenario_id == scenario_id,
        FinancialResult.is_consolidated.is_(False),
    )
    if construction_object_id is not None:
        query = query.filter(FinancialResult.construction_object_id == construction_object_id)
    return query.order_by(FinancialResult.period, FinancialResult.construction_object_id).all()


@router.get("/consolidated", response_model=list[FinancialResultRead])
def consolidated_results(
    scenario_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        db.query(FinancialResult)
        .filter(
            FinancialResult.scenario_id == scenario_id,
            FinancialResult.is_consolidated.is_(True),
        )
        .order_by(FinancialResult.period)
        .all()
    )
