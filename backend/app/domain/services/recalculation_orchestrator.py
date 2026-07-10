"""RecalculationOrchestrator — полный пересчёт сценария."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.services.aggregation_service import AggregationService
from app.domain.services.completeness_validator import CompletenessValidator
from app.domain.services.consensus_service import ConsensusService, FinancialResultCalculator
from app.infrastructure.db.models import CashFlowLine, FinancialResult, Scenario, ScenarioStatus


class RecalculationOrchestrator:
    def __init__(self):
        self.consensus = ConsensusService()
        self.calculator = FinancialResultCalculator()
        self.aggregation = AggregationService()
        self.completeness = CompletenessValidator()

    def recalculate(self, db: Session, scenario_id: UUID, skip_completeness: bool = False) -> dict:
        scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
        if not scenario:
            raise ValueError("Scenario not found")

        if not skip_completeness:
            check = self.completeness.validate_scenario(db, scenario_id)
            if not check["is_complete"]:
                raise ValueError(f"Incomplete data: {check['missing']}")

        self.consensus.recalc_for_cash_flow_lines(db, scenario_id)

        db.query(FinancialResult).filter(FinancialResult.scenario_id == scenario_id).delete()

        lines = db.query(CashFlowLine).filter(CashFlowLine.scenario_id == scenario_id).all()
        calculated = self.calculator.calculate_from_cash_flows(lines)
        self.calculator.persist_results(db, scenario_id, calculated, is_consolidated=False)

        self.aggregation.consolidate(db, scenario_id)

        scenario.status = ScenarioStatus.calculated
        scenario.calculated_at = datetime.now(timezone.utc)
        db.commit()

        return {
            "scenario_id": str(scenario_id),
            "status": scenario.status.value,
            "calculated_at": scenario.calculated_at.isoformat(),
            "lines_processed": len(lines),
        }
