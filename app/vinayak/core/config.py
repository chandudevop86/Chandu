from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None


class SettingsValidationError(RuntimeError):
    """Raised when runtime configuration is unsafe for startup."""


# ---------------- RUNTIME ---------------- #

@dataclass(frozen=True)
class RuntimeSettings:
    environment: str
    app_name: str
    host: str
    port: int

    @property
    def normalized_environment(self) -> str:
        return self.environment.strip().lower()

    @property
    def is_production(self) -> bool:
        return self.normalized_environment in {"prod", "production"}

    @property
    def is_development_like(self) -> bool:
        return self.normalized_environment in {"local", "dev", "development", "test"}


# ---------------- AUTH (DB ONLY) ---------------- #

@dataclass(frozen=True)
class AuthSettings:
    auto_login_enabled: bool
    sync_admin_from_env: bool
    secure_cookies: bool
    session_cookie_name: str
    legacy_session_cookie_name: str


# ---------------- OTHER SETTINGS ---------------- #

@dataclass(frozen=True)
class SqlSettings:
    url: str
    provider: str


@dataclass(frozen=True)
class AppSettings:
    runtime: RuntimeSettings
    auth: AuthSettings
    sql: SqlSettings


# ---------------- ENV LOADER ---------------- #

def _str_env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or default).strip()


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def _default_sqlite_url() -> str:
    db_path = Path(__file__).resolve().parents[1] / "data" / "vinayak.db"
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"

def _detect_sql_provider(url: str) -> str:
    lower = (url or "").lower()
    if lower.startswith("postgresql"):
        return "postgresql"
    if lower.startswith("mysql"):
        return "mysql"
    if lower.startswith("sqlite"):
        return "sqlite"
    return "unknown"


# ---------------- SETTINGS ---------------- #

@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    if load_dotenv:
        base_dir = Path(__file__).resolve().parents[1]
        env_path = base_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    sql_url = _str_env("VINAYAK_DATABASE_URL", _default_sqlite_url())

    runtime = RuntimeSettings(
        environment=_str_env("APP_ENV", "dev"),
        app_name=_str_env("APP_NAME", "Vinayak Trading Platform"),
        host=_str_env("APP_HOST", "0.0.0.0"),
        port=_int_env("APP_PORT", 8000),
    )

    return AppSettings(
        runtime=runtime,
        auth=AuthSettings(
            auto_login_enabled=_bool_env("VINAYAK_AUTO_LOGIN", False),
            sync_admin_from_env=False,  # ❌ DISABLED (DB ONLY)
            secure_cookies=_bool_env("VINAYAK_SECURE_COOKIES", True),
            session_cookie_name=_str_env("VINAYAK_SESSION_COOKIE_NAME", "vinayak_session"),
            legacy_session_cookie_name=_str_env(
                "VINAYAK_LEGACY_SESSION_COOKIE_NAME",
                "vinayak_admin_session",
            ),
        ),
        sql=SqlSettings(
            url=sql_url,
            provider=_detect_sql_provider(sql_url),
        ),
    )


def reset_settings_cache() -> None:
    get_settings.cache_clear()


# ---------------- VALIDATION (CLEANED) ---------------- #

def validate_settings(*, startup: bool = False) -> AppSettings:
    """
    DB AUTH SYSTEM:
    - NO admin env validation
    - NO secret validation
    - NO startup blocking for admin config
    """
    settings = get_settings()
    errors: list[str] = []

    if settings.runtime.is_production:
        if settings.sql.provider == "sqlite":
            errors.append("Production cannot use SQLite database.")

    if startup and errors:
        raise SettingsValidationError(" ".join(errors))

    return settings
def should_auto_initialize_database() -> bool:
    settings = get_settings()

    # Safe default behavior:
    # auto init only in dev/test, NOT prod
    return settings.runtime.is_development_like