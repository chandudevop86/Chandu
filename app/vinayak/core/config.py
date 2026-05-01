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
    pass


# ---------------- OBSERVABILITY (FIX) ---------------- #

@dataclass(frozen=True)
class ObservabilitySettings:
    request_id_header: str = "X-Request-ID"
    log_level: str = "INFO"


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


# ---------------- AUTH ---------------- #

@dataclass(frozen=True)
class AuthSettings:
    auto_login_enabled: bool
    sync_admin_from_env: bool
    secure_cookies: bool
    session_cookie_name: str
    legacy_session_cookie_name: str


# ---------------- SQL ---------------- #

@dataclass(frozen=True)
class SqlSettings:
    url: str
    provider: str


# ---------------- APP SETTINGS (FIXED) ---------------- #

@dataclass(frozen=True)
class AppSettings:
    runtime: RuntimeSettings
    auth: AuthSettings
    sql: SqlSettings
    observability: ObservabilitySettings  # ✅ FIX ADDED


# ---------------- HELPERS ---------------- #

def _str_env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or default).strip()


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _bool_env(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() not in {"0", "false", "no", "off"}


def _default_sqlite_url() -> str:
    db_path = Path(__file__).resolve().parents[1] / "data" / "vinayak.db"
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"


def _detect_sql_provider(url: str) -> str:
    url = (url or "").lower()
    if "postgresql" in url:
        return "postgresql"
    if "mysql" in url:
        return "mysql"
    if "sqlite" in url:
        return "sqlite"
    return "unknown"


# ---------------- SETTINGS ---------------- #

@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    if load_dotenv:
        base = Path(__file__).resolve().parents[1]
        env = base / ".env"
        if env.exists():
            load_dotenv(env)

    sql_url = _str_env("VINAYAK_DATABASE_URL", _default_sqlite_url())

    return AppSettings(
        runtime=RuntimeSettings(
            environment=_str_env("APP_ENV", "dev"),
            app_name=_str_env("APP_NAME", "Vinayak"),
            host=_str_env("APP_HOST", "0.0.0.0"),
            port=_int_env("APP_PORT", 8000),
        ),
        auth=AuthSettings(
            auto_login_enabled=_bool_env("VINAYAK_AUTO_LOGIN", False),
            sync_admin_from_env=False,
            secure_cookies=_bool_env("VINAYAK_SECURE_COOKIES", True),
            session_cookie_name="vinayak_session",
            legacy_session_cookie_name="vinayak_admin_session",
        ),
        sql=SqlSettings(
            url=sql_url,
            provider=_detect_sql_provider(sql_url),
        ),
        observability=ObservabilitySettings(),  # ✅ FIX ADDED
    )


def reset_settings_cache():
    get_settings.cache_clear()


def validate_settings():
    s = get_settings()
    if s.runtime.is_production and s.sql.provider == "sqlite":
        raise SettingsValidationError("SQLite not allowed in production")
    return s


def should_auto_initialize_database() -> bool:
    return get_settings().runtime.is_development_like