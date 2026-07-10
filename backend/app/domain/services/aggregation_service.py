from collections import defaultdict
from datetime import date


def month_range(start: date, end: date) -> list[str]:
    months: list[str] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return months


class AggregationService:
    def horizon(self, objects) -> list[str]:
        objects = list(objects)
        if not objects:
            return []
        start = min(obj.construction_start for obj in objects)
        end = max(obj.construction_end for obj in objects)
        return month_range(start, end)

    def consolidate(self, object_results, scenario_id: int, financial_result_cls):
        grouped = defaultdict(lambda: {"revenue": 0.0, "costs": 0.0, "profit": 0.0})
        for result in object_results:
            grouped[result.period]["revenue"] += float(result.revenue or 0)
            grouped[result.period]["costs"] += float(result.costs or 0)
            grouped[result.period]["profit"] += float(result.profit or 0)

        return [
            financial_result_cls(
                scenario_id=scenario_id,
                construction_object_id=None,
                period=period,
                revenue=values["revenue"],
                costs=values["costs"],
                profit=values["profit"],
                is_consolidated=True,
            )
            for period, values in sorted(grouped.items())
        ]
