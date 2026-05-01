from vinayak.db.db_async import (
    get_engine,
    build_session_factory,
)

import os

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vinayak.db")


def get_database_provider() -> str:
    url = get_database_url()

    if url.startswith("sqlite"):
        return "sqlite"
    elif url.startswith("postgresql"):
        return "postgresql"
    elif url.startswith("mysql"):
        return "mysql"
    return "unknown"
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

_engine = None
_SessionLocal = None


def build_session_factory():
    """
    Central async session factory
    """
    global _engine, _SessionLocal

    if _SessionLocal:
        return _SessionLocal

    from vinayak.core.config import get_settings

    settings = get_settings()
    database_url = settings.sql.url

    _engine = create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
    )

    _SessionLocal = async_sessionmaker(
        bind=_engine,
        expire_on_commit=False,
    )

    return _SessionLocal


async def initialize_database():
    """
    Optional startup initializer (safe for dev/prod)
    """
    SessionLocal = build_session_factory()

    async with SessionLocal() as conn:
        # If you use SQLAlchemy models:
        # from vinayak.db.base import Base
        # await conn.run_sync(Base.metadata.create_all)

        return True
__all__ = ["get_engine", "build_session_factory"]