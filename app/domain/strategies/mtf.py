from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.domain.models.context import StrategyContext
from app.domain.models.signal import StrategySignal
from app.domain.strategies.base import BaseStrategy, StrategyConfig


@dataclass(slots=True)
class MTFConfig(StrategyConfig):
    higher_timeframe: str = "1D"


class MTFStrategy(BaseStrategy):
    name = "MTF"

    def __init__(self, config: MTFConfig | None = None) -> None:
        super().__init__(config or MTFConfig())

    def generate_signals(self, candles: pd.DataFrame, context: StrategyContext) -> list[StrategySignal]:
        return []

    def calculate_levels(self, candles: pd.DataFrame, index: int, side: str, context: StrategyContext) -> tuple[float, float]:
        row = candles.iloc[index]
        close = float(row["close"])
        buffer = max(float(row["avg_range_5"]) * 0.4, close * 0.001, 0.05)
        if side.upper() == "BUY":
            stop_loss = float(row["low"]) - buffer
            return stop_loss, close + (close - stop_loss) * float(context.rr_ratio)
        stop_loss = float(row["high"]) + buffer
        return stop_loss, close - (stop_loss - close) * float(context.rr_ratio)
