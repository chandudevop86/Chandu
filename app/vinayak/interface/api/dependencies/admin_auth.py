from __future__ import annotations

from fastapi import HTTPException, Request
from vinayak.auth.service import ADMIN_ROLE, AuthenticatedUser, UserAuthService
from vinayak.core.config import get_settings
from app.vinayak.infrastructure.db.engine import build_session_factory

# =========================
# CONFIG
# =========================

settings = get_settings()

COOKIE_NAME = settings.auth.session_cookie_name or "vinayak_token"
LEGACY_COOKIE_NAME = settings.auth.legacy_session_cookie_name or "vinayak_admin_session"

TOKEN_EXP_HOURS = 8


# =========================
# USER LOADER (ASYNC)
# =========================

async def get_current_user(request: Request) -> AuthenticatedUser | None:
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        return None

    try:
        SessionLocal = build_session_factory()

        async with SessionLocal() as session:
            auth = UserAuthService(session)
            return await auth.get_authenticated_user(token)

    except Exception:
        return None


# =========================
# HELPERS (ASYNC)
# =========================

async def is_authenticated(request: Request) -> bool:
    return (await get_current_user(request)) is not None


async def require_user_session(request: Request) -> AuthenticatedUser:
    user = await get_current_user(request)

    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    return user


async def require_admin_session(request: Request) -> AuthenticatedUser:
    user = await require_user_session(request)

    if str(user.role).upper() != ADMIN_ROLE:
        raise HTTPException(status_code=403, detail="Admin authentication required.")

    return user


# =========================
# COOKIE HELPERS
# =========================

def set_auth_cookie(response, token: str):
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # 👉 change to True in production (HTTPS)
        samesite="lax",
    )


def clear_auth_cookie(response):
    response.delete_cookie(COOKIE_NAME)