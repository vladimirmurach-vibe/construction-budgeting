from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.domain.services.recalculation_orchestrator import RecalculationOrchestrator
from app.infrastructure.db.models import (
    CashFlowLine,
    ConstructionObject,
    FinancialResult,
    InputForm,
    Scenario,
    User,
)
from app.infrastructure.db.session import get_db
from app.presentation.api.deps import get_current_user
from app.presentation.api.schemas import CompareRow, ScenarioCreate, ScenarioRead, ScenarioUpdate


router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("/compare", response_model=list[CompareRow])
def compare_scenarios(
    version_a: int,
    version_b: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    totals = {}
    for scenario_id in [version_a, version_b]:
        rows = (
            db.query(FinancialResult)
            .filter(
                FinancialResult.scenario_id == scenario_id,
                FinancialResult.is_consolidated.is_(True),
            )
            .all()
        )
        if not rows:
            _recalculate_scenario(db, scenario_id)
            rows = (
                db.query(FinancialResult)
                .filter(
                    FinancialResult.scenario_id == scenario_id,
                    FinancialResult.is_consolidated.is_(True),
                )
                .all()
            )
        totals[scenario_id] = sum(float(row.profit or 0) for row in rows)

    a_value = totals.get(version_a, 0.0)
    b_value = totals.get(version_b, 0.0)
    variance = b_value - a_value
    variance_percent = None if a_value == 0 else (variance / a_value) * 100
    return [
        CompareRow(
            metric="profit",
            version_a=a_value,
            version_b=b_value,
            variance=variance,
            variance_percent=variance_percent,
        )
    ]


@router.get("", response_model=list[ScenarioRead])
def list_scenarios(
    include_archived: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Scenario)
    if not include_archived:
        query = query.filter(Scenario.status != "archived")
    return query.order_by(Scenario.created_at, Scenario.id).all()


@router.post("", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
def create_scenario(
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    version_number = 1
    parent = None
    if payload.parent_version_id is not None:
        parent = db.get(Scenario, payload.parent_version_id)
        if parent is None:
            raise HTTPException(status_code=422, detail="parent_version_id does not exist")
        version_number = parent.version_number + 1

    if payload.construction_object_id is not None and db.get(
        ConstructionObject, payload.construction_object_id
    ) is None:
        raise HTTPException(status_code=422, detail="construction_object_id does not exist")

    scenario = Scenario(
        name=payload.name,
        type=payload.type,
        scope=payload.scope,
        construction_object_id=payload.construction_object_id,
        parent_version_id=payload.parent_version_id,
        version_number=version_number,
        status="draft",
    )
    db.add(scenario)
    db.flush()
    _seed_scenario_lines(db, scenario, parent)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("/{scenario_id}", response_model=ScenarioRead)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.patch("/{scenario_id}", response_model=ScenarioRead)
def update_scenario(
    scenario_id: int,
    payload: ScenarioUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("scope", scenario.scope) == "single_object" and data.get(
        "construction_object_id", scenario.construction_object_id
    ) is None:
        raise HTTPException(status_code=422, detail="single_object scenarios require object")
    for key, value in data.items():
        setattr(scenario, key, value)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(scenario)
    db.commit()
    return None


@router.post("/{scenario_id}/recalculate", response_model=ScenarioRead)
def recalculate_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return _recalculate_scenario(db, scenario_id)


def _recalculate_scenario(db: Session, scenario_id: int) -> Scenario:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    lines = db.query(CashFlowLine).filter(CashFlowLine.scenario_id == scenario.id).all()
    if not lines:
        _seed_scenario_lines(db, scenario, None)
        db.flush()
        lines = db.query(CashFlowLine).filter(CashFlowLine.scenario_id == scenario.id).all()

    if scenario.scope == "single_object":
        objects = [db.get(ConstructionObject, scenario.construction_object_id)]
    else:
        object_ids = sorted({line.construction_object_id for line in lines})
        objects = db.query(ConstructionObject).filter(ConstructionObject.id.in_(object_ids)).all()
    objects = [obj for obj in objects if obj is not None]

    required_forms = {
        form.code for form in db.query(InputForm).filter(InputForm.is_required.is_(True)).all()
    }
    db.query(FinancialResult).filter(FinancialResult.scenario_id == scenario.id).delete()
    try:
        results = RecalculationOrchestrator().recalculate(
            scenario, lines, objects, required_forms, FinancialResult
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    db.add_all(results)
    db.commit()
    db.refresh(scenario)
    return scenario


def _seed_scenario_lines(db: Session, scenario: Scenario, parent: Scenario | None) -> None:
    source_lines = []
    if parent is not None:
        source_lines = db.query(CashFlowLine).filter(CashFlowLine.scenario_id == parent.id).all()
    if not source_lines:
        demo = db.query(Scenario).filter(Scenario.name == "Демо бюджет 2026").first()
        if demo is not None and demo.id != scenario.id:
            source_lines = db.query(CashFlowLine).filter(CashFlowLine.scenario_id == demo.id).all()

    allowed_object_ids = None
    if scenario.scope == "single_object":
        allowed_object_ids = {scenario.construction_object_id}

    for line in source_lines:
        if allowed_object_ids is not None and line.construction_object_id not in allowed_object_ids:
            continue
        db.add(
            CashFlowLine(
                scenario_id=scenario.id,
                construction_object_id=line.construction_object_id,
                form_code=line.form_code,
                line_item=line.line_item,
                period=line.period,
                base_amount=line.base_amount,
                adjustment=line.adjustment,
                consensus_amount=line.consensus_amount,
                actual_amount=line.actual_amount,
                source=line.source,
            )
        )
