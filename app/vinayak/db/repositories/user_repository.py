from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from vinayak.db.models.user import UserRecord

class UserAuthService:
    def __init__(self, users: UserRepository):
        self.users = users
class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_username(self, username: str) -> UserRecord | None:
        stmt = select(UserRecord).where(
            UserRecord.username == username.strip()
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> UserRecord | None:
        result = await self.session.execute(
            select(UserRecord).where(UserRecord.id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_users(self) -> list[UserRecord]:
        result = await self.session.execute(
            select(UserRecord).order_by(
                UserRecord.role.asc(),
                UserRecord.username.asc()
            )
        )
        return list(result.scalars().all())

    async def create_user(
        self,
        *,
        username: str,
        password_hash: str,
        role: str,
        is_active: bool = True
    ) -> UserRecord:

        record = UserRecord(
            username=username.strip(),
            password_hash=password_hash,
            role=role.strip().upper(),
            is_active=is_active,
        )

        self.session.add(record)
        await self.session.flush()
        return record