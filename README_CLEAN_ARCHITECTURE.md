# Clean Trading Architecture

Run the trading API without replacing the existing app entrypoint:

```powershell
uvicorn app.trading_main:app --reload
```

Core request:

```http
POST /trading/signals
```

Strategy modules implement one interface:

```python
prepare_data()
generate_signals()
calculate_levels()
```

Current implemented strategies:

- `amd`
- `breakout`
- `mean_reversion`

Migration mapping:

- Existing strategy code -> `app/domain/strategies/`
- Existing indicator code -> `app/domain/indicators/indicators.py`
- Existing position sizing/risk code -> `app/domain/risk/risk_manager.py`
- Existing strategy dispatcher -> `app/domain/engine/strategy_engine.py`
- Existing business service/API glue -> `app/application/` and `app/presentation/api/`
- Broker/data-provider code -> `app/infrastructure/`
