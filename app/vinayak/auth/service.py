from __future__ import annotations

import base64
import hashlib
import hmac
import os
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from vinayak.db.models.user import UserRecord
from vinayak.db.repositories.user_repository import UserRepository


ADMIN_ROLE = 'ADMIN'
USER_ROLE = 'USER'
PASSWORD_ITERATIONS = 120000

# 🔐 REQUIRED SECRET (NO DEFAULT)
APP_SECRET = os.getenv("APP_SECRET")

if not APP_SECRET or APP_SECRET.lower() in {
    "change-me",
    "replace-me",
    "secret",
    "default",
    "super-secret-key-change-this",
}:
    raise RuntimeError("APP_SECRET must be securely configured")


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

    def authenticate(self, username: str, password: str) -> AuthenticatedUser | None:
        record = self.users.get_by_username(username)

        if not record or not record.is_active:
            return None

        if not self.verify_password(password, record.password_hash):
            return None

        return AuthenticatedUser(
            id=record.id,
            username=record.username,
            role=record.role,
            is_active=record.is_active
        )

    # ---------------- SESSION ---------------- #

    def create_session_token(self, user: AuthenticatedUser) -> str:
        record = self.users.get_by_id(user.id)

        if not record or not record.is_active:
            raise ValueError("Invalid user")

        return user.to_cookie_token(
            APP_SECRET,
            session_salt=record.password_hash
        )

    def get_authenticated_user(self, token: str | None) -> AuthenticatedUser | None:
        if not token or ':' not in token:
            return None

        user_id_raw, _ = token.split(':', 1)

        try:
            user_id = int(user_id_raw)
        except ValueError:
            return None

        record = self.users.get_by_id(user_id)

        if not record or not record.is_active:
            return None

        expected = AuthenticatedUser(
            id=record.id,
            username=record.username,
            role=record.role,
            is_active=record.is_active
        ).to_cookie_token(APP_SECRET, session_salt=record.password_hash)

        if not hmac.compare_digest(token, expected):
            return None

        return AuthenticatedUser(
            id=record.id,
            username=record.username,
            role=record.role,
            is_active=record.is_active
        )

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