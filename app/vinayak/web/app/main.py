from __future__ import annotations

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from vinayak.api.dependencies.admin_auth import get_current_user, require_admin_session
from vinayak.api.dependencies.db import get_db
from vinayak.auth.constants import COOKIE_NAME
from vinayak.auth.backend import WebAuthBackend
from vinayak.auth.service import ADMIN_ROLE, UserAuthService
from vinayak.db.repositories.deferred_execution_job_repository import DeferredExecutionJobRepository
from vinayak.messaging.outbox import OutboxService
from vinayak.observability.observability_dashboard_spec import build_observability_dashboard_html
from vinayak.web.app.role_pages import (
    render_admin_dashboard_page,
    render_admin_execution_page,
    render_admin_jobs_page,
    render_admin_logs_page,
    render_admin_settings_page,
    render_admin_validation_page,
    render_trade_history_page,
    render_user_home_page,
    render_user_signal_page,
)
from vinayak.web.app.workspace_html import WORKSPACE_DOWNLOADS_HTML, WORKSPACE_HTML, WORKSPACE_REPORTS_HTML
from vinayak.web.services.role_view_service import RoleViewService
from vinayak.api.services.live_analysis_jobs import get_live_analysis_job_service

router = APIRouter()

# ---------------------------
# HELPERS (FIXED MISSING PARTS)
# ---------------------------

def _render_login(error_message: str | None = None, *, form_action: str = '/login') -> HTMLResponse:
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


def _auth_config_error_message(*, admin_only: bool) -> str:
    prefix = "Admin account" if admin_only else "User account"
    return f"{prefix} is not available. Create the account in the database and try again."


def _redirect_for_role(role: str) -> str:
    return "/admin/dashboard" if str(role).upper() == ADMIN_ROLE else "/app"


def _admin_or_login(request: Request) -> bool:
    user = get_current_user(request)
    return user is not None and str(user.role).upper() == ADMIN_ROLE


def _user_or_login(request: Request) -> bool:
    return get_current_user(request) is not None


# ---------------------------
# ROUTES
# ---------------------------

@router.get('/admin/dashboard/data')
def admin_dashboard_data(
    request: Request,
    db: Session = Depends(get_db),
    format: str = Query(default="html"),
):
    if not _admin_or_login(request):
        if format == "json":
            return JSONResponse(status_code=401, content={"detail": "Authentication required."})
        return _render_login('Admin sign in to access the dashboard.', form_action='/admin/login')

    service = RoleViewService(db)
    payload = service.build_admin_dashboard()

    if format == "json":
        return JSONResponse(content=payload)

    return HTMLResponse(render_admin_dashboard_page(payload))


# ---------------------------
# HOME
# ---------------------------

@router.get('/', response_class=HTMLResponse)
def home_page():
    return HTMLResponse("<h1>Vinayak Platform</h1>")


# ---------------------------
# LOGIN
# ---------------------------

@router.get('/login', response_class=HTMLResponse)
def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(_redirect_for_role(user.role), status_code=303)
    return _render_login()


@router.post('/login')
def login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    backend = WebAuthBackend(db)
    user = backend.login_user(username, password)

    if not user:
        return _render_login("Invalid username or password")

    return backend.build_login_response(user, redirect_to=_redirect_for_role(user.role))


@router.post('/logout')
def logout(request: Request, db: Session = Depends(get_db)):
    backend = WebAuthBackend(db)
    backend.logout_user(request.cookies.get(COOKIE_NAME))
    return backend.build_logout_response(redirect_to='/login')


# ---------------------------
# USER PAGES
# ---------------------------

@router.get('/app', response_class=HTMLResponse)
def user_home_page(request: Request, db: Session = Depends(get_db)):
    if not _user_or_login(request):
        return _render_login("Sign in required")

    service = RoleViewService(db)
    return HTMLResponse(render_user_home_page(service.build_user_home()))


@router.get('/app/live-signal', response_class=HTMLResponse)
def user_signal(request: Request, db: Session = Depends(get_db)):
    if not _user_or_login(request):
        return _render_login("Sign in required")

    service = RoleViewService(db)
    return HTMLResponse(render_user_signal_page(service.build_user_signal()))


@router.get('/app/trade-history', response_class=HTMLResponse)
def trade_history(request: Request, db: Session = Depends(get_db)):
    if not _user_or_login(request):
        return _render_login("Sign in required")

    service = RoleViewService(db)
    return HTMLResponse(render_trade_history_page(service.build_user_trade_history()))


# ---------------------------
# ADMIN LOGIN
# ---------------------------

@router.get('/admin/login', response_class=HTMLResponse)
def admin_login_page():
    return _render_login('Admin login required', form_action='/admin/login')


@router.post('/admin/login')
async def admin_login(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    backend = WebAuthBackend(db)

    user = await backend.login_admin(username, password)

    if user is None:
        return _render_login('Invalid username or password.', form_action='/admin/login')

    return backend.build_login_response(user, redirect_to='/admin/dashboard')

@router.post('/admin/logout')
def admin_logout(request: Request, db: Session = Depends(get_db)):
    backend = WebAuthBackend(db)
    backend.logout_user(request.cookies.get(COOKIE_NAME))
    return WebAuthBackend.build_logout_response(redirect_to="/admin")
