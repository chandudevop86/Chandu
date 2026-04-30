from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from vinayak.db.db_async import build_session_factory
from fastapi import FastAPI, Depends
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# -----------------------------
# Base model
# -----------------------------
class Base(DeclarativeBase):
    pass


# -----------------------------
# Example model (replace with yours)
# -----------------------------
class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]


# -----------------------------
# Config (replace with your get_settings())
# -----------------------------
def get_database_url() -> str:
    # 👉 change this to your real config
    return "sqlite:///./test.db"
    # For Postgres:
    # return "postgresql://user:pass@localhost:5432/dbname"


# -----------------------------
# Helpers
# -----------------------------
def _ensure_sqlite_parent_dir(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return

    raw_path = url.replace("sqlite:///", "", 1).strip()
    if not raw_path:
        return

    db_path = Path(raw_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _to_async_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://")
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///")
    return url


# -----------------------------
# Engine
# -----------------------------
@lru_cache(maxsize=1)
def get_engine(database_url: str | None = None) -> AsyncEngine:
    url = database_url or get_database_url()
    _ensure_sqlite_parent_dir(url)

    async_url = _to_async_url(url)
    is_sqlite = async_url.startswith("sqlite+aiosqlite:///")

    connect_args = {"check_same_thread": False} if is_sqlite else {}

    kwargs = {
        "echo": False,
        "pool_pre_ping": not is_sqlite,
        "connect_args": connect_args,
    }

    if not is_sqlite:
        kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 1800,
        })

    return create_async_engine(async_url, **kwargs)


# -----------------------------
# Session factory
# -----------------------------
@lru_cache(maxsize=1)
def build_session_factory(database_url: str | None = None) -> async_sessionmaker:
    engine = get_engine(database_url)

    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )


SessionLocal = build_session_factory()


# -----------------------------
# Dependency
# -----------------------------
async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


# -----------------------------
# Reset
# -----------------------------
def reset_database_state(database_url: str | None = None) -> None:
    try:
        engine = get_engine(database_url)
        loop = asyncio.get_event_loop()

        if loop.is_running():
            loop.create_task(engine.dispose())
        else:
            loop.run_until_complete(engine.dispose())
    except Exception:
        pass

    build_session_factory.cache_clear()
    get_engine.cache_clear()


# -----------------------------
# Initialize DB
# -----------------------------
async def initialize_database(database_url: str | None = None) -> None:
    engine = get_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# -----------------------------
# FastAPI app
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_database()
    print("✅ DB initialized")
    yield


app = FastAPI(lifespan=lifespan)


# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))
    return {"status": "ok", "db": result.scalar()}


@app.post("/users")
async def create_user(username: str, db: AsyncSession = Depends(get_db)):
    user = UserRecord(username=username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@app.get("/users")
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserRecord))
    return result.scalars().all()