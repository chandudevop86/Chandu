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

__all__ = ["get_engine", "build_session_factory"]