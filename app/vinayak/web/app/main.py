from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from vinayak.api.dependencies.admin_auth import get_current_user
from vinayak.api.dependencies.db import get_db
from vinayak.auth.constants import COOKIE_NAME
from vinayak.auth.backend import WebAuthBackend
from vinayak.auth.service import ADMIN_ROLE
from vinayak.web.app.role_pages import (
    render_admin_dashboard_page,
    render_trade_history_page,
    render_user_home_page,
    render_user_signal_page,
)
from vinayak.web.services.role_view_service import RoleViewService

router = APIRouter()
@router.get("/admin")
def admin_root():
    return RedirectResponse(url="/admin/login")

# ---------------------------
# HELPERS
# ---------------------------

def _render_login(error_message: str | None = None, *, form_action: str = "/login") -> HTMLResponse:
    html = f"""
    <html>
    <body>
        <h2>Login</h2>
        <p style="color:red">{error_message or ""}</p>
        <form method="post" action="{form_action}">
            <input name="username" placeholder="username" />
            <input name="password" type="password" placeholder="password" />
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(html)


def _redirect_for_role(role: str) -> str:
    return "/admin/dashboard" if str(role).upper() == ADMIN_ROLE else "/app"


# ---------------------------
# HOME
# ---------------------------

@router.get("/", response_class=HTMLResponse)
def home_page():
    return HTMLResponse("<h1>Vinayak Platform</h1>")


# ---------------------------
# LOGIN (USER)
# ---------------------------

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(_redirect_for_role(user.role), status_code=303)
    return _render_login()


@router.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    backend = WebAuthBackend(db)
    user = backend.login_user(username, password)

    if not user:
        return _render_login("Invalid username or password")

    return backend.build_login_response(
        user,
        redirect_to=_redirect_for_role(user.role),
    )


# ---------------------------
# LOGOUT (USER)
# ---------------------------

@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    backend = WebAuthBackend(db)
    backend.logout_user(request.cookies.get(COOKIE_NAME))
    return backend.build_logout_response(redirect_to="/login")


# ---------------------------
# USER PAGES
# ---------------------------

@router.get("/app", response_class=HTMLResponse)
def user_home_page(request: Request, db: Session = Depends(get_db)):
    if not get_current_user(request):
        return _render_login("Sign in required")

    service = RoleViewService(db)
    return HTMLResponse(render_user_home_page(service.build_user_home()))


@router.get("/app/live-signal", response_class=HTMLResponse)
def user_signal(request: Request, db: Session = Depends(get_db)):
    if not get_current_user(request):
        return _render_login("Sign in required")

    service = RoleViewService(db)
    return HTMLResponse(render_user_signal_page(service.build_user_signal()))


@router.get("/app/trade-history", response_class=HTMLResponse)
def trade_history(request: Request, db: Session = Depends(get_db)):
    if not get_current_user(request):
        return _render_login("Sign in required")

    service = RoleViewService(db)
    return HTMLResponse(render_trade_history_page(service.build_user_trade_history()))


# ---------------------------
# ADMIN LOGIN
# ---------------------------

@router.get("/admin/login", response_class=HTMLResponse)
def admin_login_page():
    return _render_login("Admin login required", form_action="/admin/login")


@router.post("/admin/login")
def admin_login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    backend = WebAuthBackend(db)

    # ✅ FIX: NO await (sync system)
    user = await backend.login_admin(username, password)

    if user is None:
        return _render_login(
            "Invalid username or password.",
            form_action="/admin/login",
        )

    return backend.build_login_response(
        user,
        redirect_to="/admin/dashboard",
    )
# ---------------------------
# ADMIN LOGOUT
# ---------------------------

@router.post("/admin/logout")
def admin_logout(request: Request, db: Session = Depends(get_db)):
    backend = WebAuthBackend(db)

    backend.logout_user(request.cookies.get(COOKIE_NAME))

    return backend.build_logout_response(redirect_to="/admin")
