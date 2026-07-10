"""DisaggregationService — модуль adjustment-disaggregation (v1.0.0)."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.services.consensus_service import ConsensusService
from app.infrastructure.db.models import CashFlowLine


class DisaggregationService:
    """Распределение корректировки пропорционально base_amount."""

    def __init__(self):
        self.consensus = ConsensusService()

    def disaggregate(
        self,
        db: Session,
        scenario_id: UUID,
        form_code: str,
        period: str,
        total_adjustment: Decimal,
        construction_object_id: Optional[UUID] = None,
    ) -> int:
        query = db.query(CashFlowLine).filter(
            CashFlowLine.scenario_id == scenario_id,
            CashFlowLine.form_code == form_code,
            CashFlowLine.period == period,
        )
        if construction_object_id:
            query = query.filter(CashFlowLine.construction_object_id == construction_object_id)

        lines = query.all()
        if not lines:
            return 0

        base_sum = sum(Decimal(str(l.base_amount)) for l in lines)
        updated = 0
        if base_sum == 0:
            share = total_adjustment / len(lines)
            for line in lines:
                line.adjustment = float(share)
                line.consensus_amount = float(self.consensus.calculate_for_record(line.base_amount, line.adjustment))
                updated += 1
        else:
            for line in lines:
                ratio = Decimal(str(line.base_amount)) / base_sum
                line.adjustment = float(total_adjustment * ratio)
                line.consensus_amount = float(self.consensus.calculate_for_record(line.base_amount, line.adjustment))
                updated += 1

        db.flush()
        return updated
