from __future__ import annotations

"""Shared runtime factories for execution-facing app surfaces."""

from functools import lru_cache

from sqlalchemy.orm import Session

from app.vinayak.infrastructure.cache.redis_client import RedisCache
from app.vinayak.domain.execution.facade import ExecutionFacade
from app.vinayak.domain.execution.guard import ExecutionGuard, InMemoryGuardStateStore, RedisGuardStateStore


@lru_cache(maxsize=1)
def build_execution_guard() -> ExecutionGuard:
    redis_cache = RedisCache.from_env()
    if redis_cache.is_configured():
        return ExecutionGuard(RedisGuardStateStore(redis_cache))
    return ExecutionGuard(InMemoryGuardStateStore())


def build_execution_facade(session: Session) -> ExecutionFacade:
    return ExecutionFacade(session, execution_guard=build_execution_guard())


__all__ = ["build_execution_facade", "build_execution_guard"]
