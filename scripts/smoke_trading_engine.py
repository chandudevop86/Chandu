from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.application.trading_service import TradingService


def sample_candles() -> list[dict[str, float | str]]:
    start = datetime(2026, 1, 1, 9, 15)
    candles: list[dict[str, float | str]] = []
    price = 100.0
    for index in range(80):
        drift = 0.35 if index > 30 else 0.05
        open_price = price
        close_price = price + drift
        high = max(open_price, close_price) + 0.4
        low = min(open_price, close_price) - 0.4
        candles.append({"timestamp": (start + timedelta(minutes=index)).isoformat(), "open": round(open_price, 2), "high": round(high, 2), "low": round(low, 2), "close": round(close_price, 2), "volume": 1000 + index * 20})
        price = close_price
    return candles


def main() -> None:
    service = TradingService()
    for strategy_name in ("amd", "breakout", "mean_reversion"):
        signals = service.run_strategy(strategy_name=strategy_name, data=sample_candles(), symbol="TEST", capital=100000, risk_pct=1.0, rr_ratio=2.0)
        print(strategy_name, len(signals))


if __name__ == "__main__":
    main()
