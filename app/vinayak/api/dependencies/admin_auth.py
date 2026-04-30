from __future__ import annotations

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from vinayak.auth.constants import COOKIE_NAME, LEGACY_COOKIE_NAME
from vinayak.auth.service import ADMIN_ROLE, AuthenticatedUser, UserAuthService
from vinayak.core.config import get_settings
from vinayak.db.session import build_session_factory

# =========================
# CONFIG
# =========================

settings = get_settings()
COOKIE_NAME = settings.auth.session_cookie_name or "vinayak_token"
TOKEN_EXP_HOURS = 8


# =========================
# USER LOADER
# =========================

def get_current_user(request: Request) -> AuthenticatedUser | None:
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        return None

    session_factory = build_session_factory()
    session: Session = session_factory()
    try:
        auth = UserAuthService(session)
        return auth.get_authenticated_user(token)
    except Exception:
        return None
    finally:
        session.close()


# =========================
# HELPERS
# =========================

def is_authenticated(request: Request) -> bool:
    return get_current_user(request) is not None


def require_user_session(request: Request) -> AuthenticatedUser:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


def require_admin_session(request: Request) -> AuthenticatedUser:
    user = require_user_session(request)

    if str(user.role).upper() != ADMIN_ROLE:
        raise HTTPException(status_code=403, detail="Admin authentication required.")

    return user


# =========================
# COOKIE HELPERS
# =========================

def set_auth_cookie(response, token: str):
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=False,   # set True in production HTTPS
        samesite="lax",
    )


def clear_auth_cookie(response):
    response.delete_cookie(COOKIE_NAME)

COOKIE_NAME = settings.auth.session_cookie_name or "vinayak_token"
LEGACY_COOKIE_NAME = settings.auth.legacy_session_cookie_name or "vinayak_admin_session"
