from __future__ import annotations

from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from vinayak.auth.constants import COOKIE_NAME, LEGACY_COOKIE_NAME
from vinayak.auth.service import ADMIN_ROLE, AuthenticatedUser, UserAuthService
from vinayak.db.repositories.user_repository import UserRepository   # ✅ FIX


class WebAuthBackend:
    def __init__(self, session: Session) -> None:
        repo = UserRepository(session)
        self.auth = UserAuthService(repo)

    def login_user(self, username: str, password: str) -> AuthenticatedUser | None:
        return self.auth.authenticate(username, password)

    async def login_admin(self, username: str, password: str) -> AuthenticatedUser | None:
        # ✅ FIX: removed async + await
        user = await self.auth.authenticate(username, password)

        if user is None:
            return None

        if str(user.role).upper() != ADMIN_ROLE:
            return None

        return user

    def build_login_response(self, user: AuthenticatedUser, *, redirect_to: str) -> RedirectResponse:
        response = RedirectResponse(url=redirect_to, status_code=303)
        response.set_cookie(
            key=COOKIE_NAME,
            value=self.auth.create_session_token(user),
            httponly=True,
            samesite='lax',
            secure=False,  # change to True in HTTPS
        )
        return response

    def logout_user(self, token: str | None) -> None:
        self.auth.revoke_session_token(token)

    @staticmethod
    def build_logout_response(*, redirect_to: str) -> RedirectResponse:
        response = RedirectResponse(url=redirect_to, status_code=303)
        response.delete_cookie(COOKIE_NAME)
        response.delete_cookie(LEGACY_COOKIE_NAME)
        return response


__all__ = ['WebAuthBackend']