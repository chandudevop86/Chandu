from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from vinayak.db.models.user import UserRecord
from vinayak.db.repositories.user_session_repository import UserSessionRepository
from vinayak.db.repositories.user_repository import UserRepository


ADMIN_ROLE = 'ADMIN'
USER_ROLE = 'USER'
PASSWORD_ITERATIONS = 120000
SESSION_TTL_HOURS = 8


@dataclass(slots=True)
class AuthenticatedUser:
    id: int
    username: str
    role: str
    is_active: bool

    def to_cookie_token(self, secret: str, session_salt: str = '') -> str:
        payload = f'{self.id}:{self.username}:{self.role}:{session_salt}'.encode()
        signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return f'{self.id}:{signature}'


class UserAuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.sessions = UserSessionRepository(session)

    # ---------------- PASSWORD ---------------- #

    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(16)
        derived = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt,
            PASSWORD_ITERATIONS
        )
        return (
            f'pbkdf2_sha256${PASSWORD_ITERATIONS}$'
            f'{base64.urlsafe_b64encode(salt).decode()}$'
            f'{base64.urlsafe_b64encode(derived).decode()}'
        )

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations, salt, digest = password_hash.split('$', 3)

            if algorithm != 'pbkdf2_sha256':
                return False

            actual = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                base64.urlsafe_b64decode(salt),
                int(iterations)
            )

            return hmac.compare_digest(
                actual,
                base64.urlsafe_b64decode(digest)
            )
        except Exception:
            return False

    # ---------------- AUTH ---------------- #

    # def authenticate(self, username: str, password: str) -> AuthenticatedUser | None:
    #     record = await self.users.get_by_username(username)
    #     if not record or not record.is_active:
    #         return None

    #     if not self.verify_password(password, record.password_hash):
    #         return None

    #     return AuthenticatedUser(
    #         id=record.id,
    #         username=record.username,
    #         role=record.role,
    #         is_active=record.is_active
    #     )
from sqlalchemy import select

class UserAuthService:

    async def authenticate(self, username: str, password: str):
        record = await self.users.get_by_username(username)

        if not record:
            return None

        if not self._verify_password(password, record.password_hash):
            return None

        return record



    # ---------------- SESSION ---------------- #

    @staticmethod
    def _hash_session_token(token: str) -> str:
        return hashlib.sha256(str(token or '').encode()).hexdigest()

    def create_session_token(self, user: AuthenticatedUser) -> str:
        record = self.users.get_by_id(user.id)

        if not record or not record.is_active:
            raise ValueError("Invalid user")

        token = secrets.token_urlsafe(32)
        self.sessions.create_session(
            user_id=record.id,
            token_hash=self._hash_session_token(token),
            expires_at=datetime.now(UTC) + timedelta(hours=SESSION_TTL_HOURS),
        )
        self.session.commit()
        return token

    def get_authenticated_user(self, token: str | None) -> AuthenticatedUser | None:
        if not token:
            return None

        session_record = self.sessions.get_by_token_hash(self._hash_session_token(token))
        if session_record is None or session_record.revoked_at is not None:
            return None

        now = datetime.now(UTC)
        if session_record.expires_at <= now:
            return None

        record = self.users.get_by_id(session_record.user_id)
        if not record or not record.is_active:
            return None

        self.sessions.touch(session_record)
        self.session.commit()

        return AuthenticatedUser(
            id=record.id,
            username=record.username,
            role=record.role,
            is_active=record.is_active
        )

    def revoke_session_token(self, token: str | None) -> None:
        if not token:
            return
        session_record = self.sessions.get_by_token_hash(self._hash_session_token(token))
        if session_record is None or session_record.revoked_at is not None:
            return
        self.sessions.revoke(session_record)
        self.session.commit()

    # ---------------- USER MGMT ---------------- #

    def create_user(self, *, username: str, password: str, role: str = USER_ROLE, is_active: bool = True) -> UserRecord:
        username = username.strip()
        role = role.upper()

        if not username:
            raise ValueError("Username required")

        if len(password) < 6:
            raise ValueError("Password too short")

        if role not in {ADMIN_ROLE, USER_ROLE}:
            raise ValueError("Invalid role")

        if self.users.get_by_username(username):
            raise ValueError("User exists")

        record = self.users.create_user(
            username=username,
            password_hash=self.hash_password(password),
            role=role,
            is_active=is_active
        )

        self.session.commit()
        self.session.refresh(record)
        return record
