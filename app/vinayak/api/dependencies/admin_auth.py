from __future__ import annotations

import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Request

from vinayak.auth.service import ADMIN_ROLE, AuthenticatedUser
from vinayak.core.config import get_settings


# =========================
# CONFIG
# =========================

settings = get_settings()

JWT_SECRET = settings.auth.admin_secret
JWT_ALGO = "HS256"
COOKIE_NAME = settings.auth.session_cookie_name or "vinayak_token"
TOKEN_EXP_HOURS = 8


# =========================
# TOKEN CREATION
# =========================

def create_session_token(user: AuthenticatedUser) -> str:
    payload = {
        "user_id": user.id,
        "username": user.username,
        "role": str(user.role).upper(),
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXP_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


# =========================
# USER LOADER
# =========================

def get_current_user(request: Request) -> AuthenticatedUser | None:
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])

        return AuthenticatedUser(
            id=payload.get("user_id"),
            username=payload.get("username"),
            role=payload.get("role"),
            is_active=True,
        )

    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


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