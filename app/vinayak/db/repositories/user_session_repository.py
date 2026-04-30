from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from vinayak.db.models.user_session import UserSessionRecord


class UserSessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_session(self, *, user_id: int, token_hash: str, expires_at: datetime) -> UserSessionRecord:
        record = UserSessionRecord(
            user_id=int(user_id),
            token_hash=str(token_hash),
            expires_at=expires_at.astimezone(UTC),
            last_seen_at=datetime.now(UTC),
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_token_hash(self, token_hash: str) -> UserSessionRecord | None:
        return (
            self.session.query(UserSessionRecord)
            .filter(UserSessionRecord.token_hash == str(token_hash))
            .one_or_none()
        )

    def touch(self, record: UserSessionRecord) -> UserSessionRecord:
        record.last_seen_at = datetime.now(UTC)
        self.session.add(record)
        self.session.flush()
        return record

    def revoke(self, record: UserSessionRecord) -> UserSessionRecord:
        record.revoked_at = datetime.now(UTC)
        self.session.add(record)
        self.session.flush()
        return record

