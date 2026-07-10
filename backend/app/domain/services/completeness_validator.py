"""CompletenessValidator — REQ-013, кастомная логика fastapi-base."""
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.db.models import CashFlowLine, ConstructionObject, InputForm, Scenario, ScenarioScope


class CompletenessValidator:
    def validate_scenario(self, db: Session, scenario_id: UUID) -> dict:
        scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            return {"is_complete": False, "missing": ["scenario not found"]}

        forms = db.query(InputForm).all()
        if scenario.scope == ScenarioScope.single_object:
            objects = [scenario.construction_object_id] if scenario.construction_object_id else []
        else:
            objects = [o.id for o in db.query(ConstructionObject).all()]

        missing: list[str] = []
        for obj_id in objects:
            for form in forms:
                count = (
                    db.query(CashFlowLine)
                    .filter(
                        CashFlowLine.scenario_id == scenario_id,
                        CashFlowLine.construction_object_id == obj_id,
                        CashFlowLine.form_code == form.code,
                    )
                    .count()
                )
                if count == 0:
                    missing.append(f"object={obj_id}, form={form.code}")

        return {"is_complete": len(missing) == 0, "missing": missing}

    def get_fill_indicators(self, db: Session, scenario_id: UUID) -> list[dict]:
        scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        forms = db.query(InputForm).all()
        if scenario and scenario.scope == ScenarioScope.single_object:
            objects = db.query(ConstructionObject).filter(
                ConstructionObject.id == scenario.construction_object_id
            ).all()
        else:
            objects = db.query(ConstructionObject).all()

        indicators = []
        for obj in objects:
            for form in forms:
                count = (
                    db.query(CashFlowLine)
                    .filter(
                        CashFlowLine.scenario_id == scenario_id,
                        CashFlowLine.construction_object_id == obj.id,
                        CashFlowLine.form_code == form.code,
                    )
                    .count()
                )
                indicators.append({
                    "construction_object_id": str(obj.id),
                    "construction_object_name": obj.name,
                    "form_code": form.code,
                    "filled": count > 0,
                    "line_count": count,
                })
        return indicators
