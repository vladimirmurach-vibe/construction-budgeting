class DisaggregationService:
    def distribute_adjustment(self, lines, total_adjustment: float) -> None:
        base_total = sum(float(line.base_amount or 0) for line in lines)
        if not lines:
            return

        if base_total == 0:
            share = float(total_adjustment) / len(lines)
            for line in lines:
                line.adjustment = share
            return

        for line in lines:
            line.adjustment = float(total_adjustment) * (float(line.base_amount or 0) / base_total)
