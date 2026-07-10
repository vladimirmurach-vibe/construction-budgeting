"""AggregationService — модуль forecast-aggregation (v1.0.0)."""
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.db.models import ConstructionObject, FinancialResult, Scenario


class AggregationService:
    """Агрегация financial_result по объектам и периодам."""

    def aggregate(
        self,
        db: Session,
        scenario_id: UUID,
        group_by: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict]:
        group_by = group_by or ["construction_object_id", "period"]
        query = db.query(FinancialResult).filter(
            FinancialResult.scenario_id == scenario_id,
            FinancialResult.is_consolidated == False,  # noqa: E712
        )
        if filters:
            if "construction_object_id" in filters and filters["construction_object_id"]:
                query = query.filter(
                    FinancialResult.construction_object_id == filters["construction_object_id"]
                )
            if "period_from" in filters and filters["period_from"]:
                query = query.filter(FinancialResult.period >= filters["period_from"])
            if "period_to" in filters and filters["period_to"]:
                query = query.filter(FinancialResult.period <= filters["period_to"])

        rows = query.all()
        buckets: dict[tuple, dict] = defaultdict(lambda: {"revenue": Decimal(0), "costs": Decimal(0), "profit": Decimal(0)})

        for row in rows:
            key_parts = []
            for field in group_by:
                key_parts.append(getattr(row, field))
            key = tuple(key_parts)
            buckets[key]["revenue"] += Decimal(str(row.revenue))
            buckets[key]["costs"] += Decimal(str(row.costs))
            buckets[key]["profit"] += Decimal(str(row.profit))

        result = []
        for key, vals in buckets.items():
            item = {group_by[i]: key[i] for i in range(len(group_by))}
            item.update({k: float(v) for k, v in vals.items()})
            result.append(item)
        return result

    def consolidate(self, db: Session, scenario_id: UUID) -> list[FinancialResult]:
        """Консолидация по всем объектам на горизонте min(start)..max(end)."""
        objects = db.query(ConstructionObject).all()
        if not objects:
            return []

        horizon_start = min(o.construction_start for o in objects)
        horizon_end = max(o.construction_end for o in objects)
        horizon_periods = set(self._generate_periods(horizon_start, horizon_end))

        detail = db.query(FinancialResult).filter(
            FinancialResult.scenario_id == scenario_id,
            FinancialResult.is_consolidated == False,  # noqa: E712
        ).all()

        by_period: dict[str, dict[str, Decimal]] = defaultdict(
            lambda: {"revenue": Decimal(0), "costs": Decimal(0), "profit": Decimal(0)}
        )
        for row in detail:
            by_period[row.period]["revenue"] += Decimal(str(row.revenue))
            by_period[row.period]["costs"] += Decimal(str(row.costs))
            by_period[row.period]["profit"] += Decimal(str(row.profit))

        all_periods = sorted(horizon_periods | set(by_period.keys()))
        consolidated: list[FinancialResult] = []
        for period in all_periods:
            vals = by_period.get(period, {"revenue": Decimal(0), "costs": Decimal(0), "profit": Decimal(0)})
            fr = FinancialResult(
                scenario_id=scenario_id,
                construction_object_id=None,
                period=period,
                revenue=float(vals["revenue"]),
                costs=float(vals["costs"]),
                profit=float(vals["profit"]),
                is_consolidated=True,
            )
            consolidated.append(fr)
            db.add(fr)
        db.flush()
        return consolidated

    @staticmethod
    def _generate_periods(start: date, end: date) -> list[str]:
        periods = []
        year, month = start.year, start.month
        while (year, month) <= (end.year, end.month):
            periods.append(f"{year:04d}-{month:02d}")
            month += 1
            if month > 12:
                month = 1
                year += 1
        return periods

    def get_consolidated(self, db: Session, scenario_id: UUID) -> list[dict]:
        rows = db.query(FinancialResult).filter(
            FinancialResult.scenario_id == scenario_id,
            FinancialResult.is_consolidated == True,  # noqa: E712
        ).order_by(FinancialResult.period).all()
        return [
            {
                "period": r.period,
                "revenue": float(r.revenue),
                "costs": float(r.costs),
                "profit": float(r.profit),
                "is_consolidated": r.is_consolidated,
            }
            for r in rows
        ]
