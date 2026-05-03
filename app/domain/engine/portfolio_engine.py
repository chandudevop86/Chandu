from __future__ import annotations

from app.domain.models.position import Position


class PortfolioEngine:
    def total_unrealized_pnl(self, positions: list[Position], last_prices: dict[str, float]) -> float:
        return sum(position.unrealized_pnl(last_prices[position.symbol]) for position in positions if position.symbol in last_prices)
