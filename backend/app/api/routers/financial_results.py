from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import FinancialResultResponse
from app.domain.services.aggregation_service import AggregationService
from app.infrastructure.db.models import FinancialResult, User, UserRole
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/financial-results", tags=["financial-results"])
aggregation = AggregationService()


@router.get("", response_model=list[FinancialResultResponse])
def list_financial_results(
    scenario_id: UUID = Query(...),
    construction_object_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.project_manager and user.construction_object_id:
        construction_object_id = user.construction_object_id

    query = db.query(FinancialResult).filter(
        FinancialResult.scenario_id == scenario_id,
        FinancialResult.is_consolidated == False,  # noqa: E712
    )
    if construction_object_id:
        query = query.filter(FinancialResult.construction_object_id == construction_object_id)
    return query.order_by(FinancialResult.period).all()


@router.get("/consolidated")
def get_consolidated(
    scenario_id: UUID = Query(...),
    period_from: Optional[str] = Query(None),
    period_to: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = aggregation.get_consolidated(db, scenario_id)
    if period_from:
        data = [r for r in data if r["period"] >= period_from]
    if period_to:
        data = [r for r in data if r["period"] <= period_to]
    return data


@router.get("/by-object")
def get_by_object(
    scenario_id: UUID = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    filters = {"scenario_id": scenario_id}
    if user.role == UserRole.project_manager and user.construction_object_id:
        filters["construction_object_id"] = user.construction_object_id
    return aggregation.aggregate(db, scenario_id, group_by=["construction_object_id", "period"], filters=filters)


@router.get("/summary")
def get_summary(
    scenario_id: UUID = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    consolidated = aggregation.get_consolidated(db, scenario_id)
    return {
        "total_revenue": sum(r["revenue"] for r in consolidated),
        "total_costs": sum(r["costs"] for r in consolidated),
        "total_profit": sum(r["profit"] for r in consolidated),
        "objects_count": db.query(FinancialResult.construction_object_id)
        .filter(FinancialResult.scenario_id == scenario_id, FinancialResult.is_consolidated == False)  # noqa: E712
        .distinct()
        .count(),
    }
