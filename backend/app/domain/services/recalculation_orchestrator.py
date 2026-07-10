from collections import defaultdict
from datetime import datetime

from app.domain.services.aggregation_service import AggregationService
from app.domain.services.completeness_validator import CompletenessValidator
from app.domain.services.consensus_service import ConsensusService


class RecalculationOrchestrator:
    def __init__(
        self,
        consensus_service: ConsensusService | None = None,
        aggregation_service: AggregationService | None = None,
        completeness_validator: CompletenessValidator | None = None,
    ):
        self.consensus_service = consensus_service or ConsensusService()
        self.aggregation_service = aggregation_service or AggregationService()
        self.completeness_validator = completeness_validator or CompletenessValidator()

    def recalculate(
        self,
        scenario,
        cash_flow_lines,
        construction_objects,
        required_form_codes: set[str],
        financial_result_cls,
    ):
        is_complete, missing = self.completeness_validator.validate(
            scenario, required_form_codes, cash_flow_lines
        )
        if not is_complete:
            raise ValueError(f"Scenario is incomplete. Missing: {', '.join(missing)}")

        self.consensus_service.recalculate_lines(cash_flow_lines)

        lines_by_key = defaultdict(list)
        for line in cash_flow_lines:
            lines_by_key[(line.construction_object_id, line.period)].append(line)

        object_results = []
        object_ids = {obj.id for obj in construction_objects}
        horizon = self.aggregation_service.horizon(construction_objects)
        for object_id in sorted(object_ids):
            for period in horizon:
                lines = lines_by_key.get((object_id, period), [])
                revenue = sum(
                    float(line.consensus_amount or 0)
                    for line in lines
                    if self._is_revenue(line.line_item)
                )
                costs = sum(
                    float(line.consensus_amount or 0)
                    for line in lines
                    if not self._is_revenue(line.line_item)
                )
                object_results.append(
                    financial_result_cls(
                        scenario_id=scenario.id,
                        construction_object_id=object_id,
                        period=period,
                        revenue=revenue,
                        costs=costs,
                        profit=self.consensus_service.calculate_profit(revenue, costs),
                        is_consolidated=False,
                    )
                )

        consolidated = self.aggregation_service.consolidate(
            object_results, scenario.id, financial_result_cls
        )
        scenario.status = "calculated"
        scenario.calculated_at = datetime.utcnow()
        return object_results + consolidated

    @staticmethod
    def _is_revenue(line_item: str) -> bool:
        normalized = line_item.lower()
        return "revenue" in normalized or "выруч" in normalized or "sales" in normalized
