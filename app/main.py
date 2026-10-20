"""App factory. Use app.asgi:app for uvicorn; tests build their own instance."""
from __future__ import annotations

import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .ai.explainer import Explainer
from .api.routes import router
from .clock import Clock
from .config import BASE_DIR, Settings, load_settings
from .domain.fx import RateTable
from .domain.money import MoneyError
from .domain.providers import load_providers
from .integrations.sandbox_provider import SandboxProviderAdapter
from .persistence.audit import AuditLog
from .persistence.db import Database
from .security.permissions import PermissionDenied
from .security.ratelimit import RateLimited, RateLimiter
from .services import InvalidState, NotFound, Services


def create_app(settings: Settings | None = None, clock: Clock | None = None) -> FastAPI:
    settings = settings or load_settings()
    clock = clock or Clock()
    db = Database(settings.database_path)
    if not db.is_seeded():
        db.seed(json.loads((settings.data_dir / "seed.json").read_text(encoding="utf-8")))
    audit = AuditLog(db, clock)
    services = Services(
        settings=settings, db=db, audit=audit,
        rates=RateTable.from_json(settings.data_dir / "rates.json"),
        providers=load_providers(settings.data_dir / "providers.json"),
        explainer=Explainer(settings), sandbox=SandboxProviderAdapter(), clock=clock,
    )

    app = FastAPI(title="TuitionBridge", version="0.1.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.state.settings = settings
    app.state.services = services
    app.state.rate_limiter = RateLimiter(settings.rate_limit_per_minute, clock)
    app.include_router(router)

    @app.exception_handler(PermissionDenied)
    async def _denied(request: Request, exc: PermissionDenied):
        services.audit.append(actor=exc.principal.key_id, action="PERMISSION_DENIED", tier=int(exc.required),
                              account_id=exc.account_id or exc.principal.account_id, entity_type="request",
                              entity_id=request.url.path, payload={"method": request.method, "reason": str(exc)})
        return JSONResponse(status_code=403, content={"error": {
            "code": "PERMISSION_DENIED", "message": str(exc), "required_tier": int(exc.required),
            "required_tier_name": exc.required.name, "principal_max_tier": int(exc.principal.max_tier)}})

    @app.exception_handler(RateLimited)
    async def _limited(request: Request, exc: RateLimited):
        return JSONResponse(status_code=429, content={"error": {"code": "RATE_LIMITED", "message": str(exc)}})

    @app.exception_handler(MoneyError)
    async def _money(request: Request, exc: MoneyError):
        return JSONResponse(status_code=400, content={"error": {"code": "INVALID_MONEY_INPUT", "message": str(exc)}})

    @app.exception_handler(NotFound)
    async def _notfound(request: Request, exc: NotFound):
        return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": str(exc)}})

    @app.exception_handler(InvalidState)
    async def _state(request: Request, exc: InvalidState):
        return JSONResponse(status_code=409, content={"error": {"code": "INVALID_STATE", "message": str(exc)}})

    frontend = BASE_DIR / "app" / "frontend"
    if frontend.exists():
        app.mount("/", StaticFiles(directory=str(frontend), html=True), name="frontend")
    return app
