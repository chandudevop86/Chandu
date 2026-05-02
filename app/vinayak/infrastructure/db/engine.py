from __future__ import annotations

import os
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)

from vinayak.core.config import get_settings

# =========================
# GLOBALS
# =========================

_engine: AsyncEngine | None = None
_SessionLocal: async_sessionmaker[AsyncSession] | None = None


# =========================
# DATABASE CONFIG
# =========================

def get_database_url() -> str:
    settings = get_settings()
    return settings.sql.url


def get_database_provider() -> str:
    url = get_database_url().lower()

    if url.startswith("sqlite"):
        return "sqlite"
    if url.startswith("postgresql"):
        return "postgresql"
    if url.startswith("mysql"):
        return "mysql"
    return "unknown"


# =========================
# ENGINE
# =========================

def get_engine() -> AsyncEngine:
    global _engine

    if _engine:
        return _engine

    database_url = get_database_url()

    _engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )

    return _engine


# =========================
# SESSION FACTORY
# =========================

def build_session_factory() -> async_sessionmaker[AsyncSession]:
    global _SessionLocal

    if _SessionLocal:
        return _SessionLocal

    engine = get_engine()

    _SessionLocal = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    return _SessionLocal


# =========================
# DB INITIALIZER
# =========================

async def initialize_database() -> bool:
    """
    Initialize database (create tables if needed)
    """
    engine = get_engine()

    try:
        async with engine.begin() as conn:
            # Uncomment if using models
            # from vinayak.db.base import Base
            # await conn.run_sync(Base.metadata.create_all)
            pass

        return True
    except Exception:
        return False


# =========================
# EXPORTS
# =========================

__all__ = [
    "get_engine",
    "build_session_factory",
    "initialize_database",
    "get_database_url",
    "get_database_provider",
]