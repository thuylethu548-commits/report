"""Generate the upgraded pixel_floor.html with 12 departments grid (4x3).
Run: python scripts/gen_pixel_floor_v2.py
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'web', 'templates', 'admin', 'pixel_floor.html')

# 12 Department definitions
DEPTS = [
    {
        'key': 'lead_pm', 'num': '01', 'tag': 'ĐIỀU HÀNH & CHIẾN LƯỢC',
        'title': 'Ban Điều Hành PM', 'officer': 'Antigravity Lead PM (Gemini 3.8)',
        'color': '#38bdf8', 'badge_class': 'badge-green', 'default_status': 'RECENT RECORD',
        'bubble': '[RECENT_RECORD] Phân bổ vốn an toàn. Đang theo dõi chỉ số drawdown toàn sàn.',
        'kpi_label': 'Phân bổ vốn:', 'kpi_val': '100% USDT An Toàn',
        'action_url': '/admin/settings', 'action_label': 'CẤU HÌNH SÀN & BOT ↗',
        'sprite': 'sprite_01_pm.png', 'scene': 'dept_01_pm.jpg',
    },
    {
        'key': 'risk_council', 'num': '02', 'tag': 'QUẢN TRỊ RỦI RO',
        'title': 'Hội Đồng Rủi Ro (CRO)', 'officer': 'Agent Rik — Claude-Sonnet-4-6 (Vyce AI)',
        'color': '#ef4444', 'badge_class': 'badge-amber', 'default_status': 'VETO ARMED',
        'bubble': '[VETO_ACTIVE] Phủ quyết mọi lệnh vào cản. Bảo toàn vốn là ưu tiên số 1!',
        'kpi_label': 'Cơ chế bảo vệ:', 'kpi_val': 'AI Veto & Hard SL 1.5%',
        'action_url': '/admin/lessons', 'action_label': 'SỔ TAY BÀI HỌC ↗',
        'sprite': 'sprite_02_risk.png', 'scene': 'dept_02_risk.jpg',
    },
    {
        'key': 'news_scout', 'num': '03', 'tag': 'TRINH SÁT TIN TỨC',
        'title': 'Trinh Sát Tin Tức & NLP', 'officer': 'Agent Hash — GPT-5.6-Terra (9Router)',
        'color': '#06b6d4', 'badge_class': 'badge-green', 'default_status': 'SCANNING',
        'bubble': '[SCANNING] Quét macro sentiment & on-chain data. NLP analysis đang chạy.',
        'kpi_label': 'Tốc độ phản ứng:', 'kpi_val': '< 150ms Telemetry',
        'action_url': '/admin/audit-logs', 'action_label': 'NHẬT KÝ AUDIT ↗',
        'sprite': 'sprite_03_scout.png', 'scene': 'dept_03_scout.jpg',
    },
    {
        'key': 'quant_lab', 'num': '04', 'tag': 'CHIẾN LƯỢC ĐỊNH LƯỢNG',
        'title': 'Phòng Thí Nghiệm Quant', 'officer': 'Agent Palermo — DeepSeek-V4.1 (Vyce AI)',
        'color': '#a855f7', 'badge_class': 'badge-purple', 'default_status': 'ALGO READY',
        'bubble': '[ALGO_ACTIVE] Tín hiệu gần nhất: Multi-TF hợp lưu EMA/RSI/BB đa khung thời gian.',
        'kpi_label': 'Chiến lược:', 'kpi_val': 'EMA_Trend & RSI_Bollinger',
        'action_url': '/admin/quantum', 'action_label': 'QUANTUM COCKPIT ↗',
        'sprite': 'sprite_04_quant.png', 'scene': 'dept_04_quant.jpg',
    },
    {
        'key': 'breakout_hunter', 'num': '05', 'tag': 'SĂN ĐỘT PHÁ',
        'title': 'Đội Săn Breakout', 'officer': 'Agent Tory — Groq Qwen-2.5-27b',
        'color': '#f97316', 'badge_class': 'badge-amber', 'default_status': 'HUNTING',
        'bubble': '[HUNTING] Theo dõi Donchian Surge 20 nến & volume spike breakout.',
        'kpi_label': 'Chiến lược:', 'kpi_val': 'Donchian Surge & Momentum',
        'action_url': '/admin/quantum', 'action_label': 'QUANTUM COCKPIT ↗',
        'sprite': 'sprite_05_execution.png', 'scene': 'dept_05_execution.jpg',
    },
    {
        'key': 'volatility_lab', 'num': '06', 'tag': 'BIẾN ĐỘNG & REGIME',
        'title': 'Phòng Đo Biến Động', 'officer': 'Agent Volt — Gemini-2.0-Flash',
        'color': '#eab308', 'badge_class': 'badge-amber', 'default_status': 'REGIME SCAN',
        'bubble': '[REGIME] Phân loại ADX-14 & đo lường biến động để chỉnh size lệnh tự động.',
        'kpi_label': 'Chỉ số:', 'kpi_val': 'ADX-14 Regime Detection',
        'action_url': '/admin/quantum', 'action_label': 'QUANTUM COCKPIT ↗',
        'sprite': 'sprite_04_quant.png', 'scene': 'dept_04_quant.jpg',
    },
    {
        'key': 'execution_oms', 'num': '07', 'tag': 'THỰC THI & KHỚP LỆNH',
        'title': 'Bộ Phận Khớp Lệnh OMS', 'officer': 'Agent Meme — Cloudflare Llama-3.3',
        'color': '#ec4899', 'badge_class': 'badge-green', 'default_status': 'GUARDIAN ON',
        'bubble': '[TRAILING_ACTIVE] Sẵn sàng dời SL về Break-Even khi lãi +1.0%. Khóa lợi nhuận an toàn.',
        'kpi_label': 'Vị thế & Phí sàn:', 'kpi_val': '0 Vị Thế Mở · Phí Min',
        'action_url': '/admin/trader-demo', 'action_label': 'TRADER DEMO / OMS ↗',
        'sprite': 'sprite_05_execution.png', 'scene': 'dept_05_execution.jpg',
    },
    {
        'key': 'spot_dca', 'num': '08', 'tag': 'SPOT DCA SWING',
        'title': 'Phòng Spot DCA Engine', 'officer': 'AI Spot Sniper — Claude + DeepSeek (Vyce)',
        'color': '#14b8a6', 'badge_class': 'badge-green', 'default_status': 'DCA ACTIVE',
        'bubble': '[SPOT_DCA] AI Spot Sniper giám sát SOL/BTC/ETH. DCA micro-swing +3.5%~+6%.',
        'kpi_label': 'Holding:', 'kpi_val': 'SOL 0.09 · Paper Mode',
        'action_url': '/admin/trader-demo', 'action_label': 'SPOT PORTFOLIO ↗',
        'sprite': 'sprite_06_community.png', 'scene': 'dept_06_community.jpg',
    },
    {
        'key': 'arbitrage_desk', 'num': '09', 'tag': 'CHÊNH LỆCH GIÁ',
        'title': 'Trung Tâm Arbitrage', 'officer': 'Agent Deck — OpenRouter Nemotron-3.5',
        'color': '#8b5cf6', 'badge_class': 'badge-purple', 'default_status': 'SCANNING',
        'bubble': '[ARB_SCAN] Quét chênh lệch funding rate & cross-pair spreads liên tục.',
        'kpi_label': 'Funding Rate:', 'kpi_val': 'Cross-Pair Spread Monitor',
        'action_url': '/admin/quantum', 'action_label': 'QUANT COCKPIT ↗',
        'sprite': 'sprite_04_quant.png', 'scene': 'dept_04_quant.jpg',
    },
    {
        'key': 'accounting_pm', 'num': '10', 'tag': 'KẾ TOÁN & BÀI HỌC',
        'title': 'Phòng Kế Toán & Post-Mortem', 'officer': 'Agent Core — DeepSeek-V4-Flash (Vyce)',
        'color': '#10b981', 'badge_class': 'badge-green', 'default_status': 'LOGGING',
        'bubble': '[POST_MORTEM] Đã tích lũy 19 bài học. Phân tích Sharpe & PnL liên tục.',
        'kpi_label': 'Sharpe Ratio:', 'kpi_val': 'PnL Analytics Engine',
        'action_url': '/admin/performance', 'action_label': 'HIỆU SUẤT & TOKEN ↗',
        'sprite': 'sprite_01_pm.png', 'scene': 'dept_01_pm.jpg',
    },
    {
        'key': 'community_affiliate', 'num': '11', 'tag': 'KHÁCH HÀNG & SQUARE',
        'title': 'Trung Tâm CRM & Square', 'officer': 'GPT-5.6-Luna (9Router)',
        'color': '#3b82f6', 'badge_class': 'badge-green', 'default_status': 'CONNECTED',
        'bubble': '[SQUARE_SYNC] Đã đồng bộ mã giới thiệu Binance GRO_28502_O41DR & bản tin Telegram.',
        'kpi_label': 'Mã Giới Thiệu:', 'kpi_val': 'GRO_28502_O41DR',
        'action_url': '/admin/clients', 'action_label': 'QUẢN LÝ KHÁCH HÀNG ↗',
        'sprite': 'sprite_06_community.png', 'scene': 'dept_06_community.jpg',
    },
    {
        'key': 'cvar_stress', 'num': '12', 'tag': 'KIỂM SOÁT KÝ QUỸ',
        'title': 'Phòng CVaR & Stress Test', 'officer': 'Agent Prof — Groq GPT-OSS-120b',
        'color': '#f43f5e', 'badge_class': 'badge-amber', 'default_status': 'STRESS TEST',
        'bubble': '[CVaR] Stress test margin Futures liên tục. Giám sát liquidation & CVaR 95%.',
        'kpi_label': 'Margin Health:', 'kpi_val': 'CVaR Sentinel Active',
        'action_url': '/admin/performance', 'action_label': 'HIỆU SUẤT ↗',
        'sprite': 'sprite_02_risk.png', 'scene': 'dept_02_risk.jpg',
    },
]

# 7 AI Providers for Model Health panel
PROVIDERS = [
    ('vyce', 'Vyce AI', 'Claude/DeepSeek', '#a855f7'),
    ('groq', 'Groq', 'Llama/Qwen/OSS', '#f97316'),
    ('gemini', 'Gemini', 'Gemini 3.8/2.0', '#38bdf8'),
    ('ninerouter', '9Router', 'GPT-5.6 Terra/Luna', '#10b981'),
    ('cloudflare', 'Cloudflare', 'Llama-3.3', '#eab308'),
    ('openrouter', 'OpenRouter', 'Nemotron/DS', '#8b5cf6'),
    ('etfbit', 'ETFBit', 'GPT-5.6-Sol', '#ec4899'),
]


def gen_dept_card(d):
    """Generate HTML for a single department card."""
    return f'''
        <!-- DEPT {d['num']}: {d['key'].upper()} -->
        <div class="dept-card" id="card-{d['key']}" onclick="openDeptDetailModal('{d['key']}')">
            <div class="dept-card-scene" style="background-image: url('/static/images/dept_scenes/{d['scene']}');"></div>
            <div class="dept-card-overlay"></div>
            <div class="dept-card-content">
                <div class="dept-card-header">
                    <div class="dept-header-left">
                        <div class="dept-sprite-avatar" style="border-color: {d['color']};">
                            <img src="/static/images/sprites/{d['sprite']}" alt="{d['key']}">
                        </div>
                        <div class="dept-info">
                            <span class="dept-tag-id" style="color: {d['color']};">{d['num']} · {d['tag']}</span>
                            <div class="dept-title">{d['title']}</div>
                            <span class="dept-officer">{d['officer']}</span>
                        </div>
                    </div>
                    <span class="dept-status-badge {d['badge_class']}" id="status-{d['key']}">● {d['default_status']}</span>
                </div>

                <div class="dept-thought-bubble" id="bubble-{d['key']}" style="border-color: {d['color']}33;">
                    {d['bubble']}
                </div>

                <div class="dept-kpi-row">
                    <span class="dept-kpi-label">{d['kpi_label']}</span>
                    <span class="dept-kpi-val" style="color: {d['color']};">{d['kpi_val']}</span>
                </div>

                <div class="dept-card-footer">
                    <span style="font-size: 10px; color: #64748b; font-family: 'JetBrains Mono', monospace;">Click để xem chi tiết</span>
                    <a href="{d['action_url']}" class="dept-btn-action" style="border-color: {d['color']}44; color: {d['color']};" onclick="event.stopPropagation()">{d['action_label']}</a>
                </div>
            </div>
        </div>'''


def gen_provider_row(pid, name, models, color):
    return f'''                <div class="model-health-row" id="mh-{pid}">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="mh-dot" style="background: {color}; box-shadow: 0 0 6px {color};"></span>
                        <span style="color: {color}; font-weight: 700;">{name}</span>
                        <span style="color: #64748b; font-size: 10px;">({models})</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="mh-latency" id="mh-lat-{pid}" style="color: #f8fafc; font-weight: 700;">--ms</span>
                        <span class="mh-status" id="mh-st-{pid}" style="color: #10b981;">●</span>
                    </div>
                </div>'''


# Read the existing CSS from original file to preserve styles
EXTRA_CSS = '''<link rel="stylesheet" href="/static/css/pixel_floor.css?v=12.0&t=202609200510">
<style>
/* Scoped enhancements for pixel floor v2 — 12 departments */
.test-btn-group {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}
.btn-alert-test {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    cursor: pointer;
    border: 1px solid;
    transition: all 0.2s ease;
}
.btn-alert-green { background: rgba(16, 185, 129, 0.15); color: #34d399; border-color: #10b981; }
.btn-alert-green:hover { background: #10b981; color: #fff; box-shadow: 0 0 10px rgba(16, 185, 129, 0.5); }
.btn-alert-red { background: rgba(239, 68, 68, 0.15); color: #f87171; border-color: #ef4444; }
.btn-alert-red:hover { background: #ef4444; color: #fff; box-shadow: 0 0 10px rgba(239, 68, 68, 0.5); }
.btn-alert-purple { background: rgba(168, 85, 247, 0.15); color: #c084fc; border-color: #a855f7; }
.btn-alert-purple:hover { background: #a855f7; color: #fff; box-shadow: 0 0 10px rgba(168, 85, 247, 0.5); }
.btn-alert-gold { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: #f59e0b; }
.btn-alert-gold:hover { background: #f59e0b; color: #fff; box-shadow: 0 0 10px rgba(245, 158, 11, 0.5); }

/* 2.5D Isometric Canvas Styles */
.office-stage-container {
    position: relative;
    background: radial-gradient(circle at 50% 35%, #0d1527 0%, #060913 70%, #02040a 100%);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 14px;
    padding: 16px;
    overflow: hidden;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.8), inset 0 0 60px rgba(14, 165, 233, 0.08);
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-bottom: 20px;
}
.office-stage-header {
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 10px; z-index: 10;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 10px;
}
.office-stage-title-wrap { display: flex; align-items: center; gap: 10px; }
.office-stage-badge {
    background: linear-gradient(135deg, #0284c7, #6366f1);
    color: #fff; font-size: 10px; font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    padding: 3px 8px; border-radius: 6px; letter-spacing: 0.5px;
    box-shadow: 0 0 10px rgba(2, 132, 199, 0.5);
}
.office-stage-title {
    font-size: 14px; font-weight: 800; color: #f8fafc;
    letter-spacing: 0.5px; display: flex; align-items: center; gap: 6px;
}
.office-stage-controls { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.btn-office-tool {
    background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(56, 189, 248, 0.3);
    color: #94a3b8; padding: 5px 12px; border-radius: 6px;
    font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace;
    cursor: pointer; transition: all 0.2s ease;
    display: inline-flex; align-items: center; gap: 6px;
}
.btn-office-tool:hover {
    color: #fff; background: rgba(56, 189, 248, 0.25);
    border-color: #38bdf8; box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
}
.btn-office-tool.active {
    background: #0284c7; color: #fff; border-color: #38bdf8;
    box-shadow: 0 0 14px rgba(2, 132, 199, 0.6);
}
.office-viewport {
    position: relative; width: 100%; height: 520px; overflow: hidden;
    border-radius: 10px;
    background: radial-gradient(ellipse at 50% 40%, #0c1427 0%, #050813 65%, #020308 100%);
    border: 1px solid rgba(56, 189, 248, 0.25);
    box-shadow: inset 0 0 60px rgba(0, 0, 0, 0.8), 0 8px 32px rgba(0, 0, 0, 0.6);
    user-select: none; cursor: default;
}
#office-stage-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: block; }
.office-hud-tooltip {
    position: absolute; pointer-events: none; z-index: 50;
    background: rgba(6, 11, 24, 0.94); border: 1px solid #38bdf8;
    border-radius: 8px; padding: 8px 12px; min-width: 190px; max-width: 260px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.85), 0 0 16px rgba(56, 189, 248, 0.35);
    font-family: 'JetBrains Mono', monospace; backdrop-filter: blur(8px);
    transition: opacity 0.15s ease, transform 0.15s ease;
    transform: translate(-50%, -115%);
}
.hud-tooltip-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; gap: 8px; }
.hud-tooltip-badge { font-size: 9px; font-weight: 800; color: #38bdf8; background: rgba(56, 189, 248, 0.15); padding: 2px 6px; border-radius: 4px; letter-spacing: 0.5px; }
.hud-tooltip-status { font-size: 9px; font-weight: 700; color: #10b981; }
.hud-tooltip-title { font-size: 12px; font-weight: 800; color: #f8fafc; margin-bottom: 2px; }
.hud-tooltip-officer { font-size: 9.5px; color: #94a3b8; margin-bottom: 6px; }
.hud-tooltip-metric { font-size: 10px; color: #38bdf8; background: rgba(15, 23, 42, 0.8); padding: 3px 6px; border-radius: 4px; border: 1px solid rgba(255, 255, 255, 0.06); margin-bottom: 4px; }
.hud-tooltip-hint { font-size: 8px; color: #64748b; text-align: right; font-style: italic; }
.office-view-indicator {
    position: absolute; bottom: 12px; right: 14px; pointer-events: none;
    display: flex; align-items: center; gap: 6px;
    background: rgba(2, 6, 23, 0.75); border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 20px; padding: 4px 10px;
    font-size: 9.5px; font-family: 'JetBrains Mono', monospace;
    font-weight: 700; color: #38bdf8; backdrop-filter: blur(4px); z-index: 20;
}
.view-indicator-dot { width: 6px; height: 6px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981; animation: pulse-dot 1.5s infinite; }
.office-event-log-ticker {
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(2, 6, 23, 0.85); border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px; padding: 6px 12px;
    font-size: 11px; font-family: 'JetBrains Mono', monospace; gap: 10px;
}
.event-ticker-tag { color: #a855f7; font-weight: 800; white-space: nowrap; }
.event-ticker-msg { color: #cbd5e1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.event-ticker-stat { color: #10b981; font-weight: 700; white-space: nowrap; }

/* ===== NEW: Model Health & Spot Portfolio Bottom Panels ===== */
.pixel-bottom-duo-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 16px;
}
.model-health-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 5px 8px; background: rgba(15, 23, 42, 0.5); border-radius: 6px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
}
.mh-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.spot-holding-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 8px; background: rgba(15, 23, 42, 0.5); border-radius: 6px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
}

/* ===== 4x3 Grid Upgrade ===== */
.dept-cards-grid {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 14px !important;
}
@media (max-width: 1200px) {
    .dept-cards-grid { grid-template-columns: repeat(3, 1fr) !important; }
}
@media (max-width: 900px) {
    .dept-cards-grid { grid-template-columns: repeat(2, 1fr) !important; }
    .office-viewport { height: 440px; }
    .pixel-bottom-duo-grid { grid-template-columns: 1fr; }
}
@media (max-width: 600px) {
    .dept-cards-grid { grid-template-columns: 1fr !important; }
}
</style>'''


def generate():
    # Build department cards HTML
    dept_cards_html = '\n'.join(gen_dept_card(d) for d in DEPTS)

    # Build provider rows
    provider_rows_html = '\n'.join(gen_provider_row(*p) for p in PROVIDERS)

    html = f'''{{% extends "layouts/admin_base.html" %}}

{{% block extra_css %}}
{EXTRA_CSS}
{{% endblock %}}

{{% block content %}}
<!-- Confetti Celebration Canvas -->
<canvas id="confetti-canvas"></canvas>

<!-- Fixed Real-time Alert Toast Container ("Xanh Đỏ Tím Vàng") -->
<div id="pixel-alert-container"></div>

<div class="pixel-floor-wrapper">

    <!-- 1. TOP LIVE TICKER STRIP -->
    <div class="pixel-ticker-header-bar">
        <div class="ticker-pairs-wrap">
            <div class="ticker-pair-card">
                <span class="ticker-symbol">BTC/USDT</span>
                <span class="ticker-price bullish" id="ticker-BTCUSDT">--</span>
            </div>
            <div class="ticker-pair-card">
                <span class="ticker-symbol">ETH/USDT</span>
                <span class="ticker-price bullish" id="ticker-ETHUSDT">--</span>
            </div>
            <div class="ticker-pair-card">
                <span class="ticker-symbol">SOL/USDT</span>
                <span class="ticker-price bearish" id="ticker-SOLUSDT">--</span>
            </div>
            <div class="ticker-pair-card">
                <span class="ticker-symbol">BNB/USDT</span>
                <span class="ticker-price bullish" id="ticker-BNBUSDT">--</span>
            </div>
        </div>

        <div class="ticker-right-tools">
            <div class="live-badge-glow">
                <span class="live-dot-pulse"></span>
                <span>AUDIT MODE · RECENT RECORD</span>
            </div>
            <div class="clock-display" id="pixel-live-clock">--:--:-- GMT+7</div>
            <div style="font-size: 11px; color: #64748b; font-family: 'JetBrains Mono', monospace;" id="pixel-live-date">--/--/----</div>
        </div>
    </div>

    <!-- 2. HERO BANNER: THIÊN CƠ CÁC V2.0 -->
    <div class="thien-co-hero">
        <div class="thien-co-hero-bg"></div>
        <div class="thien-co-hero-overlay"></div>
        <div class="thien-co-hero-content">
            <div class="hero-branding">
                <div class="hero-seal-badge">天機</div>
                <div class="hero-titles">
                    <h1>THIÊN CƠ CÁC · TRỤ SỞ GIAO DỊCH TỰ ĐỘNG V2.0</h1>
                    <div class="hero-subtitle">
                        <span>Astra Quant Labs</span>
                        <span>·</span>
                        <span style="color: #38bdf8;">Tầng 404 Institutional Floor</span>
                        <span>·</span>
                        <span style="color: #10b981;">172+ Models · 7 Nguồn API</span>
                    </div>
                </div>
            </div>

            <div class="hero-metrics-strip">
                <div class="hero-metric-item">
                    <span class="hero-metric-label">Vốn Bảo Toàn</span>
                    <span class="hero-metric-val" id="hero-bal-val" style="color: #38bdf8;">$--</span>
                </div>
                <div class="hero-metric-item">
                    <span class="hero-metric-label">Tổng PnL</span>
                    <span class="hero-metric-val" id="hero-pnl-val" style="color: #10b981;">--</span>
                </div>
                <div class="hero-metric-item">
                    <span class="hero-metric-label">Tỷ Lệ Veto AI</span>
                    <span class="hero-metric-val" id="hero-veto-val" style="color: #ef4444;">--</span>
                </div>
                <div class="hero-metric-item">
                    <span class="hero-metric-label">Agents Trực Chiến</span>
                    <span class="hero-metric-val" id="hero-agents-val" style="color: #c084fc;">-- / 12 Phòng Ban</span>
                </div>
            </div>
        </div>

        <!-- Real-time Alert Marquee & Controls -->
        <div class="hero-actions-bar">
            <div class="hero-alert-banner">
                <span class="hero-alert-tag" id="hero-alert-tag">⚡ THÔNG BÁO MỚI</span>
                <span class="hero-alert-text" id="hero-alert-text">Hệ thống sẵn sàng: 12 phòng ban đang trực chiến — 172+ AI models từ 7 nguồn API.</span>
            </div>

            <div class="hero-btn-group">
                <button class="btn-cyber" id="btn-toggle-sound" onclick="toggleAudio()">🔊 Âm Thanh: BẬT</button>
                <div class="test-btn-group">
                    <span style="font-size: 10px; color: #64748b; font-family: 'JetBrains Mono', monospace;">Nổ Alert:</span>
                    <button class="btn-alert-test btn-alert-green" onclick="testAlert('green')" title="Test Khớp Lệnh / Lãi">🟢 Xanh</button>
                    <button class="btn-alert-test btn-alert-red" onclick="testAlert('red')" title="Test AI Veto / Cắt Lỗ">🔴 Đỏ</button>
                    <button class="btn-alert-test btn-alert-purple" onclick="testAlert('purple')" title="Test Tín Hiệu Chiến Lược">🟣 Tím</button>
                    <button class="btn-alert-test btn-alert-gold" onclick="testAlert('gold')" title="Test Chốt Lời / Trailing">🟡 Vàng</button>
                </div>
                <button class="btn-cyber btn-cyber-primary" onclick="fetchPixelFloorTelemetry(true)">🔄 Làm Mới</button>
            </div>
        </div>
    </div>

    <!-- 2.5 VIRTUAL OFFICE 2.5D ISOMETRIC STAGE -->
    <div class="office-stage-container" id="office-stage-container">
        <div class="office-stage-header">
            <div class="office-stage-title-wrap">
                <span class="office-stage-badge">LIVE 2.5D ISOMETRIC ENGINE</span>
                <div class="office-stage-title">
                    <span>🏢</span> ASTRA PIXEL TRADING FLOOR · 12 PHÒNG BAN TRỰC CHIẾN
                </div>
            </div>

            <div class="office-stage-controls">
                <button class="btn-office-tool active" id="btn-toggle-view" onclick="toggleOfficeView()">🎮 Chế Độ: 2.5D Isometric</button>
                <button class="btn-office-tool" onclick="triggerOfficeCoffeeBreak()" title="Mô phỏng Agent rời bàn đi pha cafe">☕ Đi Lấy Cafe</button>
                <button class="btn-office-tool" onclick="triggerOfficeElevator()" title="Mô phỏng Thang máy On-chain">🚪 Thang Máy On-Chain</button>
                <button class="btn-office-tool" onclick="simulateSignalHandoff('BUY')" title="Mô phỏng Quant -> Risk -> OMS">⚡ Luồng Tín Hiệu</button>
                <button class="btn-office-tool" onclick="simulateVetoHandoff()" title="Mô phỏng Risk Council phủ quyết">🛡️ Luồng VETO</button>
                <button class="btn-office-tool" onclick="simulateApiError()" title="Mô phỏng lỗi API">⚠️ Lỗi API</button>
                <button class="btn-office-tool" onclick="simulateProfitHandoff()" title="Mô phỏng chốt lời">💰 Chốt Lời ➔ PM</button>
            </div>
        </div>

        <div class="office-viewport" id="office-viewport">
            <canvas id="office-stage-canvas"></canvas>
            <div id="office-hud-tooltip" class="office-hud-tooltip" style="display: none;">
                <div class="hud-tooltip-header">
                    <span class="hud-tooltip-badge" id="hud-badge">01 · PM</span>
                    <span class="hud-tooltip-status" id="hud-status">ONLINE</span>
                </div>
                <div class="hud-tooltip-title" id="hud-title">Ban Điều Hành PM</div>
                <div class="hud-tooltip-officer" id="hud-officer">Antigravity Lead PM (Gemini 3.8)</div>
                <div class="hud-tooltip-metric" id="hud-metric">Phân bổ vốn: 100% USDT</div>
                <div class="hud-tooltip-hint">Nhấp chuột để mở chi tiết phòng ban ↗</div>
            </div>
            <div class="office-view-indicator" id="office-view-indicator">
                <span class="view-indicator-dot"></span>
                <span id="office-view-indicator-text">2.5D ISOMETRIC VIEW · 60 FPS</span>
            </div>
        </div>

        <div class="office-event-log-ticker">
            <span class="event-ticker-tag" id="office-ticker-tag">⚡ LUỒNG CÔNG VIỆC:</span>
            <span class="event-ticker-msg" id="office-ticker-msg">Hệ thống phân tán 12 phòng ban đang hoạt động đồng bộ trên nền tảng 2.5D Isometric Canvas Engine.</span>
            <span class="event-ticker-stat" id="office-ticker-stat">12 / 12 TRỰC CHIẾN</span>
        </div>
    </div>

    <!-- 3. MƯỜI HAI PHÒNG BAN (4×3 GRID CARDS) -->
    <div class="dept-cards-grid">
{dept_cards_html}
    </div>

    <!-- 4. BOTTOM DASHBOARD: 5 MIDDLE KPI CARDS -->
    <div class="pixel-middle-kpi-grid">
        <div class="middle-kpi-card">
            <div class="kpi-icon-square kpi-icon-blue">💼</div>
            <div class="kpi-info-col">
                <div class="kpi-label-text">Số Dư Ký Quỹ (Margin)</div>
                <div class="kpi-value-text" id="kpi-balance-display">$--</div>
                <div class="kpi-sub-text">Bản ghi đã xác minh</div>
            </div>
        </div>

        <div class="middle-kpi-card">
            <div class="kpi-icon-square kpi-icon-green">📦</div>
            <div class="kpi-info-col">
                <div class="kpi-label-text">Vị Thế Đang Mở</div>
                <div class="kpi-value-text" id="kpi-open-pos-display" style="color: #10b981;">0</div>
                <div class="kpi-sub-text">Không có rủi ro trôi nổi</div>
            </div>
        </div>

        <div class="middle-kpi-card">
            <div class="kpi-icon-square kpi-icon-purple">📊</div>
            <div class="kpi-info-col">
                <div class="kpi-label-text">Tổng Lệnh Hôm Nay</div>
                <div class="kpi-value-text" id="kpi-today-trades-display">--</div>
                <div class="kpi-sub-text">Đã qua kiểm định rủi ro</div>
            </div>
        </div>

        <div class="middle-kpi-card">
            <div class="kpi-icon-square kpi-icon-rose">🎯</div>
            <div class="kpi-info-col">
                <div class="kpi-label-text">Win Rate</div>
                <div class="kpi-value-text" style="color: #10b981;" id="kpi-winrate-display">--%</div>
                <div class="kpi-sub-text">Tỷ lệ thắng trung bình</div>
            </div>
        </div>

        <div class="middle-kpi-card">
            <div class="kpi-icon-square kpi-icon-amber">💰</div>
            <div class="kpi-info-col">
                <div class="kpi-label-text">Tổng PnL</div>
                <div class="kpi-value-text" style="color: #10b981;" id="kpi-pnl-display">$--</div>
                <div class="kpi-sub-text">Lợi nhuận ròng tích lũy</div>
            </div>
        </div>
    </div>

    <!-- 5. BOTTOM 3-COLUMN ANALYTICS, TOKEN TELEMETRY & FEED -->
    <div class="pixel-bottom-tri-grid">
        <!-- Col 1: PnL / Win Rate Performance Chart -->
        <div class="tri-card">
            <div class="tri-card-header">
                <div class="tri-card-title">
                    <span>📈</span> HIỆU SUẤT GIAO DỊCH
                </div>
                <div class="chart-tabs-bar">
                    <button class="chart-tab-btn active" onclick="switchChartTab('pnl', this)">PNL</button>
                    <button class="chart-tab-btn" onclick="switchChartTab('winrate', this)">Win Rate</button>
                    <button class="chart-tab-btn" onclick="switchChartTab('orders', this)">Số Lệnh</button>
                    <button class="chart-tab-btn" onclick="switchChartTab('dd', this)">Drawdown</button>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: baseline; font-size: 11px; font-family: 'JetBrains Mono', monospace;">
                <span style="color: #94a3b8;">Trạng thái:</span>
                <span id="chart-sub-pnl" style="color: #10b981; font-weight: 700;">— Lịch sử PnL đã kiểm chứng</span>
            </div>
            <div style="height: 140px; background: rgba(2, 6, 23, 0.6); border-radius: 8px; border: 1px dashed #1e293b; display: flex; align-items: center; justify-content: center; font-family: 'JetBrains Mono', monospace; font-size: 11px; color: #64748b;">
                <div style="text-align: center;">
                    <div style="color: #10b981; font-weight: 800; font-size: 16px;" id="chart-growth-display">--</div>
                    <div style="margin-top: 4px;">Biểu đồ đường PnL đã được đồng bộ với Sổ lệnh OMS</div>
                </div>
            </div>
        </div>

        <!-- Col 2: Token Telemetry & Model Stats (DYNAMIC) -->
        <div class="tri-card">
            <div class="tri-card-header">
                <div class="tri-card-title">
                    <span>⚡</span> TÀI NGUYÊN AI & MODEL (7 NGUỒN)
                </div>
                <span style="font-size: 10px; color: #10b981; font-family: 'JetBrains Mono', monospace;">● BÌNH THƯỜNG</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px;" id="model-health-container">
{provider_rows_html}
            </div>
        </div>

        <!-- Col 3: Real-time Activity Feed (DYNAMIC) -->
        <div class="tri-card">
            <div class="tri-card-header">
                <div class="tri-card-title">
                    <span>📡</span> NHẬT KÝ SỰ KIỆN REALTIME
                </div>
                <span style="font-size: 10px; color: #38bdf8; font-family: 'JetBrains Mono', monospace;">● LIVE FEED</span>
            </div>
            <div class="activity-feed-list" id="pixel-activity-feed">
                <div class="activity-feed-item">
                    <div class="act-time">--:--</div>
                    <div class="act-icon-box" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">📡</div>
                    <div class="act-text">
                        <div class="act-title">Đang tải nhật ký sự kiện...</div>
                        <div class="act-author">Thiên Cơ Các · 12 Phòng Ban</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- 6. SPOT PORTFOLIO & MODEL HEALTH BOTTOM PANELS -->
    <div class="pixel-bottom-duo-grid">
        <!-- Spot Portfolio Panel -->
        <div class="tri-card">
            <div class="tri-card-header">
                <div class="tri-card-title">
                    <span>💎</span> SPOT PORTFOLIO · DCA ENGINE
                </div>
                <span style="font-size: 10px; color: #14b8a6; font-family: 'JetBrains Mono', monospace;" id="spot-mode-badge">● PAPER MODE</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px;" id="spot-portfolio-container">
                <div class="spot-holding-row">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #14b8a6; font-weight: 700;">SOL</span>
                        <span style="color: #94a3b8;">0.09 @ ~\\$110</span>
                    </div>
                    <span style="color: #10b981; font-weight: 700;" id="spot-sol-pnl">+0.03%</span>
                </div>
                <div class="spot-holding-row">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #f97316; font-weight: 700;">BTC</span>
                        <span style="color: #94a3b8;">0.001 LONG (Futures)</span>
                    </div>
                    <span style="color: #10b981; font-weight: 700;" id="spot-btc-pnl">+\\$0.14</span>
                </div>
                <div class="spot-holding-row">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #38bdf8; font-weight: 700;">USDT</span>
                        <span style="color: #94a3b8;">Free Balance</span>
                    </div>
                    <span style="color: #f8fafc; font-weight: 700;" id="spot-usdt-free">\\$4.92</span>
                </div>
            </div>
        </div>

        <!-- Fleet Agent Status Panel -->
        <div class="tri-card">
            <div class="tri-card-header">
                <div class="tri-card-title">
                    <span>🤖</span> FLEET MANAGER · 10 AGENTS
                </div>
                <span style="font-size: 10px; color: #c084fc; font-family: 'JetBrains Mono', monospace;" id="fleet-status-badge">● 10 / 10 ONLINE</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-family: 'JetBrains Mono', monospace; font-size: 10px;" id="fleet-agents-grid">
                <div class="spot-holding-row"><span style="color: #38bdf8;">🎯 Astra</span><span style="color: #10b981;">IDLE</span></div>
                <div class="spot-holding-row"><span style="color: #ef4444;">🛡️ Rik</span><span style="color: #eab308;">BUSY</span></div>
                <div class="spot-holding-row"><span style="color: #06b6d4;">📡 Hash</span><span style="color: #eab308;">BUSY</span></div>
                <div class="spot-holding-row"><span style="color: #a855f7;">📊 Palermo</span><span style="color: #eab308;">BUSY</span></div>
                <div class="spot-holding-row"><span style="color: #f97316;">⚡ Tory</span><span style="color: #eab308;">BUSY</span></div>
                <div class="spot-holding-row"><span style="color: #eab308;">🌊 Volt</span><span style="color: #eab308;">BUSY</span></div>
                <div class="spot-holding-row"><span style="color: #ec4899;">🎯 Meme</span><span style="color: #10b981;">IDLE</span></div>
                <div class="spot-holding-row"><span style="color: #8b5cf6;">💹 Deck</span><span style="color: #10b981;">IDLE</span></div>
                <div class="spot-holding-row"><span style="color: #f43f5e;">🔒 Prof</span><span style="color: #eab308;">BUSY</span></div>
                <div class="spot-holding-row"><span style="color: #10b981;">📋 Core</span><span style="color: #10b981;">IDLE</span></div>
            </div>
        </div>
    </div>

</div>

<!-- Department Detail Modal -->
<div class="pixel-modal-backdrop" id="pixelDeptModal" onclick="closeDeptModal(event)">
    <div class="pixel-modal-box" onclick="event.stopPropagation()">
        <div class="pixel-modal-header">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div id="modal-dept-icon" style="font-size: 28px;">🏢</div>
                <div>
                    <h2 id="modal-dept-title" style="font-size: 16px; font-weight: 800; color: #f8fafc; margin: 0;">Tiêu đề Phòng Ban</h2>
                    <div id="modal-dept-officer" style="font-size: 11px; color: #38bdf8; font-family: 'JetBrains Mono', monospace; margin-top: 2px;">Agent Officer</div>
                </div>
            </div>
            <button class="pixel-modal-close" onclick="closeDeptModal()">✕ ĐÓNG</button>
        </div>

        <div style="display: flex; flex-direction: column; gap: 12px; font-family: 'JetBrains Mono', monospace; font-size: 12px;">
            <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 12px;">
                <span style="color: #64748b; font-size: 10px; text-transform: uppercase;">AI Model & Provider:</span>
                <div id="modal-dept-model" style="color: #a855f7; margin-top: 4px; font-weight: 700;">--</div>
            </div>
            <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 12px;">
                <span style="color: #64748b; font-size: 10px; text-transform: uppercase;">Chức Năng & Quyền Hạn:</span>
                <div id="modal-dept-role" style="color: #e2e8f0; margin-top: 4px; font-weight: 600;">--</div>
            </div>
            <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 12px;">
                <span style="color: #64748b; font-size: 10px; text-transform: uppercase;">Hoạt Động Hiện Tại:</span>
                <div id="modal-dept-activity" style="color: #38bdf8; margin-top: 4px; font-weight: 600;">--</div>
            </div>
            <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 12px;">
                <span style="color: #64748b; font-size: 10px; text-transform: uppercase;">Ý Nghĩ / Speech Bubble:</span>
                <div id="modal-dept-bubble" style="color: #f59e0b; margin-top: 4px; font-style: italic;">--</div>
            </div>
            <div id="modal-dept-extra" style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; display: none;"></div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 10px; border-top: 1px solid #1e293b; padding-top: 12px;">
            <button class="btn-cyber" onclick="closeDeptModal()">Đóng Cửa Sổ</button>
            <button class="btn-cyber btn-cyber-primary" id="modal-action-btn" onclick="executeDeptAction()">THỰC THI NHIỆM VỤ ↗</button>
        </div>
    </div>
</div>
{{% endblock %}}

{{% block scripts %}}
<script src="/static/js/pixel_floor.js?v=12.0&t=202609200510"></script>
{{% endblock %}}
'''
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ Generated {OUTPUT}")
    print(f"   Lines: {len(html.splitlines())}")
    print(f"   Departments: {len(DEPTS)}")
    print(f"   Providers: {len(PROVIDERS)}")


if __name__ == '__main__':
    generate()
