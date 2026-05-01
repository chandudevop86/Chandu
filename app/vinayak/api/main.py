from fastapi import FastAPI
from fastapi.responses import JSONResponse

from vinayak.api.middleware.request_context import RequestContextMiddleware
from vinayak.api.routes.catalog import router as catalog_router
from vinayak.api.routes.dashboard import router as dashboard_router
from vinayak.api.routes.executions import router as executions_router
from vinayak.api.routes.health import router as health_router
from vinayak.api.routes.outbox import router as outbox_router
from vinayak.api.routes.production import router as production_router
from vinayak.api.routes.reviewed_trades import router as reviewed_trades_router
from vinayak.api.routes.signals import router as signals_router
from vinayak.api.routes.strategies import router as strategies_router
from vinayak.core.config import SettingsValidationError
from vinayak.core.config import should_auto_initialize_database
from vinayak.core.config import validate_settings
from vinayak.db.engine import initialize_database
from vinayak.web.app.main import router as web_router
from vinayak.db.engine import initialize_database

app = FastAPI(title='Vinayak Trading Platform', version='0.2.0')
app.add_middleware(RequestContextMiddleware)

import logging

logger = logging.getLogger(__name__)

@app.on_event("startup")
def startup():
    try:
        validate_settings()
        if should_auto_initialize_database():
            initialize_database()
            print("✅ Database initialized")
        else:
            print("ℹ️ Skipping DB initialization")

    except Exception as e:
        print(f"❌ Startup failed: {e}")

@app.exception_handler(ValueError)
def handle_value_error(_, exc):
    return JSONResponse(status_code=400, content={'error': str(exc)})


@app.exception_handler(SettingsValidationError)
def handle_settings_validation_error(_, exc: SettingsValidationError):
    return JSONResponse(status_code=503, content={'error': str(exc)})


app.include_router(health_router)
app.include_router(signals_router)
app.include_router(reviewed_trades_router)
app.include_router(executions_router)
app.include_router(dashboard_router)
app.include_router(strategies_router)
app.include_router(catalog_router)
app.include_router(outbox_router)
app.include_router(production_router)
app.include_router(web_router)
