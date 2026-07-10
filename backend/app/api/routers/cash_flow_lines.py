from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_roles
from app.api.schemas import AdjustmentRequest, CashFlowLineResponse, CashFlowLineUpdate
from app.domain.services.consensus_service import ConsensusService
from app.domain.services.disaggregation_service import DisaggregationService
from app.infrastructure.db.models import CashFlowLine, CashFlowSource, ConstructionObject, User, UserRole
from app.infrastructure.db.session import get_db

router = APIRouter(tags=["cash-flow-lines"])
consensus = ConsensusService()
disaggregation = DisaggregationService()


@router.get("/cash-flow-lines", response_model=list[CashFlowLineResponse])
def list_cash_flow_lines(
    scenario_id: UUID = Query(...),
    source: Optional[CashFlowSource] = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(CashFlowLine).filter(CashFlowLine.scenario_id == scenario_id)
    if source:
        query = query.filter(CashFlowLine.source == source)
    if user.role == UserRole.project_manager and user.construction_object_id:
        query = query.filter(CashFlowLine.construction_object_id == user.construction_object_id)
    return query.all()


@router.get("/cash-flow-lines/grid")
def get_grid_data(
    scenario_id: UUID = Query(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        db.query(CashFlowLine)
        .options(joinedload(CashFlowLine.construction_object))
        .filter(CashFlowLine.scenario_id == scenario_id)
    )
    if user.role == UserRole.project_manager and user.construction_object_id:
        query = query.filter(CashFlowLine.construction_object_id == user.construction_object_id)

    rows = []
    for line in query.all():
        rows.append({
            "id": str(line.id),
            "construction_object_name": line.construction_object.name if line.construction_object else "",
            "form_code": line.form_code,
            "line_item": line.line_item,
            "period": line.period,
            "base_amount": float(line.base_amount),
            "adjustment": float(line.adjustment or 0),
            "consensus_amount": float(line.consensus_amount),
            "actual_amount": float(line.actual_amount) if line.actual_amount is not None else None,
        })
    return rows


@router.patch("/cash-flow-lines/{line_id}", response_model=CashFlowLineResponse)
def update_cash_flow_line(
    line_id: UUID,
    body: CashFlowLineUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.budget_analyst, UserRole.project_manager)),
):
    line = db.query(CashFlowLine).filter(CashFlowLine.id == line_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Not found")
    if user.role == UserRole.project_manager and line.construction_object_id != user.construction_object_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if body.base_amount is not None:
        line.base_amount = body.base_amount
    if body.adjustment is not None:
        line.adjustment = body.adjustment
    line.consensus_amount = float(consensus.calculate_for_record(line.base_amount, line.adjustment))
    db.commit()
    db.refresh(line)
    return line


@router.post("/adjustment")
def apply_adjustment(
    scenario_id: UUID,
    body: AdjustmentRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.budget_analyst, UserRole.project_manager)),
):
    updated = disaggregation.disaggregate(
        db,
        scenario_id,
        body.form_code,
        body.period,
        Decimal(str(body.total_adjustment)),
        body.construction_object_id,
    )
    db.commit()
    return {"updated": updated}


@router.post("/pivot")
def pivot_aggregate(
    scenario_id: UUID,
    rows: list[str] | None = None,
    cols: list[str] | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Агрегированная таблица для mod-pivot-tabulator."""
    query = (
        db.query(CashFlowLine)
        .options(joinedload(CashFlowLine.construction_object))
        .filter(CashFlowLine.scenario_id == scenario_id)
    )
    if user.role == UserRole.project_manager and user.construction_object_id:
        query = query.filter(CashFlowLine.construction_object_id == user.construction_object_id)

    data = []
    for line in query.all():
        data.append({
            "construction_object_name": line.construction_object.name if line.construction_object else "",
            "form_code": line.form_code,
            "line_item": line.line_item,
            "period": line.period,
            "base_amount": float(line.base_amount),
            "adjustment": float(line.adjustment or 0),
            "consensus_amount": float(line.consensus_amount),
            "actual_amount": float(line.actual_amount) if line.actual_amount is not None else None,
        })
    return {"data": data, "rows": rows or ["construction_object_name", "form_code", "line_item"], "cols": cols or ["period"]}
