# """ from __future__ import annotations

# from functools import lru_cache
# from pathlib import Path

# from sqlalchemy import create_engine
# from sqlalchemy.engine import Engine
# from sqlalchemy.orm import DeclarativeBase, sessionmaker

# from vinayak.core.config import get_settings


# class Base(DeclarativeBase):
#     pass


# def get_database_url() -> str:
#     return get_settings().sql.url


# def get_database_provider() -> str:
#     return get_settings().sql.provider


# def _ensure_sqlite_parent_dir(url: str) -> None:
#     if not str(url or '').startswith('sqlite:///'):
#         return
#     raw_path = str(url).replace('sqlite:///', '', 1).strip()
#     if not raw_path:
#         return
#     db_path = Path(raw_path)
#     parent = db_path.parent
#     if parent and not parent.exists():
#         parent.mkdir(parents=True, exist_ok=True)


# @lru_cache(maxsize=8)
# def get_engine(database_url: str | None = None) -> Engine:
#     url = database_url or get_database_url()
#     _ensure_sqlite_parent_dir(url)

#     is_sqlite = url.startswith("sqlite")

#     connect_args = {"check_same_thread": False} if is_sqlite else {}

#     engine_kwargs = {
#         "future": True,
#         "connect_args": connect_args,
#         "pool_pre_ping": not is_sqlite,
#     }

#     # Only apply pooling configs for non-SQLite DBs
#     if not is_sqlite:
#         engine_kwargs.update({
#             "pool_size": 5,
#             "max_overflow": 10,
#         })

#     return create_engine(url, **engine_kwargs)

# @lru_cache(maxsize=8)
# def build_session_factory(database_url: str | None = None) -> sessionmaker:
#     engine = get_engine(database_url)
#     return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# def reset_database_state(database_url: str | None = None) -> None:
#     try:from __future__ import annotations

# from functools import lru_cache
# from pathlib import Path

# from sqlalchemy import create_engine
# from sqlalchemy.engine import Engine
# from sqlalchemy.orm import DeclarativeBase, sessionmaker

# from vinayak.core.config import get_settings


# class Base(DeclarativeBase):
#     pass


# def get_database_url() -> str:
#     return get_settings().sql.url


# def get_database_provider() -> str:
#     return get_settings().sql.provider


# def _ensure_sqlite_parent_dir(url: str) -> None:
#     if not str(url or "").startswith("sqlite:///"):
#         return

#     raw_path = str(url).replace("sqlite:///", "", 1).strip()
#     if not raw_path:
#         return

#     db_path = Path(raw_path)
#     parent = db_path.parent

#     if parent and not parent.exists():
#         parent.mkdir(parents=True, exist_ok=True)


# # ✅ ONE engine only
# @lru_cache(maxsize=1)
# def get_engine(database_url: str | None = None) -> Engine:
#     url = database_url or get_database_url()
#     _ensure_sqlite_parent_dir(url)

#     is_sqlite = url.startswith("sqlite:///")

#     connect_args = {"check_same_thread": False} if is_sqlite else {}

#     engine_kwargs = {
#         "future": True,
#         "connect_args": connect_args,
#         "pool_pre_ping": not is_sqlite,
#     }

#     if not is_sqlite:
#         engine_kwargs.update({
#             "pool_size": 10,
#             "max_overflow": 20,
#             "pool_timeout": 30,
#             "pool_recycle": 1800,
#         })

#     return create_engine(url, **engine_kwargs)


# @lru_cache(maxsize=1)
# def build_session_factory(database_url: str | None = None) -> sessionmaker:
#     engine = get_engine(database_url)

#     return sessionmaker(
#         bind=engine,
#         autoflush=False,
#         autocommit=False,
#         future=True,
#     )


# def reset_database_state(database_url: str | None = None) -> None:
#     try:
#         engine = get_engine(database_url)
#         engine.dispose()
#     except Exception:
#         pass

#     build_session_factory.cache_clear()
#     get_engine.cache_clear()


# def initialize_database(database_url: str | None = None) -> None:
#     # Import all models so SQLAlchemy registers them
#     import vinayak.db.models  # ✅ better than individual imports

#     Base.metadata.create_all(bind=get_engine(database_url))


# SessionLocal = build_session_factory()
#         engine = get_engine(database_url)
#         engine.dispose()
#     except Exception:
#         pass
#     build_session_factory.cache_clear()
#     get_engine.cache_clear()


# def initialize_database(database_url: str | None = None) -> None:
#     from vinayak.db.models.deferred_execution_job import DeferredExecutionJobRecord  # noqa: F401
#     from vinayak.db.models.execution import ExecutionRecord  # noqa: F401
#     from vinayak.db.models.execution_audit_log import ExecutionAuditLogRecord  # noqa: F401
#     from vinayak.db.models.live_analysis_job import LiveAnalysisJobRecord  # noqa: F401
#     from vinayak.db.models.outbox_event import OutboxEventRecord  # noqa: F401
#     from vinayak.db.models.production import (  # noqa: F401
#         AuditLogRecord,
#         BacktestReportRecord,
#         ExecutionRecordV2,
#         ExecutionRequestRecord,
#         PositionRecord,
#         SignalRecordV2,
#         StrategyRunRecord,
#         ValidationLogRecord,
#     )
#     from vinayak.db.models.reviewed_trade import ReviewedTradeRecord  # noqa: F401
#     from vinayak.db.models.signal import SignalRecord  # noqa: F401
#     from vinayak.db.models.user import UserRecord  # noqa: F401
#     from vinayak.db.models.user_session import UserSessionRecord  # noqa: F401

#     Base.metadata.create_all(bind=get_engine(database_url))

# SessionLocal = build_session_factory()
 """