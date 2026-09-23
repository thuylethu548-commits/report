import hmac
import hashlib
import urllib.parse
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from config.settings import settings
from data.storage import Database

router = APIRouter(prefix="/admin", tags=["Admin Control Panel"])


def get_expected_admin_token() -> str:
    secret = getattr(settings, "ADMIN_SESSION_SECRET", "astra_admin_secret_key_2026").encode()
    return hmac.new(secret, b"astra_authenticated_admin_session", hashlib.sha256).hexdigest()


def is_admin_authenticated(request: Request) -> bool:
    token = request.cookies.get("admin_session_token", "") or request.query_params.get("admin_token", "")
    if not token:
        return False
    expected = get_expected_admin_token()
    return hmac.compare_digest(token, expected)


async def parse_form(request: Request) -> dict:
    body = await request.body()
    decoded = body.decode("utf-8", errors="replace")
    parsed = urllib.parse.parse_qs(decoded)
    return {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}


def get_admin_router(templates: Jinja2Templates, db: Database) -> APIRouter:
    router = APIRouter(prefix="/admin", tags=["Admin Control Panel"])

    # -------------------------------------------------------------------------
    # Authentication Handlers
    # -------------------------------------------------------------------------

    @router.get("/login", response_class=HTMLResponse)
    async def admin_login_page(request: Request, next: str = "/admin"):
        if is_admin_authenticated(request):
            return RedirectResponse(url=next, status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/login.html",
            context={"title": "Đăng Nhập Quản Trị Viên — Astra Control Desk", "error": None, "next_url": next}
        )

    @router.post("/login", response_class=HTMLResponse)
    async def admin_login_submit(request: Request):
        form_data = await parse_form(request)
        password = form_data.get("password", "").strip()
        next_url = form_data.get("next", "/admin").strip() or "/admin"

        expected_password = getattr(settings, "ADMIN_PASSWORD", "AstraAdmin@2026")
        if not hmac.compare_digest(password, expected_password):
            return templates.TemplateResponse(
                request=request,
                name="admin/login.html",
                context={
                    "title": "Đăng Nhập Quản Trị Viên — Astra Control Desk",
                    "error": "Mật khẩu quản trị viên không chính xác!",
                    "next_url": next_url
                }
            )

        resp = RedirectResponse(url=next_url, status_code=303)
        token = get_expected_admin_token()
        resp.set_cookie(key="admin_session_token", value=token, max_age=86400 * 3, httponly=True, samesite="lax")
        return resp

    @router.get("/logout")
    async def admin_logout():
        resp = RedirectResponse(url="/admin/login", status_code=303)
        resp.delete_cookie(key="admin_session_token")
        return resp

    # -------------------------------------------------------------------------
    # Protected Admin Views
    # -------------------------------------------------------------------------

    @router.get("", response_class=HTMLResponse)
    @router.get("/", response_class=HTMLResponse)
    @router.get("/cockpit", response_class=HTMLResponse)
    async def admin_cockpit(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/cockpit.html",
            context={
                "title": "ASTRA CONTROL DESK — Operator Cockpit",
                "current_page": "cockpit",
                "breadcrumb": f"COCKPIT DESK — {settings.SYMBOL} ({settings.TIMEFRAME})"
            }
        )

    @router.get("/quantum", response_class=HTMLResponse)
    async def admin_quantum(request: Request, tab: str = "cockpit"):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/quantum", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/quantum_cockpit.html",
            context={
                "title": "GPTHEIST QUANTUM DESK — 10-Agent Autonomous Terminal",
                "current_page": "quantum",
                "breadcrumb": "QUANTUM COCKPIT (GPTHEIST PROTOCOL)",
                "initial_tab": tab
            }
        )

    @router.get("/trader-demo", response_class=HTMLResponse)
    async def admin_trader_demo(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/trader-demo", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/trader_demo.html",
            context={
                "title": "TRADER DEMO PANEL — Trải Nghiệm Thực Chiến Đa Tác Tử",
                "current_page": "trader_demo",
                "breadcrumb": f"TRADER DEMO DESK — {settings.SYMBOL} ({settings.TIMEFRAME})"
            }
        )

    @router.get("/settings", response_class=HTMLResponse)
    async def admin_settings(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/settings", status_code=303)
        all_settings = await db.get_all_settings()
        settings_dict = {item["key"]: item["value"] for item in all_settings}
        
        view_settings = {
            "TRADING_MODE": settings_dict.get("TRADING_MODE", settings.TRADING_MODE),
            "SYMBOL": settings_dict.get("SYMBOL", settings.SYMBOL),
            "TIMEFRAME": settings_dict.get("TIMEFRAME", settings.TIMEFRAME),
            "DAILY_MAX_DRAWDOWN_PERCENT": float(settings_dict.get("DAILY_MAX_DRAWDOWN_PERCENT", settings.DAILY_MAX_DRAWDOWN_PERCENT)),
            "MAX_ORDER_SIZE_USDT": float(settings_dict.get("MAX_ORDER_SIZE_USDT", 50.0)),
            "ENABLE_AI_ADVISORY": settings_dict.get("ENABLE_AI_ADVISORY", "true").lower() in ("true", "1"),
            "STOP_LOSS_ATR_MULTIPLIER": float(settings_dict.get("STOP_LOSS_ATR_MULTIPLIER", 1.5)),
            "TAKE_PROFIT_ATR_MULTIPLIER": float(settings_dict.get("TAKE_PROFIT_ATR_MULTIPLIER", 3.0)),
            "ENABLE_MULTI_TIMEFRAME": settings_dict.get("ENABLE_MULTI_TIMEFRAME", "true").lower() in ("true", "1") if "ENABLE_MULTI_TIMEFRAME" in settings_dict else settings.ENABLE_MULTI_TIMEFRAME,
            "ENABLE_TELEGRAM": settings_dict.get("ENABLE_TELEGRAM", "false").lower() in ("true", "1") if "ENABLE_TELEGRAM" in settings_dict else settings.ENABLE_TELEGRAM,
            "TELEGRAM_BOT_TOKEN": settings_dict.get("TELEGRAM_BOT_TOKEN", settings.TELEGRAM_BOT_TOKEN),
            "TELEGRAM_CHAT_ID": settings_dict.get("TELEGRAM_CHAT_ID", settings.TELEGRAM_CHAT_ID),
            "AUTO_TRADE_ENABLED": settings_dict.get("AUTO_TRADE_ENABLED", "true").lower() in ("true", "1") if "AUTO_TRADE_ENABLED" in settings_dict else settings.AUTO_TRADE_ENABLED,
            "MARKET_TYPE": settings_dict.get("MARKET_TYPE", getattr(settings, "MARKET_TYPE", "futures")),
            "FUTURES_LEVERAGE": int(settings_dict.get("FUTURES_LEVERAGE", getattr(settings, "FUTURES_LEVERAGE", 3))),
            "LIVE_MAX_USDT_PER_ORDER": float(settings_dict.get("LIVE_MAX_USDT_PER_ORDER", getattr(settings, "LIVE_MAX_USDT_PER_ORDER", 20.0))),
            "COOLDOWN_MINUTES": int(settings_dict.get("COOLDOWN_MINUTES", getattr(settings, "COOLDOWN_MINUTES", 15))),
            "BINANCE_API_KEY": settings_dict.get("BINANCE_API_KEY", settings.BINANCE_API_KEY),
            "BINANCE_API_SECRET": settings_dict.get("BINANCE_API_SECRET", settings.BINANCE_API_SECRET),
        }

        return templates.TemplateResponse(
            request=request,
            name="admin/settings.html",
            context={
                "title": "Cấu Hình Hệ Thống Chung — Astra Desk",
                "current_page": "settings",
                "breadcrumb": "CẤU HÌNH ĐỘNG HỆ THỐNG",
                "settings": view_settings
            }
        )

    @router.get("/trades", response_class=HTMLResponse)
    async def admin_trades_ledger(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/trades", status_code=303)
        trades = await db.get_all_trades_ledger(limit=500)
        analytics = await db.get_trades_analytics()
        return templates.TemplateResponse(
            request=request,
            name="admin/trades_history.html",
            context={
                "title": "Sổ Lệnh & Data Thực Chiến — Astra Desk",
                "current_page": "trades",
                "breadcrumb": "SỔ LỆNH GIAO DỊCH & DATA HỌC TẬP THỰC CHIẾN",
                "trades": trades,
                "analytics": analytics
            }
        )

    @router.get("/trades/{order_id}", response_class=HTMLResponse)
    async def admin_trade_analysis_page(request: Request, order_id: str):
        if not is_admin_authenticated(request):
            return RedirectResponse(url=f"/admin/login?next=/admin/trades/{order_id}", status_code=303)
        trade = await db.get_trade_by_id(order_id)
        if not trade:
            return RedirectResponse(url="/admin/trades", status_code=303)

        leverage = int(getattr(settings, "FUTURES_LEVERAGE", 3))
        ep = float(trade.get("entry_price") or 0.0)
        qty = float(trade.get("quantity") or 0.0)
        margin_usdt = round((ep * qty) / max(leverage, 1), 2)

        current_price = ep
        unrealized_pnl = 0.0
        unrealized_pct = 0.0
        if trade.get("status") == "OPEN":
            async with db._conn.cursor() as cur:
                await cur.execute("SELECT close FROM candles WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", (trade.get("symbol"),))
                candle = await cur.fetchone()
                if candle:
                    current_price = float(candle[0])
            if trade.get("side") == "BUY":
                unrealized_pnl = round((current_price - ep) * qty - float(trade.get("fee") or 0.0), 4)
            else:
                unrealized_pnl = round((ep - current_price) * qty - float(trade.get("fee") or 0.0), 4)
            unrealized_pct = round((unrealized_pnl / max(margin_usdt, 0.01)) * 100, 2)

        golden_audit = await db.get_golden_audit(order_id) if hasattr(db, "get_golden_audit") else None

        return templates.TemplateResponse(
            request=request,
            name="admin/trade_analysis.html",
            context={
                "title": f"Khám Nghiệm Lệnh {trade.get('symbol')} - Astra Desk",
                "current_page": "trades",
                "breadcrumb": f"SỔ LỆNH > KHÁM NGHIỆM CHI TIẾT: {trade.get('symbol')} ({order_id[:10]})",
                "trade": trade,
                "current_price": current_price,
                "margin_usdt": margin_usdt,
                "leverage": leverage,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pct": unrealized_pct,
                "golden_audit": golden_audit
            }
        )

    @router.get("/lessons", response_class=HTMLResponse)
    async def admin_lessons(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/lessons", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/lessons.html",
            context={
                "title": "Sổ Tay Bài Học Xương Máu — Astra Desk",
                "current_page": "lessons",
                "breadcrumb": "SỔ TAY BÀI HỌC XƯƠNG MÁU & QUẢN TRỊ RỦI RO"
            }
        )

    @router.get("/campaign", response_class=HTMLResponse)
    @router.get("/camp", response_class=HTMLResponse)
    async def admin_campaign_page(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/campaign", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/campaign.html",
            context={
                "title": "Chiến Dịch Scale Vốn 500U — Astra Desk",
                "current_page": "campaign",
                "breadcrumb": "CHIẾN DỊCH SCALE VỐN & LỘ TRÌNH 500U (RISK GATES)"
            }
        )

    @router.get("/audit-logs", response_class=HTMLResponse)
    async def admin_audit_logs(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/audit-logs", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/audit_logs.html",
            context={
                "title": "Audit Logs & Tín Hiệu — Astra Desk",
                "current_page": "logs",
                "breadcrumb": "AUDIT LOGS & LỊCH SỬ TÍN HIỆU"
            }
        )

    @router.get("/clients", response_class=HTMLResponse)
    async def admin_clients(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/clients", status_code=303)
        clients = await db.get_all_active_client_credentials()
        summary = await db.get_all_clients_admin_summary()
        affiliate_summary = await db.get_affiliate_summary()
        affiliate_events = await db.get_affiliate_events(limit=20)
        return templates.TemplateResponse(
            request=request,
            name="admin/clients.html",
            context={
                "title": "Quản Trị Khách Hàng & Hoa Hồng — Astra Desk",
                "current_page": "clients",
                "breadcrumb": "QUẢN TRỊ KHÁCH HÀNG & HOA HỒNG SAAS",
                "clients": clients,
                "summary": summary,
                "affiliate_summary": affiliate_summary,
                "affiliate_events": affiliate_events,
                "binance_referral_url": getattr(settings, "BINANCE_REFERRAL_URL", ""),
                "okx_referral_url": getattr(settings, "OKX_REFERRAL_URL", "")
            }
        )

    @router.get("/pixel-floor", response_class=HTMLResponse)
    @router.get("/pixel_floor", response_class=HTMLResponse)
    async def admin_pixel_floor(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/pixel-floor", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/pixel_floor.html",
            context={
                "title": "Phòng Ban Pixel — Astra Quant Trading Floor",
                "current_page": "pixel_floor",
                "breadcrumb": "VĂN PHÒNG ĐỊNH LƯỢNG PIXEL (TRADING FLOOR)"
            }
        )

    @router.get("/mkt-floor", response_class=HTMLResponse)
    @router.get("/mkt_floor", response_class=HTMLResponse)
    async def admin_mkt_floor(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/mkt-floor", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/mkt_floor.html",
            context={
                "title": "Phòng Ban MKT (Tầng Dưới) — Nemark MKT Niver",
                "current_page": "mkt_floor",
                "breadcrumb": "TRỤ SỞ 12 PHÒNG BAN MARKETING & ADS (TẦNG DƯỚI)"
            }
        )

    @router.get("/performance", response_class=HTMLResponse)
    async def admin_performance(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/performance", status_code=303)
        scorecard = await db.get_agent_performance_scorecard()
        return templates.TemplateResponse(
            request=request,
            name="admin/performance.html",
            context={
                "title": "Đánh Giá Hiệu Suất & Tiêu Thụ Token AI — Astra Desk",
                "current_page": "performance",
                "breadcrumb": "ĐÁNH GIÁ HIỆU SUẤT TÁC TỬ & QUẢN TRỊ TOKEN AI",
                "scorecard": scorecard
            }
        )

    @router.get("/ai-orchestration", response_class=HTMLResponse)
    async def admin_ai_orchestration(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/ai-orchestration", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/ai_orchestration.html",
            context={
                "title": "Trung Tâm Điều Phối AI & 7 Nguồn API — Astra Desk",
                "current_page": "ai_orchestration",
                "breadcrumb": "TRUNG TÂM ĐIỀU PHỐI AI & QUẢN TRỊ 7 NGUỒN API"
            }
        )

    @router.get("/workflows", response_class=HTMLResponse)
    async def admin_workflows(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/workflows", status_code=303)
        wfs = await db.get_project_workflows()
        confirmed_count = sum(1 for w in wfs if w.get("status") == "CONFIRMED")
        pending_count = len(wfs) - confirmed_count
        return templates.TemplateResponse(
            request=request,
            name="admin/workflows.html",
            context={
                "title": "Sơ Đồ Kiến Trúc & Luồng Vận Hành Hệ Thống — Astra Desk",
                "current_page": "workflows",
                "breadcrumb": "SƠ ĐỒ KIẾN TRÚC & QUY TRÌNH WORKFLOW HỆ THỐNG",
                "workflows": wfs,
                "total_count": len(wfs),
                "confirmed_count": confirmed_count,
                "pending_count": pending_count
            }
        )

    @router.get("/research", response_class=HTMLResponse)
    async def admin_research_lab(request: Request):
        if not is_admin_authenticated(request):
            return RedirectResponse(url="/admin/login?next=/admin/research", status_code=303)
        return templates.TemplateResponse(
            request=request,
            name="admin/research_lab.html",
            context={
                "title": "Astra Digital Research Lab — Phòng Nghiên Cứu Số Đa Tác Tử",
                "current_page": "research",
                "breadcrumb": "PHÒNG NGHIÊN CỨU SỐ ĐA TÁC TỬ (DIGITAL RESEARCH LAB)"
            }
        )

    return router
