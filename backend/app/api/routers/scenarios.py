from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.api.schemas import ScenarioCreate, ScenarioResponse
from app.domain.services.recalculation_orchestrator import RecalculationOrchestrator
from app.infrastructure.db.models import CashFlowLine, Scenario, ScenarioScope, ScenarioStatus, User, UserRole
from app.infrastructure.db.session import get_db

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioResponse])
def list_scenarios(
    include_archived: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = db.query(Scenario)
    if not include_archived:
        query = query.filter(Scenario.status != ScenarioStatus.archived)
    if user.role == UserRole.project_manager and user.construction_object_id:
        query = query.filter(
            (Scenario.scope == ScenarioScope.all_objects)
            | (Scenario.construction_object_id == user.construction_object_id)
        )
    return query.order_by(Scenario.created_at.desc()).all()


@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
def create_scenario(
    body: ScenarioCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.budget_analyst, UserRole.project_manager)),
):
    if body.scope == ScenarioScope.single_object and not body.construction_object_id:
        raise HTTPException(status_code=422, detail="construction_object_id required for single_object")

    if body.parent_version_id:
        parent = db.query(Scenario).filter(Scenario.id == body.parent_version_id).first()
        version_number = (parent.version_number + 1) if parent else 1
    else:
        version_number = 1

    scenario = Scenario(
        name=body.name,
        type=body.type,
        scope=body.scope,
        construction_object_id=body.construction_object_id,
        version_number=version_number,
        parent_version_id=body.parent_version_id,
        status=ScenarioStatus.draft,
    )
    db.add(scenario)
    db.flush()

    if body.parent_version_id:
        parent_lines = db.query(CashFlowLine).filter(CashFlowLine.scenario_id == body.parent_version_id).all()
        for pl in parent_lines:
            db.add(CashFlowLine(
                scenario_id=scenario.id,
                construction_object_id=pl.construction_object_id,
                form_code=pl.form_code,
                line_item=pl.line_item,
                period=pl.period,
                base_amount=pl.base_amount,
                adjustment=pl.adjustment,
                consensus_amount=pl.consensus_amount,
                actual_amount=pl.actual_amount,
                source=pl.source,
            ))

    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/{scenario_id}", response_model=ScenarioResponse)
def get_scenario(scenario_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Not found")
    return scenario


@router.post("/{scenario_id}/recalculate")
def recalculate_scenario(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.budget_analyst, UserRole.project_manager)),
):
    orchestrator = RecalculationOrchestrator()
    try:
        return orchestrator.recalculate(db, scenario_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/{scenario_id}/archive", response_model=ScenarioResponse)
def archive_scenario(
    scenario_id: UUID,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.budget_analyst)),
):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Not found")
    scenario.status = ScenarioStatus.archived
    db.commit()
    db.refresh(scenario)
    return scenario
