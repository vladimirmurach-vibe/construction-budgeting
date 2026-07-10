from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domain.services.consensus_service import ConsensusService
from app.infrastructure.db.models import CashFlowLine, User
from app.infrastructure.db.session import get_db
from app.presentation.api.deps import get_current_user
from app.presentation.api.schemas import CashFlowLineRead, CashFlowLineUpdate


router = APIRouter(prefix="/cash-flow-lines", tags=["cash-flow-lines"])


@router.get("", response_model=list[CashFlowLineRead])
def list_lines(
    scenario_id: int | None = None,
    construction_object_id: int | None = None,
    source: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(CashFlowLine)
    if scenario_id is not None:
        query = query.filter(CashFlowLine.scenario_id == scenario_id)
    if construction_object_id is not None:
        query = query.filter(CashFlowLine.construction_object_id == construction_object_id)
    if source is not None:
        query = query.filter(CashFlowLine.source == source)
    return query.order_by(CashFlowLine.id).all()


@router.patch("/{line_id}", response_model=CashFlowLineRead)
def patch_line(
    line_id: int,
    payload: CashFlowLineUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    line = db.get(CashFlowLine, line_id)
    if line is None:
        raise HTTPException(status_code=404, detail="Cash flow line not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(line, key, value)
    ConsensusService().recalculate_line(line)
    db.commit()
    db.refresh(line)
    return line
