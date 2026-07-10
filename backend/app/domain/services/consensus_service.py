class ConsensusService:
    def recalculate_line(self, line) -> None:
        line.consensus_amount = float(line.base_amount or 0) + float(line.adjustment or 0)

    def recalculate_lines(self, lines) -> None:
        for line in lines:
            self.recalculate_line(line)

    @staticmethod
    def calculate_profit(revenue: float, costs: float) -> float:
        return float(revenue or 0) - float(costs or 0)
