from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json
import os
import time
import logging

from app.vinayak.infrastructure.cache.redis_client import RedisCache
from app.vinayak.infrastructure.db.repositories.execution_repository import ExecutionRepository
from app.vinayak.infrastructure.db.repositories.signal_repository import SignalRepository
from vinayak.observability.alerting import build_active_alerts
from vinayak.observability.observability_logger import tail_events
from vinayak.observability.observability_metrics import get_observability_snapshot
from app.vinayak.infrastructure.db.engine import build_session_factory

logger = logging.getLogger(__name__)

# -----------------------------
# Cache
# -----------------------------
_REDIS_CACHE = RedisCache.from_env()

_LATEST_ANALYSIS_TTL_SECONDS = 2.0
_LATEST_ANALYSIS_CACHE: dict[str, Any] = {
    "signature": None,
    "loaded_at": 0.0,
    "value": {},
}

# -----------------------------
# Helpers
# -----------------------------
def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except Exception:
        return default


def _parse_ts(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    for candidate in (raw, raw.replace("Z", "+00:00")):
        try:
            return datetime.fromisoformat(candidate)
        except Exception:
            continue
    return None


def _reports_dir() -> Path:
    return Path(os.getenv("REPORTS_DIR", "app/vinayak/data/reports"))


# -----------------------------
# Latest analysis (sync – OK)
# -----------------------------
def _load_latest_analysis() -> dict[str, Any]:
    try:
        cached = (
            _REDIS_CACHE.get_json("vinayak:artifact:latest_live_analysis")
            if _REDIS_CACHE.is_configured()
            else None
        )
        if isinstance(cached, dict) and cached:
            return cached

        report_files = sorted(
            _reports_dir().glob("*live_analysis_result.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        latest_path = report_files[0] if report_files else None

        if not latest_path or not latest_path.exists() or latest_path.stat().st_size == 0:
            _LATEST_ANALYSIS_CACHE.update(
                {"signature": None, "loaded_at": time.monotonic(), "value": {}}
            )
            return {}

        stat = latest_path.stat()
        signature = (str(latest_path.resolve()), stat.st_mtime_ns, stat.st_size)

        now = time.monotonic()

        if (
            _LATEST_ANALYSIS_CACHE.get("signature") == signature
            and (now - _LATEST_ANALYSIS_CACHE.get("loaded_at", 0))
            <= _LATEST_ANALYSIS_TTL_SECONDS
        ):
            return dict(_LATEST_ANALYSIS_CACHE.get("value", {}))

        payload = json.loads(latest_path.read_text())
        value = payload if isinstance(payload, dict) else {}

        _LATEST_ANALYSIS_CACHE.update(
            {"signature": signature, "loaded_at": now, "value": value}
        )

        return dict(value)

    except Exception as e:
        logger.exception("Failed to load latest analysis")
        return {}


# -----------------------------
# Async DB loader
# -----------------------------
async def _load_latest_canonical_state() -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        SessionLocal = build_session_factory()

        async with SessionLocal() as session:
            signal_repo = SignalRepository(session)
            exec_repo = ExecutionRepository(session)

            latest_signal_record = await signal_repo.get_latest_signal()
            latest_execution_record = await exec_repo.get_latest_execution()

            latest_signal: dict[str, Any] = {}
            latest_execution: dict[str, Any] = {}

            if latest_signal_record:
                latest_signal = {
                    "symbol": latest_signal_record.symbol,
                    "side": latest_signal_record.side,
                    "entry_price": latest_signal_record.entry_price,
                    "stop_loss": latest_signal_record.stop_loss,
                    "target_price": latest_signal_record.target_price,
                    "timestamp": (
                        latest_signal_record.signal_time.strftime("%Y-%m-%d %H:%M:%S")
                        if latest_signal_record.signal_time
                        else ""
                    ),
                }

            if latest_execution_record:
                latest_execution = {
                    "execution_status": str(latest_execution_record.status or ""),
                    "broker_name": str(latest_execution_record.broker or ""),
                    "price": _safe_float(latest_execution_record.executed_price),
                    "reason": str(latest_execution_record.notes or ""),
                }

            return latest_signal, latest_execution

    except Exception:
        logger.exception("DB load failed")
        return {}, {}


# -----------------------------
# Main API builder (ASYNC)
# -----------------------------
async def build_observability_dashboard_payload() -> dict[str, Any]:
    snapshot = get_observability_snapshot()
    now = datetime.now(UTC)

    latest_analysis = _load_latest_analysis()

    # ✅ correct async usage
    canonical_signal, canonical_execution = await _load_latest_canonical_state()

    latest_signal = dict(
        canonical_signal
        or ((latest_analysis.get("signals") or [{}])[-1]
            if latest_analysis.get("signals") else {})
    )

    latest_execution = dict(
        canonical_execution
        or ((latest_analysis.get("execution_rows") or [{}])[-1]
            if latest_analysis.get("execution_rows") else {})
    )

    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "latest_signal": latest_signal,
        "latest_execution": latest_execution,
        "alerts": build_active_alerts(snapshot),
        "recent_failures": tail_events(10),
    }


__all__ = ["build_observability_dashboard_payload"]