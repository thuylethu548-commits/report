import os
import logging
from typing import Optional, List, Dict, Any
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from data.storage import Database
from risk_engine.circuit_breaker import CircuitBreaker
from core.event_bus import EventBus
from execution.paper_trader import PaperTrader
from data.binance_client import BinanceClient

from web.routes.client_routes import get_client_router
from web.routes.admin_routes import get_admin_router
from web.routes.api_routes import get_api_router
from web.routes.canvas_routes import init_canvas_routes

logger = logging.getLogger("Web")


def create_web_app(
    db: Database,
    circuit_breaker: CircuitBreaker,
    event_bus: Optional[EventBus] = None,
    paper_trader: Optional[PaperTrader] = None,
    binance_client: Optional[BinanceClient] = None,
    audit_logs: Optional[List[Dict[str, Any]]] = None,
    binance_executor: Optional[Any] = None,
    fleet_coordinator: Optional[Any] = None
) -> FastAPI:
    app = FastAPI(title="ASTRA QUANT DESK & CLIENT PORTAL", version="3.0.0")

    # Security Headers & Anti-Abuse Middleware
    @app.middleware("http")
    async def security_headers_middleware(request, call_next):
        # Prevent oversized payload attacks (max 5MB)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 5 * 1024 * 1024:
            from fastapi.responses import JSONResponse
            return JSONResponse({"error": "Payload Too Large (Max 5MB)"}, status_code=413)

        response = await call_next(request)

        # Apply robust security headers
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Content Security Policy (allows self, Google OAuth GIS, Google Fonts, WebSockets)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://accounts.google.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data: https: blob:; "
            "connect-src 'self' https://accounts.google.com wss: ws: https:; "
            "frame-src 'self' https://accounts.google.com;"
        )
        return response

    # Base directory paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, "static")
    templates_dir = os.path.join(base_dir, "templates")

    # Mount static assets
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Setup Jinja2 templates
    templates = Jinja2Templates(directory=templates_dir)

    # In-memory audit logs list
    if audit_logs is None:
        audit_logs = []

    # Include Routers
    client_router = get_client_router(templates, db=db)
    admin_router = get_admin_router(templates, db)
    api_router = get_api_router(db, circuit_breaker, event_bus, paper_trader, binance_client, audit_logs, binance_executor=binance_executor, fleet_coordinator=fleet_coordinator)
    canvas_router = init_canvas_routes(db, templates)

    app.include_router(client_router)
    app.include_router(admin_router)
    app.include_router(api_router)
    app.include_router(canvas_router)

    # Backward-compatible API aliases (e.g., /api/status -> /api/v1/status)
    app.include_router(api_router, prefix="/api")

    logger.info("Web Application Factory initialized with Client Portal, Admin Control Panel & Antigravity 2.0 Canvas.")
    return app
