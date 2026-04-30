from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from vinayak.db.session import Base


class UserSessionRecord(Base):
    __tablename__ = 'user_sessions'
    __table_args__ = (
        Index('idx_user_sessions_token_hash', 'token_hash', unique=True),
        Index('idx_user_sessions_user_active', 'user_id', 'revoked_at', 'expires_at'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

