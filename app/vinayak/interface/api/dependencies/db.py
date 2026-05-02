from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.vinayak.infrastructure.db.engine import build_session_factory


async def get_db() -> AsyncSession:
    SessionLocal = build_session_factory()

    async with SessionLocal() as session:
        yield session