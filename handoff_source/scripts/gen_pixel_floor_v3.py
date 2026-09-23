"""Generate the upgraded Pixel Floor V3.0 template with Pinterest Cyberpunk styling,
4 Campus Wings tab filtering, NPC Persona quotes, and live Adversarial Debate feed.
Run: python scripts/gen_pixel_floor_v3.py
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'web', 'templates', 'admin', 'pixel_floor.html')

# 12 Departments with Wings & NPC details
DEPTS = [
    {
        'key': 'lead_pm', 'num': '01', 'wing': 'executive', 'tag': 'ĐIỀU HÀNH & CHIẾN LƯỢC',
        'title': 'Ban Điều Hành PM', 'officer': 'Antigravity Lead PM (Gemini 3.8)',
        'npc_name': 'Astra', 'npc_mood': '👨‍💼 Thư Thái / Điều Phối', 'npc_mood_color': '#38bdf8',
        'color': '#38bdf8', 'badge_class': 'badge-green', 'default_status': 'RECENT RECORD',
        'model': 'gemini-3.8-flash', 'provider': 'Google Gemini', 'ping': '85ms',
        'quote': 'Điều phối vốn an toàn. Đảm bảo 12 phòng ban phối hợp nhịp nhàng theo kỷ luật.',
        'kpi_label': 'Phân bổ vốn:', 'kpi_val': '100% USDT An Toàn',
        'action_url': '/admin/settings', 'action_label': 'CẤU HÌNH SÀN ↗',
        'sprite': 'sprite_01_pm.png',
    },
    {
        'key': 'risk_council', 'num': '02', 'wing': 'executive', 'tag': 'QUẢN TRỊ RỦI RO',
        'title': 'Hội Đồng Rủi Ro (CRO)', 'officer': 'Agent Rik — Claude-Sonnet-4-6 (Vyce AI)',
        'npc_name': 'Rik (CRO)', 'npc_mood': '🛡️ Phản Biện / Veto', 'npc_mood_color': '#ef4444',
        'color': '#ef4444', 'badge_class': 'badge-amber', 'default_status': 'VETO ARMED',
        'model': 'claude-sonnet-4-6', 'provider': 'Vyce AI', 'ping': '120ms',
        'quote': 'Bảo toàn vốn là số 1! Phủ quyết mọi tín hiệu vào cản hoặc R:R xấu.',
        'kpi_label': 'Cơ chế bảo vệ:', 'kpi_val': 'AI Veto & Hard SL 1.5%',
        'action_url': '/admin/lessons', 'action_label': 'SỔ TAY BÀI HỌC ↗',
        'sprite': 'sprite_02_risk.png',
    },
    {
        'key': 'news_scout', 'num': '03', 'wing': 'operations', 'tag': 'TRINH SÁT TIN TỨC',
        'title': 'Trinh Sát Tin Tức & NLP', 'officer': 'Agent Hash — GPT-5.6-Terra (9Router)',
        'npc_name': 'Hash', 'npc_mood': '📡 Cảnh Báo / Săn Tin', 'npc_mood_color': '#06b6d4',
        'color': '#06b6d4', 'badge_class': 'badge-green', 'default_status': 'SCANNING',
        'model': 'cx/gpt-5.6-terra', 'provider': '9Router', 'ping': '95ms',
        'quote': 'Quét macro sentiment & on-chain ví cá voi liên tục 24/7.',
        'kpi_label': 'Tốc độ phản ứng:', 'kpi_val': '< 150ms Telemetry',
        'action_url': '/admin/audit-logs', 'action_label': 'NHẬT KÝ AUDIT ↗',
        'sprite': 'sprite_03_scout.png',
    },
    {
        'key': 'quant_lab', 'num': '04', 'wing': 'research', 'tag': 'CHIẾN LƯỢC ĐỊNH LƯỢNG',
        'title': 'Phòng Thí Nghiệm Quant', 'officer': 'Agent Palermo — DeepSeek-V4.1 (Vyce AI)',
        'npc_name': 'Palermo', 'npc_mood': '📊 Định Lượng / Tối Ưu', 'npc_mood_color': '#a855f7',
        'color': '#a855f7', 'badge_class': 'badge-purple', 'default_status': 'ALGO READY',
        'model': 'deepseek-v4.1', 'provider': 'Vyce AI', 'ping': '45ms',
        'quote': 'Hội đồng phân kỳ RSI & giao cắt EMA 20/50 khung 15m/1h.',
        'kpi_label': 'Chiến lược:', 'kpi_val': 'EMA_Trend & RSI_Bollinger',
        'action_url': '/admin/quantum', 'action_label': 'QUANT COCKPIT ↗',
        'sprite': 'sprite_04_quant.png',
    },
    {
        'key': 'breakout_hunter', 'num': '05', 'wing': 'research', 'tag': 'SĂN ĐỘT PHÁ',
        'title': 'Đội Săn Breakout', 'officer': 'Agent Tory — Groq Qwen-2.5-27b',
        'npc_name': 'Tory', 'npc_mood': '⚡ Rình Mồi / Breakout', 'npc_mood_color': '#f97316',
        'color': '#f97316', 'badge_class': 'badge-amber', 'default_status': 'HUNTING',
        'model': 'qwen/qwen3.8-27b', 'provider': 'Groq', 'ping': '18ms',
        'quote': 'Donchian 20 nến đang nén chặt, canh breakout volume spike.',
        'kpi_label': 'Chiến lược:', 'kpi_val': 'Donchian Surge & Momentum',
        'action_url': '/admin/quantum', 'action_label': 'QUANT COCKPIT ↗',
        'sprite': 'sprite_05_execution.png',
    },
    {
        'key': 'volatility_lab', 'num': '06', 'wing': 'research', 'tag': 'BIẾN ĐỘNG & REGIME',
        'title': 'Phòng Đo Biến Động', 'officer': 'Agent Volt — Gemini-2.0-Flash',
        'npc_name': 'Volt', 'npc_mood': '🌊 Thận Trọng / Regime', 'npc_mood_color': '#eab308',
        'color': '#eab308', 'badge_class': 'badge-amber', 'default_status': 'REGIME SCAN',
        'model': 'gemini-2.0-flash', 'provider': 'Google Gemini', 'ping': '65ms',
        'quote': 'ADX-14 phân loại chế độ thị trường để tự động tinh chỉnh đòn bẩy.',
        'kpi_label': 'Chỉ số:', 'kpi_val': 'ADX-14 Regime Detection',
        'action_url': '/admin/quantum', 'action_label': 'QUANT COCKPIT ↗',
        'sprite': 'sprite_04_quant.png',
    },
    {
        'key': 'execution_oms', 'num': '07', 'wing': 'trading', 'tag': 'THỰC THI & KHỚP LỆNH',
        'title': 'Bộ Phận Khớp Lệnh OMS', 'officer': 'Agent Meme — Cloudflare Llama-3.3',
        'npc_name': 'Meme', 'npc_mood': '🎯 Trực Chiến / Trailing', 'npc_mood_color': '#ec4899',
        'color': '#ec4899', 'badge_class': 'badge-green', 'default_status': 'GUARDIAN ON',
        'model': '@cf/meta/llama-3.3-70b', 'provider': 'Cloudflare', 'ping': '110ms',
        'quote': 'Sẵn sàng khóa lãi Trailing và dời SL về hòa vốn khi lãi +1.0%.',
        'kpi_label': 'Vị thế & Phí:', 'kpi_val': '0 Vị Thế Mở · Phí Min',
        'action_url': '/admin/trader-demo', 'action_label': 'TRADER DEMO ↗',
        'sprite': 'sprite_05_execution.png',
    },
    {
        'key': 'spot_dca', 'num': '08', 'wing': 'trading', 'tag': 'SPOT DCA SWING',
        'title': 'Phòng Spot DCA Engine', 'officer': 'AI Spot Sniper — Claude + DeepSeek',
        'npc_name': 'Sniper', 'npc_mood': '💎 Điềm Tĩnh / Tích Sản', 'npc_mood_color': '#14b8a6',
        'color': '#14b8a6', 'badge_class': 'badge-green', 'default_status': 'DCA ACTIVE',
        'model': 'claude-sonnet-4-6', 'provider': 'Vyce AI', 'ping': '135ms',
        'quote': 'SOL $110 là vùng hỗ trợ tuần cứng, túc tắc DCA thêm 0.09 SOL.',
        'kpi_label': 'Holding:', 'kpi_val': 'SOL 0.09 · Paper Mode',
        'action_url': '/admin/trader-demo', 'action_label': 'SPOT DESK ↗',
        'sprite': 'sprite_06_community.png',
    },
    {
        'key': 'arbitrage_desk', 'num': '09', 'wing': 'trading', 'tag': 'CHÊNH LỆCH GIÁ',
        'title': 'Trung Tâm Arbitrage', 'officer': 'Agent Deck — OpenRouter Nemotron-3.5',
        'npc_name': 'Deck', 'npc_mood': '💹 Săn Chênh Lệch Giá', 'npc_mood_color': '#8b5cf6',
        'color': '#8b5cf6', 'badge_class': 'badge-purple', 'default_status': 'SCANNING',
        'model': 'nvidia/nemotron-3.5:free', 'provider': 'OpenRouter', 'ping': '210ms',
        'quote': 'Quét funding rate chênh lệch giữa các sàn để ăn yield rủi ro thấp.',
        'kpi_label': 'Funding Rate:', 'kpi_val': 'Cross-Pair Spread Monitor',
        'action_url': '/admin/quantum', 'action_label': 'QUANT COCKPIT ↗',
        'sprite': 'sprite_04_quant.png',
    },
    {
        'key': 'accounting_pm', 'num': '10', 'wing': 'operations', 'tag': 'KẾ TOÁN & BÀI HỌC',
        'title': 'Phòng Kế Toán & Post-Mortem', 'officer': 'Agent Core — DeepSeek-V4-Flash',
        'npc_name': 'Core', 'npc_mood': '📝 Đúc Kết / Sharpe', 'npc_mood_color': '#10b981',
        'color': '#10b981', 'badge_class': 'badge-green', 'default_status': 'LOGGING',
        'model': 'deepseek-v4-flash', 'provider': 'Vyce AI', 'ping': '50ms',
        'quote': 'Đã tích lũy 19 bài học post-mortem. Phân tích Sharpe & PnL liên tục.',
        'kpi_label': 'Sharpe Ratio:', 'kpi_val': 'PnL Analytics Engine',
        'action_url': '/admin/performance', 'action_label': 'HIỆU SUẤT ↗',
        'sprite': 'sprite_01_pm.png',
    },
    {
        'key': 'community_affiliate', 'num': '11', 'wing': 'operations', 'tag': 'KHÁCH HÀNG & SQUARE',
        'title': 'Trung Tâm CRM & Square', 'officer': 'GPT-5.6-Luna (9Router)',
        'npc_name': 'Square Desk', 'npc_mood': '📢 Hào Hứng / Kết Nối', 'npc_mood_color': '#3b82f6',
        'color': '#3b82f6', 'badge_class': 'badge-green', 'default_status': 'CONNECTED',
        'model': 'cx/gpt-5.6-luna', 'provider': '9Router', 'ping': '90ms',
        'quote': 'Đã đồng bộ mã giới thiệu Binance GRO_28502_O41DR & Telegram bot.',
        'kpi_label': 'Mã Giới Thiệu:', 'kpi_val': 'GRO_28502_O41DR',
        'action_url': '/admin/clients', 'action_label': 'CRM CLIENTS ↗',
        'sprite': 'sprite_06_community.png',
    },
    {
        'key': 'cvar_stress', 'num': '12', 'wing': 'operations', 'tag': 'KIỂM SOÁT KÝ QUỸ',
        'title': 'Phòng CVaR & Stress Test', 'officer': 'Agent Prof — Groq GPT-OSS-120b',
        'npc_name': 'Prof', 'npc_mood': '🔒 Gác Cổng Ký Quỹ', 'npc_mood_color': '#f43f5e',
        'color': '#f43f5e', 'badge_class': 'badge-amber', 'default_status': 'STRESS TEST',
        'model': 'openai/gpt-oss-120b', 'provider': 'Groq', 'ping': '22ms',
        'quote': 'Stress test margin Futures liên tục. Giám sát liquidation & CVaR 95%.',
        'kpi_label': 'Margin Health:', 'kpi_val': 'CVaR Sentinel Active',
        'action_url': '/admin/performance', 'action_label': 'HIỆU SUẤT ↗',
        'sprite': 'sprite_02_risk.png',
    },
]

PROVIDERS = [
    ('vyce', 'Vyce AI', 'Claude-4.6 / DS-V4.1', '#a855f7'),
    ('groq', 'Groq', 'Llama-3.3 / Qwen / OSS', '#f97316'),
    ('gemini', 'Google Gemini', 'Gemini 3.8 / 2.0 Flash', '#38bdf8'),
    ('ninerouter', '9Router VPS', 'cx/gpt-5.6 Terra & Luna', '#10b981'),
    ('cloudflare', 'Cloudflare AI', 'Llama-3.3 / DeepSeek R1', '#eab308'),
    ('openrouter', 'OpenRouter', 'Nemotron / 100+ Models', '#8b5cf6'),
    ('etfbit', 'ETFBit Gateway', 'gpt-5.6-sol Supreme', '#ec4899'),
]


def gen_dept_card(d):
    """Generate sleek compact Pinterest-style card with fixed height 240px."""
    return f'''
        <!-- DEPT {d['num']}: {d['key'].upper()} (Wing: {d['wing']}) -->
        <div class="dept-sleek-card" id="card-{d['key']}" data-wing="{d['wing']}" onclick="openDeptDetailModal('{d['key']}')" style="--dept-color: {d['color']};">
            <div class="dept-card-top-row">
                <div class="dept-avatar-badge-wrap">
                    <div class="dept-avatar-box" style="border-color: {d['color']}; box-shadow: 0 0 12px {d['color']}33;">
                        <img src="/static/images/sprites/{d['sprite']}" alt="{d['key']}">
                    </div>
                    <span class="dept-mood-mini-tag" id="mood-badge-{d['key']}" style="color: {d['npc_mood_color']}; border-color: {d['npc_mood_color']}44; background: {d['npc_mood_color']}15;">
                        {d['npc_mood']}
                    </span>
                </div>
                <div class="dept-top-right-meta">
                    <span class="dept-num-tag" style="color: {d['color']};">{d['num']} · {d['tag']}</span>
                    <span class="dept-status-pill {d['badge_class']}" id="status-{d['key']}">● {d['default_status']}</span>
                </div>
            </div>

            <div class="dept-card-main-title">
                <div class="dept-title-text">{d['title']}</div>
                <div class="dept-officer-text">{d['officer']}</div>
            </div>

            <!-- Model pill tag -->
            <div class="dept-model-strip">
                <span class="dept-model-tag" title="Primary AI Model">🤖 {d['model']}</span>
                <span class="dept-provider-tag">{d['provider']}</span>
                <span class="dept-ping-tag" id="ping-{d['key']}" style="color: #10b981;">● {d['ping']}</span>
            </div>

            <!-- Persona Quote Speech Bubble -->
            <div class="dept-quote-bubble" id="bubble-{d['key']}" style="border-left-color: {d['color']};">
                💬 <span class="quote-text-inner" id="quote-{d['key']}">{d['quote']}</span>
            </div>

            <!-- Card Bottom Bar -->
            <div class="dept-card-bottom-bar">
                <div class="dept-kpi-compact">
                    <span class="kpi-c-label">{d['kpi_label']}</span>
                    <span class="kpi-c-val" style="color: {d['color']};">{d['kpi_val']}</span>
                </div>
                <a href="{d['action_url']}" class="dept-btn-sleek" style="border-color: {d['color']}44; color: {d['color']};" onclick="event.stopPropagation()">{d['action_label']}</a>
            </div>
        </div>'''


def gen_provider_row(pid, name, models, color):
    return f'''                <div class="model-health-row" id="mh-{pid}">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="mh-dot" style="background: {color}; box-shadow: 0 0 8px {color};"></span>
                        <span style="color: {color}; font-weight: 700;">{name}</span>
                        <span style="color: #64748b; font-size: 10px;">({models})</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="mh-latency" id="mh-lat-{pid}" style="color: #f8fafc; font-weight: 700;">--ms</span>
                        <span class="mh-status" id="mh-st-{pid}" style="color: #10b981;">● OK</span>
                    </div>
                </div>'''


EXTRA_CSS = '''<link rel="stylesheet" href="/static/css/pixel_floor.css?v=14.0&t=202609200550">
<style>
/* ==========================================================================
   ASTRA QUANT CAMPUS V3.0 — PINTEREST CYBERPUNK STYLING SYSTEM
   ========================================================================== */

/* 1. CAMPUS WINGS TAB BAR */
.campus-wings-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px;
    background: rgba(11, 19, 43, 0.85);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 12px;
    margin-bottom: 18px;
    overflow-x: auto;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.wing-tab-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    background: transparent;
    border: 1px solid transparent;
    color: #94a3b8;
    font-size: 12px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    white-space: nowrap;
}

.wing-tab-btn:hover {
    color: #f8fafc;
    background: rgba(56, 189, 248, 0.12);
    border-color: rgba(56, 189, 248, 0.3);
}

.wing-tab-btn.active {
    background: linear-gradient(135deg, rgba(2, 132, 199, 0.35), rgba(99, 102, 241, 0.35));
    border-color: #38bdf8;
    color: #fff;
    box-shadow: 0 0 16px rgba(56, 189, 248, 0.4);
}

.wing-tab-badge {
    font-size: 9.5px;
    padding: 2px 6px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.1);
    color: #cbd5e1;
}

.wing-tab-btn.active .wing-tab-badge {
    background: #0284c7;
    color: #fff;
}

/* 2. SLEEK COMPACT DEPARTMENT CARDS (Fixed Height 240px, NO Overflows) */
.dept-cards-grid {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 16px !important;
    margin-bottom: 22px;
}

@media (max-width: 1400px) {
    .dept-cards-grid { grid-template-columns: repeat(3, 1fr) !important; }
}
@media (max-width: 960px) {
    .dept-cards-grid { grid-template-columns: repeat(2, 1fr) !important; }
}
@media (max-width: 600px) {
    .dept-cards-grid { grid-template-columns: 1fr !important; }
}

.dept-sleek-card {
    background: radial-gradient(circle at 80% 20%, rgba(15, 23, 42, 0.95), rgba(8, 14, 30, 0.98));
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 240px;
    box-sizing: border-box;
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(8px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.55);
}

.dept-sleek-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--dept-color, #38bdf8);
    opacity: 0.7;
    transition: opacity 0.25s;
}

.dept-sleek-card:hover {
    transform: translateY(-3px);
    border-color: var(--dept-color, #38bdf8);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.7), 0 0 20px rgba(56, 189, 248, 0.2);
}

.dept-sleek-card:hover::before {
    opacity: 1;
    box-shadow: 0 0 10px var(--dept-color, #38bdf8);
}

.dept-card-top-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.dept-avatar-badge-wrap {
    display: flex;
    align-items: center;
    gap: 8px;
}

.dept-avatar-box {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    border: 1.5px solid;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #020617;
    flex-shrink: 0;
}

.dept-avatar-box img {
    width: 32px;
    height: 32px;
    object-fit: cover;
    image-rendering: pixelated;
}

.dept-mood-mini-tag {
    font-size: 9.5px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 7px;
    border-radius: 4px;
    border: 1px solid;
    white-space: nowrap;
}

.dept-top-right-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
}

.dept-num-tag {
    font-size: 9.5px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.5px;
}

.dept-status-pill {
    font-size: 9px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    padding: 1px 6px;
    border-radius: 4px;
}

.dept-card-main-title {
    margin-top: 4px;
}

.dept-title-text {
    font-size: 13.5px;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.01em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.dept-officer-text {
    font-size: 10px;
    color: #94a3b8;
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 1px;
}

.dept-model-strip {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9.5px;
    padding: 3px 6px;
    background: rgba(2, 6, 23, 0.7);
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    overflow: hidden;
}

.dept-model-tag { color: #c084fc; font-weight: 700; white-space: nowrap; }
.dept-provider-tag { color: #64748b; white-space: nowrap; }
.dept-ping-tag { margin-left: auto; font-weight: 700; white-space: nowrap; }

.dept-quote-bubble {
    background: rgba(2, 6, 23, 0.85);
    border-left: 2.5px solid;
    border-radius: 0 6px 6px 0;
    padding: 6px 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    color: #cbd5e1;
    line-height: 1.35;
    height: 38px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    box-sizing: border-box;
}

.dept-card-bottom-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 6px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    gap: 6px;
}

.dept-kpi-compact {
    display: flex;
    flex-direction: column;
}

.kpi-c-label { font-size: 9px; color: #64748b; font-family: 'JetBrains Mono', monospace; }
.kpi-c-val { font-size: 10.5px; font-weight: 700; font-family: 'JetBrains Mono', monospace; white-space: nowrap; }

.dept-btn-sleek {
    font-size: 9.5px;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    padding: 3px 8px;
    border-radius: 5px;
    border: 1px solid;
    background: rgba(15, 23, 42, 0.8);
    text-decoration: none;
    transition: all 0.2s;
    white-space: nowrap;
}

.dept-btn-sleek:hover {
    background: var(--dept-color, #38bdf8);
    color: #fff !important;
    box-shadow: 0 0 10px var(--dept-color, #38bdf8);
}

/* 3. ADVERSARIAL DEBATE REALTIME FEED (Telegram Style) */
.debate-feed-card {
    background: #0b1329;
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 12px;
    padding: 14px;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.6);
}

.debate-item-box {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
    font-family: 'JetBrains Mono', monospace;
    transition: border-color 0.2s;
}

.debate-item-box:hover {
    border-color: rgba(56, 189, 248, 0.35);
}

.debate-header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;
}

.debate-badge-tag {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.3px;
}

.debate-meta-tags {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 9.5px;
    color: #94a3b8;
}

.debate-speech-text {
    font-size: 11px;
    color: #f1f5f9;
    line-height: 1.4;
    margin-top: 3px;
}

/* 4. BOTTOM TWO-COLUMN GRID */
.pixel-bottom-duo-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 18px;
}

@media (max-width: 960px) {
    .pixel-bottom-duo-grid { grid-template-columns: 1fr; }
}

.model-health-row {
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 10px; background: rgba(15, 23, 42, 0.6); border-radius: 6px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
}
.mh-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
</style>'''


def generate():
    dept_cards_html = '\n'.join(gen_dept_card(d) for d in DEPTS)
    provider_rows_html = '\n'.join(gen_provider_row(*p) for p in PROVIDERS)

    html = f'''{{% extends "layouts/admin_base.html" %}}

{{% block extra_css %}}
{EXTRA_CSS}
{{% endblock %}}

{{% block content %}}
<!-- Confetti Celebration Canvas -->
<canvas id="confetti-canvas"></canvas>

<!-- Fixed Real-time Alert Toast Container -->
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

    <!-- 2. HERO BANNER: THIÊN CƠ CÁC V3.0 -->
    <div class="thien-co-hero">
        <div class="thien-co-hero-bg"></div>
        <div class="thien-co-hero-overlay"></div>
        <div class="thien-co-hero-content">
            <div class="hero-branding">
                <div class="hero-seal-badge">天機</div>
                <div class="hero-titles">
                    <h1>THIÊN CƠ CÁC · TRỤ SỞ ASTRA QUANT V3.0</h1>
                    <div class="hero-subtitle">
                        <span>Astra Quant Labs</span>
                        <span>·</span>
                        <span style="color: #38bdf8;">Tầng 404 Institutional Floor</span>
                        <span>·</span>
                        <span style="color: #10b981;">172+ Models · 7 Nguồn API · 4 Phân Khu</span>
                    </div>
                </div>
            </div>

            <div class="hero-metrics-strip">
                <div class="hero-metric-item">
                    <span class="hero-metric-label">Vốn Bảo Toàn</span>
                    <span class="hero-metric-val" id="hero-bal-val" style="color: #38bdf8;">$21.97</span>
                </div>
                <div class="hero-metric-item">
                    <span class="hero-metric-label">Tổng PnL</span>
                    <span class="hero-metric-val" id="hero-pnl-val" style="color: #10b981;">+$0.4556</span>
                </div>
                <div class="hero-metric-item">
                    <span class="hero-metric-label">Tỷ Lệ Veto AI</span>
                    <span class="hero-metric-val" id="hero-veto-val" style="color: #ef4444;">100% An Toàn</span>
                </div>
                <div class="hero-metric-item">
                    <span class="hero-metric-label">Agents Trực Chiến</span>
                    <span class="hero-metric-val" id="hero-agents-val" style="color: #c084fc;">12 / 12 Phòng Ban</span>
                </div>
            </div>
        </div>

        <!-- Real-time Alert Marquee & Controls -->
        <div class="hero-actions-bar">
            <div class="hero-alert-banner">
                <span class="hero-alert-tag" id="hero-alert-tag">⚡ THÔNG BÁO MỚI</span>
                <span class="hero-alert-text" id="hero-alert-text">Hệ thống sẵn sàng: 12 phòng ban phân bổ theo 4 Phân Khu — 172+ AI models trực chiến.</span>
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

    <!-- 3. CAMPUS WINGS TAB BAR (4 PHÂN KHU CÔNG TY) -->
    <div class="campus-wings-bar">
        <button class="wing-tab-btn active" onclick="filterCampusWing('all', this)">
            <span>🏛️</span>
            <span>Tất Cả Phòng Ban</span>
            <span class="wing-tab-badge">12 BAN</span>
        </button>
        <button class="wing-tab-btn" onclick="filterCampusWing('executive', this)">
            <span>👑</span>
            <span>Khu Điều Hành & CRO</span>
            <span class="wing-tab-badge">2 BAN</span>
        </button>
        <button class="wing-tab-btn" onclick="filterCampusWing('trading', this)">
            <span>⚡</span>
            <span>Sàn Giao Dịch & OMS</span>
            <span class="wing-tab-badge">3 BAN</span>
        </button>
        <button class="wing-tab-btn" onclick="filterCampusWing('research', this)">
            <span>🔬</span>
            <span>Viện Quant & Breakout</span>
            <span class="wing-tab-badge">3 BAN</span>
        </button>
        <button class="wing-tab-btn" onclick="filterCampusWing('operations', this)">
            <span>🛡️</span>
            <span>An Toàn & Hậu Cần</span>
            <span class="wing-tab-badge">4 BAN</span>
        </button>
    </div>

    <!-- 4. SÀN 2.5D ISOMETRIC STAGE (4 PHÒNG CHUYÊN BIỆT) -->
    <div class="office-stage-container" id="office-stage-container">
        <div class="office-stage-header">
            <div class="office-stage-title-wrap">
                <span class="office-stage-badge">LIVE 2.5D ISOMETRIC ENGINE</span>
                <div class="office-stage-title">
                    <span>🏢</span> ASTRA PIXEL TRADING FLOOR · TRỤ SỞ 4 PHÂN KHU RIÊNG BIỆT
                </div>
            </div>

            <div class="office-stage-controls">
                <button class="btn-office-tool active" id="btn-toggle-view" onclick="toggleOfficeView()">🎮 Chế Độ: 2.5D Isometric</button>
                <button class="btn-office-tool" onclick="triggerOfficeCoffeeBreak()" title="Agent rời bàn đi pha cafe">☕ Đi Lấy Cafe</button>
                <button class="btn-office-tool" onclick="triggerOfficeElevator()" title="Thang máy On-chain đón dữ liệu">🚪 Thang Máy On-Chain</button>
                <button class="btn-office-tool" onclick="simulateSignalHandoff('BUY')" title="Quant -> Risk -> OMS">⚡ Luồng Tín Hiệu</button>
                <button class="btn-office-tool" onclick="simulateVetoHandoff()" title="Risk Council phủ quyết">🛡️ Luồng VETO</button>
                <button class="btn-office-tool" onclick="simulateApiError()" title="Báo cáo lỗi API">⚠️ Báo Lỗi</button>
                <button class="btn-office-tool" onclick="simulateProfitHandoff()" title="Báo cáo chốt lời về PM">💰 Chốt Lời ➔ PM</button>
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
                <span id="office-view-indicator-text">4 PHÒNG CHUYÊN BIỆT · 60 FPS</span>
            </div>
        </div>

        <div class="office-event-log-ticker">
            <span class="event-ticker-tag" id="office-ticker-tag">⚡ LUỒNG THỰC THI:</span>
            <span class="event-ticker-msg" id="office-ticker-msg">Hệ thống phân tán 12 phòng ban đang hoạt động đồng bộ trên nền tảng 2.5D Isometric Canvas Engine.</span>
            <span class="event-ticker-stat" id="office-ticker-stat">12 / 12 TRỰC CHIẾN</span>
        </div>
    </div>

    <!-- 5. MƯỜI HAI THẺ PHÒNG BAN DẠNG COMPACT SLEEK (PINTEREST CYBERPUNK) -->
    <div class="dept-cards-grid" id="deptCardsGrid">
{dept_cards_html}
    </div>

    <!-- 6. ADVERSARIAL DEBATE REALTIME FEED (TELEGRAM BOT STYLE) -->
    <div class="debate-feed-card" style="margin-bottom: 20px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 16px;">💬</span>
                <span style="font-size: 13px; font-weight: 800; color: #f8fafc; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.5px;">NHẬT KÝ TRANH BIỆN THỰC CHIẾN (ADVERSARIAL DEBATE FEED)</span>
            </div>
            <div style="display: flex; align-items: center; gap: 10px; font-family: 'JetBrains Mono', monospace; font-size: 10px;">
                <span style="color: #10b981;">● TELEGRAM BOT SYNC</span>
                <span style="color: #64748b;">Khung M15/1H</span>
            </div>
        </div>

        <div id="telegram-debate-feed-list">
            <!-- Sample live items from database / Telegram feed -->
            <div class="debate-item-box" style="border-left: 3px solid #ef4444;">
                <div class="debate-header-row">
                    <span class="debate-badge-tag" style="color: #ef4444;">🔴 [AI VETO - PHỦ QUYẾT BẢO TOÀN VỐN]</span>
                    <div class="debate-meta-tags">
                        <span>Cặp: <strong style="color:#38bdf8;">BTC/USDT</strong></span>
                        <span>Rủi ro: <strong style="color:#ef4444;">5/5</strong></span>
                        <span>Tự tin: <strong style="color:#10b981;">95%</strong></span>
                        <span>05:30</span>
                    </div>
                </div>
                <div class="debate-speech-text">
                    <em>"Bear conclusively dismantles this signal. Catastrophic 0.15:1 reward:risk, 75% stop-loss wiping equity, and a 30USD account with no risk management. A 0.23% target cannot justify a 1.5% loss scenario. This is gambling, not trading."</em>
                </div>
            </div>

            <div class="debate-item-box" style="border-left: 3px solid #a855f7;">
                <div class="debate-header-row">
                    <span class="debate-badge-tag" style="color: #a855f7;">🔔 [TÍN HIỆU CHIẾN LƯỢC] RSI_Bollinger</span>
                    <div class="debate-meta-tags">
                        <span>Tài sản: <strong style="color:#38bdf8;">BTC/USDT</strong></span>
                        <span>BUY @ <strong>$81,051.00</strong></span>
                        <span>SL: $79,835 | TP: $81,238</span>
                        <span>05:30</span>
                    </div>
                </div>
                <div class="debate-speech-text">
                    Tín hiệu mua quá bán khung M15 phát sinh tại $81,051.00. Chuyển giao Hội Đồng Rủi Ro thẩm định.
                </div>
            </div>

            <div class="debate-item-box" style="border-left: 3px solid #ef4444;">
                <div class="debate-header-row">
                    <span class="debate-badge-tag" style="color: #ef4444;">🔴 [AI VETO - PHỦ QUYẾT BẢO TOÀN VỐN]</span>
                    <div class="debate-meta-tags">
                        <span>Cặp: <strong style="color:#38bdf8;">1000PEPE/USDT</strong></span>
                        <span>Rủi ro: <strong style="color:#ef4444;">5/5</strong></span>
                        <span>Tự tin: <strong style="color:#10b981;">92%</strong></span>
                        <span>05:15</span>
                    </div>
                </div>
                <div class="debate-speech-text">
                    <em>"Fatal flaws: structure conflict across timeframes, liquidity-hunt wick, stop placement within single-candle kill zone. Memecoin mean-reversion lacks edge; overnight full exposure in weekend void = guaranteed liquidation risk."</em>
                </div>
            </div>
        </div>
    </div>

    <!-- 7. BOTTOM DASHBOARD: 5 MIDDLE KPI CARDS -->
    <div class="pixel-middle-kpi-grid">
        <div class="middle-kpi-card">
            <div class="kpi-icon-square kpi-icon-blue">💼</div>
            <div class="kpi-info-col">
                <div class="kpi-label-text">Số Dư Ký Quỹ (Margin)</div>
                <div class="kpi-value-text" id="kpi-balance-display">$21.97</div>
                <div class="kpi-sub-text">Bản ghi đã xác minh</div>
            </div>
        </div>

        <div class="middle-kpi-card">
            <div class="kpi-icon-square kpi-icon-green">📦</div>
            <div class="kpi-info-col">
                <div class="kpi-label-text">Vị Thế Đang Mở</div>
                <div class="kpi-value-text" id="kpi-open-pos-display" style="color: #10b981;">1 LIVE / 3 PAPER</div>
                <div class="kpi-sub-text">BTC Long 0.001 an toàn</div>
            </div>
        </div>

        <div class="middle-kpi-card">
            <div class="kpi-icon-square kpi-icon-purple">📊</div>
            <div class="kpi-info-col">
                <div class="kpi-label-text">Tổng Lệnh Đã Chạy</div>
                <div class="kpi-value-text" id="kpi-today-trades-display">18</div>
                <div class="kpi-sub-text">Đã qua kiểm định rủi ro</div>
            </div>
        </div>

        <div class="middle-kpi-card">
            <div class="kpi-icon-square kpi-icon-rose">🎯</div>
            <div class="kpi-info-col">
                <div class="kpi-label-text">Win Rate</div>
                <div class="kpi-value-text" style="color: #10b981;" id="kpi-winrate-display">83.3%</div>
                <div class="kpi-sub-text">Tỷ lệ thắng trung bình</div>
            </div>
        </div>

        <div class="middle-kpi-card">
            <div class="kpi-icon-square kpi-icon-amber">💰</div>
            <div class="kpi-info-col">
                <div class="kpi-label-text">Tổng PnL Tích Lũy</div>
                <div class="kpi-value-text" style="color: #10b981;" id="kpi-pnl-display">+$0.4556</div>
                <div class="kpi-sub-text">Lợi nhuận ròng thực tế</div>
            </div>
        </div>
    </div>

    <!-- 8. BOTTOM DUO PANELS: SPOT PORTFOLIO & MODEL HEALTH -->
    <div class="pixel-bottom-duo-grid">
        <!-- Spot Portfolio Panel -->
        <div class="tri-card">
            <div class="tri-card-header">
                <div class="tri-card-title">
                    <span>💎</span> SPOT PORTFOLIO · DCA SWING ENGINE
                </div>
                <span style="font-size: 10px; color: #14b8a6; font-family: 'JetBrains Mono', monospace;" id="spot-mode-badge">● PAPER DCA MODE</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 8px;" id="spot-portfolio-container">
                <div class="model-health-row">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #14b8a6; font-weight: 800;">SOL/USDT</span>
                        <span style="color: #94a3b8; font-size: 10px;">0.09 SOL @ ~$110.50</span>
                    </div>
                    <span style="color: #10b981; font-weight: 700;" id="spot-sol-pnl">+0.03% PnL</span>
                </div>
                <div class="model-health-row">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #f97316; font-weight: 800;">BTC/USDT</span>
                        <span style="color: #94a3b8; font-size: 10px;">0.001 BTC LONG (Futures @ $80,970.10)</span>
                    </div>
                    <span style="color: #10b981; font-weight: 700;" id="spot-btc-pnl">+$0.14 USDT</span>
                </div>
                <div class="model-health-row">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="color: #38bdf8; font-weight: 800;">USDT Free</span>
                        <span style="color: #94a3b8; font-size: 10px;">Số dư khả dụng sàn</span>
                    </div>
                    <span style="color: #f8fafc; font-weight: 700;" id="spot-usdt-free">$4.92 USDT</span>
                </div>
            </div>
        </div>

        <!-- Model Health Panel (7 Nguồn) -->
        <div class="tri-card">
            <div class="tri-card-header">
                <div class="tri-card-title">
                    <span>⚡</span> TÀI NGUYÊN AI & MODEL (7 NGUỒN TRỰC CHIẾN)
                </div>
                <span style="font-size: 10px; color: #10b981; font-family: 'JetBrains Mono', monospace;">● TOÀN BỘ ONLINE</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 6px;" id="model-health-container">
{provider_rows_html}
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
                <span style="color: #64748b; font-size: 10px; text-transform: uppercase;">AI Model & Nhà Cung Cấp:</span>
                <div id="modal-dept-model" style="color: #a855f7; margin-top: 4px; font-weight: 700;">--</div>
            </div>
            <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 12px;">
                <span style="color: #64748b; font-size: 10px; text-transform: uppercase;">Tâm Trạng & Cảm Xúc NPC (Persona):</span>
                <div id="modal-dept-mood" style="color: #38bdf8; margin-top: 4px; font-weight: 700;">--</div>
            </div>
            <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 12px;">
                <span style="color: #64748b; font-size: 10px; text-transform: uppercase;">Lời Thoại Thực Chiến (Speech):</span>
                <div id="modal-dept-bubble" style="color: #f59e0b; margin-top: 4px; font-style: italic; line-height: 1.4;">--</div>
            </div>
            <div style="background: #020617; border: 1px solid #1e293b; border-radius: 8px; padding: 12px;">
                <span style="color: #64748b; font-size: 10px; text-transform: uppercase;">Chức Năng & Quyền Hạn:</span>
                <div id="modal-dept-role" style="color: #e2e8f0; margin-top: 4px; font-weight: 600;">--</div>
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
<script src="/static/js/pixel_floor.js?v=14.0&t=202609200550"></script>
{{% endblock %}}
'''
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ Generated Pixel Floor V3.0 template: {OUTPUT}")
    print(f"   Lines: {len(html.splitlines())}")


if __name__ == '__main__':
    generate()
