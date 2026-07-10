"""ConsensusService — модуль consensus-calculator (v1.0.0)."""
from decimal import Decimal
from typing import Iterable

from sqlalchemy.orm import Session

from app.infrastructure.db.models import CashFlowLine, FinancialResult


class ConsensusService:
    """consensus_amount = base_amount + adjustment; profit = revenue - costs."""

    @staticmethod
    def calculate_for_record(base_amount: Decimal | float, adjustment: Decimal | float | None) -> Decimal:
        adj = Decimal(str(adjustment or 0))
        return Decimal(str(base_amount)) + adj

    def recalc_for_cash_flow_lines(self, db: Session, scenario_id) -> int:
        lines = db.query(CashFlowLine).filter(CashFlowLine.scenario_id == scenario_id).all()
        count = 0
        for line in lines:
            line.consensus_amount = self.calculate_for_record(line.base_amount, line.adjustment)
            count += 1
        db.flush()
        return count

    def audit_consistency(self, db: Session, scenario_id) -> list[str]:
        issues: list[str] = []
        lines = db.query(CashFlowLine).filter(CashFlowLine.scenario_id == scenario_id).all()
        for line in lines:
            expected = self.calculate_for_record(line.base_amount, line.adjustment)
            if Decimal(str(line.consensus_amount)) != expected:
                issues.append(f"Line {line.id}: consensus mismatch")
        return issues


class FinancialResultCalculator:
    """Расчёт финансового результата: profit = revenue - costs."""

    REVENUE_ITEMS = {"выручка", "revenue", "доход"}
    COST_ITEMS = {"затраты", "costs", "расход", "материалы", "работы"}

    @classmethod
    def classify_line_item(cls, line_item: str) -> str:
        lower = line_item.lower()
        if any(k in lower for k in cls.REVENUE_ITEMS):
            return "revenue"
        return "costs"

    def calculate_from_cash_flows(self, lines: Iterable[CashFlowLine]) -> dict[str, dict[str, Decimal]]:
        """Возвращает {object_id: {period: {revenue, costs, profit}}}."""
        buckets: dict[str, dict[str, dict[str, Decimal]]] = {}
        for line in lines:
            obj_key = str(line.construction_object_id)
            buckets.setdefault(obj_key, {})
            buckets[obj_key].setdefault(line.period, {"revenue": Decimal(0), "costs": Decimal(0)})
            amount = Decimal(str(line.consensus_amount))
            kind = self.classify_line_item(line.line_item)
            buckets[obj_key][line.period][kind] += amount

        result: dict[str, dict[str, dict[str, Decimal]]] = {}
        for obj_id, periods in buckets.items():
            result[obj_id] = {}
            for period, vals in periods.items():
                profit = vals["revenue"] - vals["costs"]
                result[obj_id][period] = {**vals, "profit": profit}
        return result

    def persist_results(
        self, db: Session, scenario_id, calculated: dict[str, dict[str, dict[str, Decimal]]], is_consolidated: bool = False
    ) -> None:
        import uuid

        for obj_id, periods in calculated.items():
            for period, vals in periods.items():
                fr = FinancialResult(
                    scenario_id=scenario_id,
                    construction_object_id=None if is_consolidated else uuid.UUID(obj_id),
                    period=period,
                    revenue=float(vals["revenue"]),
                    costs=float(vals["costs"]),
                    profit=float(vals["profit"]),
                    is_consolidated=is_consolidated,
                )
                db.add(fr)
