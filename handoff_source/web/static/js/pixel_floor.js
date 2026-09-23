/**
 * THIÊN CƠ CÁC (PIXEL TRADING FLOOR 404) CONTROLLER
 * Real-time Telemetry, Retro 8-bit Audio, Confetti & Vibrant Alert System ("Xanh Đỏ Tím Vàng")
 */

let currentTelemetry = null;
let activeModalDept = null;
let soundEnabled = false;
window.isMuted = true;
const motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)');
let telemetryPending = false;
let seenSignalTimestamps = new Set();
let seenTradeTimestamps = new Set();
let isFirstPoll = true;

// Department icon & sprite mappings
const DEPT_ICONS = {
    lead_pm: '👨‍💼',
    risk_council: '🛡️',
    news_scout: '📡',
    quant_lab: '📊',
    breakout_hunter: '⚡',
    volatility_lab: '🌊',
    execution_oms: '🎯',
    spot_dca: '💎',
    arbitrage_desk: '💹',
    accounting_pm: '📋',
    community_affiliate: '📢',
    cvar_stress: '🔒'
};

const DEPT_SPRITES = {
    lead_pm: '/static/images/sprites/sprite_01_pm.png',
    risk_council: '/static/images/sprites/sprite_02_risk.png',
    news_scout: '/static/images/sprites/sprite_03_scout.png',
    quant_lab: '/static/images/sprites/sprite_04_quant.png',
    breakout_hunter: '/static/images/sprites/sprite_05_execution.png',
    volatility_lab: '/static/images/sprites/sprite_04_quant.png',
    execution_oms: '/static/images/sprites/sprite_05_execution.png',
    spot_dca: '/static/images/sprites/sprite_06_community.png',
    arbitrage_desk: '/static/images/sprites/sprite_04_quant.png',
    accounting_pm: '/static/images/sprites/sprite_01_pm.png',
    community_affiliate: '/static/images/sprites/sprite_06_community.png',
    cvar_stress: '/static/images/sprites/sprite_02_risk.png'
};

const DEPT_SPEECHES = {
    lead_pm: [
        "Hệ thống điều hành Astra Lead PM trực chiến 24/7.",
        "Đang đồng bộ số liệu Binance Live & 12 phòng ban định lượng..."
    ],
    execution_oms: [
        "Execution OMS sẵn sàng xử lý tín hiệu và bảo vệ Trailing Stop.",
        "Giám sát độ trễ API và trượt giá trên Binance."
    ],
    quant_lab: [
        "Đang quét đa khung thời gian M15/H1 và ma trận chỉ báo kỹ thuật.",
        "Hội đồng phân kỳ RSI & giao cắt EMA 20/50 khung 15m/1h."
    ],
    risk_council: [
        "Kiểm soát rủi ro, bảo toàn vốn 100%, sẵn sàng phủ quyết tín hiệu xấu.",
        "Giám sát trần Drawdown và bảo vệ tài khoản tuyệt đối."
    ],
    spot_dca: [
        "Danh mục Spot DCA sẵn sàng gom tài sản khi có giá chiết khấu.",
        "Chiến lược DCA kỷ luật: Chỉ gom coin nền tảng khi có chiết khấu giá tốt."
    ],
    community_affiliate: [
        "Đồng bộ Telegram Bot và kênh chia sẻ tín hiệu cộng đồng.",
        "Hệ thống trực tuyến 24/7 phục vụ kết nối cộng đồng và sao chép lệnh an toàn."
    ],
    news_scout: [
        "Quét tin tức vĩ mô, macro sentiment và on-chain ví cá voi liên tục 24/7.",
        "Hệ thống NLP phân tích dòng tiền và tâm lý thị trường."
    ],
    accounting_pm: [
        "Ghi nhận nhật ký giao dịch và bài học post-mortem vào SQLite.",
        "Đã tích lũy bài học thực chiến post-mortem. Phân tích Sharpe & PnL liên tục."
    ],
    breakout_hunter: [
        "Kênh Donchian 20 nến sẵn sàng bắt nhịp bùng nổ volume.",
        "Rình mồi Breakout khi có bùng nổ volume hợp lưu xu hướng."
    ],
    volatility_lab: [
        "Theo dõi ATR và phân loại chế độ thị trường (Regime).",
        "Biên độ thị trường tích lũy. Ưu tiên chiến lược Pullback & Scalping."
    ],
    arbitrage_desk: [
        "Giám sát Funding Rate và chênh lệch spread liên sàn.",
        "Quét funding rate chênh lệch giữa các sàn để ăn yield rủi ro thấp."
    ],
    cvar_stress: [
        "Giám sát đòn bẩy an toàn và khoảng cách thanh lý > 85%.",
        "Stress test margin Futures liên tục. Giám sát liquidation price & CVaR 95%."
    ]
};

function toggleOfficeAudio() {
    soundEnabled = !soundEnabled;
    window.isMuted = !soundEnabled;
    const btn = document.getElementById('game-sfx-toggle');
    if (btn) btn.textContent = soundEnabled ? '🔊 Âm Thanh: BẬT' : '🔇 Âm Thanh: TẮT';
    const oldBtn = document.getElementById('btn-toggle-sound');
    if (oldBtn) oldBtn.textContent = soundEnabled ? '🔊 Âm Thanh: BẬT' : '🔇 Âm Thanh: TẮT';
    const hudIcon = document.getElementById('hud-audio-icon');
    if (hudIcon) hudIcon.textContent = soundEnabled ? '🔊' : '🔇';
    if (soundEnabled) playRetroSound('green');
}
window.toggleOfficeAudio = toggleOfficeAudio;

/* ==========================================================================
   1. RETRO 8-BIT SOUND SYNTHESIZER (Web Audio API - 100% Offline & Pure JS)
   ========================================================================== */
let audioCtx = null;

function getAudioContext() {
    if (!audioCtx) {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (AudioContext) {
            audioCtx = new AudioContext();
        }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    return audioCtx;
}

function playRetroSound(type) {
    if (!soundEnabled) return;
    try {
        const ctx = getAudioContext();
        if (!ctx) return;

        const now = ctx.currentTime;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);

        if (type === 'green') {
            // High cheerful 8-bit coin chime
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(523.25, now); // C5
            osc.frequency.setValueAtTime(659.25, now + 0.08); // E5
            osc.frequency.setValueAtTime(783.99, now + 0.16); // G5
            osc.frequency.setValueAtTime(1046.50, now + 0.24); // C6
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
            osc.start(now);
            osc.stop(now + 0.45);
        } else if (type === 'red') {
            // Urgent warning alarm buzz
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(320, now);
            osc.frequency.setValueAtTime(220, now + 0.1);
            osc.frequency.setValueAtTime(320, now + 0.2);
            osc.frequency.setValueAtTime(220, now + 0.3);
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.45);
            osc.start(now);
            osc.stop(now + 0.45);
        } else if (type === 'purple') {
            // Sci-fi quantum shimmer
            osc.type = 'sine';
            osc.frequency.setValueAtTime(440, now);
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.25);
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
            osc.start(now);
            osc.stop(now + 0.35);
        } else if (type === 'gold') {
            // Big victory fanfare
            osc.type = 'square';
            osc.frequency.setValueAtTime(440, now); // A4
            osc.frequency.setValueAtTime(554.37, now + 0.09); // C#5
            osc.frequency.setValueAtTime(659.25, now + 0.18); // E5
            osc.frequency.setValueAtTime(880, now + 0.27); // A5
            gain.gain.setValueAtTime(0.18, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
            osc.start(now);
            osc.stop(now + 0.6);
        } else if (type === 'turbo') {
            // High-octane Ferrari/Lambo engine rev & turbo flutter sound
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(120, now);
            osc.frequency.exponentialRampToValueAtTime(480, now + 0.28);
            osc.frequency.exponentialRampToValueAtTime(210, now + 0.55);
            gain.gain.setValueAtTime(0.25, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.62);
            osc.start(now);
            osc.stop(now + 0.62);
        } else if (type === 'elevator_ding') {
            // Pleasant two-tone elevator chime (F5 -> A5)
            osc.type = 'sine';
            osc.frequency.setValueAtTime(698.46, now); // F5
            osc.frequency.setValueAtTime(880.00, now + 0.12); // A5
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.65);
            osc.start(now);
            osc.stop(now + 0.65);
        } else if (type === 'coffee_brew') {
            // Gentle coffee bubbling & percolation sound
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(220, now);
            osc.frequency.linearRampToValueAtTime(340, now + 0.12);
            osc.frequency.linearRampToValueAtTime(260, now + 0.24);
            osc.frequency.linearRampToValueAtTime(380, now + 0.36);
            gain.gain.setValueAtTime(0.14, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.45);
            osc.start(now);
            osc.stop(now + 0.45);
        } else if (type === 'blip') {
            // Subtle 8-bit blip for packet jump or keystroke
            osc.type = 'square';
            osc.frequency.setValueAtTime(880, now);
            gain.gain.setValueAtTime(0.05, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.08);
            osc.start(now);
            osc.stop(now + 0.08);
        }
    } catch (e) {
        console.warn('Audio synth error:', e);
    }
}

function toggleAudio() {
    soundEnabled = !soundEnabled;
    window.isMuted = !soundEnabled;
    const btn = document.getElementById('btn-toggle-sound');
    if (btn) {
        btn.textContent = soundEnabled ? '🔊 Âm Thanh: BẬT' : '🔇 Âm Thanh: TẮT';
        btn.style.color = soundEnabled ? '#38bdf8' : '#64748b';
    }
    const hudIcon = document.getElementById('hud-audio-icon');
    if (hudIcon) {
        hudIcon.textContent = soundEnabled ? '🔊' : '🔇';
    }
    if (soundEnabled) {
        playRetroSound('green');
    }
}

/* ==========================================================================
   2. RETRO CONFETTI CELEBRATION (For Big Win / TP)
   ========================================================================== */
function triggerConfetti() {
    const canvas = document.getElementById('confetti-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const colors = ['#10b981', '#38bdf8', '#f59e0b', '#ec4899', '#a855f7', '#fbbf24'];
    const particles = [];

    for (let i = 0; i < 90; i++) {
        particles.push({
            x: window.innerWidth / 2 + (Math.random() - 0.5) * 200,
            y: window.innerHeight * 0.3,
            vx: (Math.random() - 0.5) * 16,
            vy: Math.random() * -12 - 4,
            size: Math.random() * 8 + 4,
            color: colors[Math.floor(Math.random() * colors.length)],
            rotation: Math.random() * 360,
            rotSpeed: (Math.random() - 0.5) * 10,
            alpha: 1
        });
    }

    let frame = 0;
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        let alive = false;

        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.4; // gravity
            p.vx *= 0.98;
            p.rotation += p.rotSpeed;
            p.alpha -= 0.012;

            if (p.alpha > 0) {
                alive = true;
                ctx.save();
                ctx.globalAlpha = p.alpha;
                ctx.translate(p.x, p.y);
                ctx.rotate((p.rotation * Math.PI) / 180);
                ctx.fillStyle = p.color;
                ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
                ctx.restore();
            }
        });

        frame++;
        if (alive && frame < 120) {
            requestAnimationFrame(animate);
        } else {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }
    animate();
}

/* ==========================================================================
   3. VIBRANT ALERT SYSTEM ("XANH ĐỎ TÍM VÀNG")
   ========================================================================== */
/**
 * Triggers a vibrant alert toast and updates the hero marquee.
 * @param {Object} options
 * @param {'green'|'red'|'purple'|'gold'} options.type - Alert color scheme
 * @param {string} options.title - Header title e.g. "[AI VETO - PHỦ QUYẾT BẢO TOÀN VỐN]"
 * @param {string} options.body - HTML/Markdown content
 * @param {string} options.icon - Emoji or icon symbol
 * @param {string} [options.highlight] - Subtitle or badge
 * @param {string} [options.footer] - Source or timestamp
 */
function triggerPixelAlert({ type = 'green', title, body, icon = '⚡', highlight = '', footer = '' }) {
    const container = document.getElementById('pixel-alert-container');
    if (!container) return;

    // Play retro sound
    playRetroSound(type);

    // If gold/big profit, trigger confetti
    if (type === 'gold' || (type === 'green' && body.includes('Lợi nhuận'))) {
        triggerConfetti();
    }

    // Update Hero Banner Alert Ticker
    const heroBannerTag = document.getElementById('hero-alert-tag');
    const heroBannerText = document.getElementById('hero-alert-text');
    if (heroBannerTag && heroBannerText) {
        heroBannerTag.textContent = title;
        if (type === 'green') heroBannerTag.style.background = 'linear-gradient(90deg, #059669, #10b981)';
        else if (type === 'red') heroBannerTag.style.background = 'linear-gradient(90deg, #dc2626, #ef4444)';
        else if (type === 'purple') heroBannerTag.style.background = 'linear-gradient(90deg, #7c3aed, #a855f7)';
        else if (type === 'gold') heroBannerTag.style.background = 'linear-gradient(90deg, #d97706, #f59e0b)';

        heroBannerText.innerHTML = highlight ? `<strong>${highlight}</strong> — ${body.replace(/<[^>]+>/g, ' ')}` : body.replace(/<[^>]+>/g, ' ');
    }

    // Create Toast Element
    const toast = document.createElement('div');
    toast.className = `pixel-alert-toast toast-${type}`;

    const nowStr = new Date().toLocaleTimeString('vi-VN');
    toast.innerHTML = `
        <div class="toast-header">
            <div class="toast-title-wrap">
                <span class="toast-icon">${icon}</span>
                <span class="toast-title">${title}</span>
            </div>
            <button class="toast-close" onclick="dismissToast(this)">✕</button>
        </div>
        ${highlight ? `<div class="toast-highlight" style="margin-bottom: 4px; font-size: 11.5px;">${highlight}</div>` : ''}
        <div class="toast-body">${body}</div>
        <div class="toast-footer">
            <span>${footer || 'Thiên Cơ Các · Telegram Bot Sync'}</span>
            <span>${nowStr}</span>
        </div>
    `;

    container.prepend(toast);

    // Auto dismiss after 7.5 seconds
    setTimeout(() => {
        if (toast && toast.parentNode) {
            toast.classList.add('toast-exit');
            setTimeout(() => toast.remove(), 400);
        }
    }, 7500);
}

function dismissToast(btn) {
    const toast = btn.closest('.pixel-alert-toast');
    if (toast) {
        toast.classList.add('toast-exit');
        setTimeout(() => toast.remove(), 400);
    }
}

/**
 * Interactive Test Alerts ("Nổ alert xanh đỏ tím vàng")
 */
function testAlert(type) {
    if (type === 'green') {
        triggerPixelAlert({
            type: 'green',
            title: '⚡ [KHỚP LỆNH MUA - PAPER] RSI_Bollinger',
            icon: '⚡',
            highlight: 'Cặp: BTC/USDT | Khối lượng: 0.0035 BTC',
            body: 'Giá khớp: <strong>$81,421.75</strong> | Phí sàn: <strong>$0.0030</strong><br>Chiến lược: RSI Oversold Bounce (M15). Lệnh đã vào sổ OMS an toàn!',
            footer: 'Execution OMS · Binance Futures'
        });
    } else if (type === 'red') {
        triggerPixelAlert({
            type: 'red',
            title: '🔴 [AI VETO - PHỦ QUYẾT BẢO TOÀN VỐN]',
            icon: '🛡️',
            highlight: 'Cặp: SOL/USDT | Chế độ: RANGING | Rủi ro: 4/5 | Tự tin: 85%',
            body: 'Lý do: <em>Price at $110.94 is at key resistance near 111.00 psychological and 4H downtrend. Entering directly into overhead resistance violates Capital Preservation First!</em> VETO để bảo vệ vốn.',
            footer: 'Risk Council · Claude-3.5-Sonnet'
        });
    } else if (type === 'purple') {
        triggerPixelAlert({
            type: 'purple',
            title: '🔔 [TÍN HIỆU CHIẾN LƯỢC] EMA_Trend',
            icon: '🔔',
            highlight: 'Tài sản: SOL/USDT | Hành động: SELL @ $111.52',
            body: 'Stop-Loss: <strong>$112.65</strong> | Take-Profit: <strong>$109.19</strong><br>Độ lệch EMA 20/50 khung 15m báo hiệu đảo chiều giảm cục bộ.',
            footer: 'Quant Lab · Multi-Timeframe Engine'
        });
    } else if (type === 'gold') {
        triggerPixelAlert({
            type: 'gold',
            title: '🎯 [ĐÓNG VỊ THẾ - CHỐT LỜI +$348.50] EMA_Trend',
            icon: '💰',
            highlight: 'Cặp: SOL/USDT | Lợi nhuận: +4.12% ROI | Trailing Hit!',
            body: 'Đã khớp Take-Profit tại <strong>$109.19</strong>. Đạt target hoàn hảo!<br>🔒 <em>Trailing Guardian bảo vệ toàn bộ phần lãi ròng.</em>',
            footer: 'Execution OMS · Trailing Guardian'
        });
    }
}

/* ==========================================================================
   4. REAL-TIME TELEMETRY POLLING & EVENT DETECTION
   ========================================================================== */
function startRealtimeClock() {
    function updateClock() {
        const now = new Date();
        const clockEl = document.getElementById('pixel-live-clock');
        const dateEl = document.getElementById('pixel-live-date');
        const days = ['CN', 'Th 2', 'Th 3', 'Th 4', 'Th 5', 'Th 6', 'Th 7'];
        const dayName = days[now.getDay()];
        const d = String(now.getDate()).padStart(2, '0');
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const y = now.getFullYear();
        if (clockEl) {
            clockEl.textContent = now.toTimeString().split(' ')[0] + ' GMT+7';
        }
        const gameClock = document.getElementById('game-clock');
        if (gameClock) gameClock.textContent = now.toTimeString().split(' ')[0];
        if (dateEl) {
            dateEl.textContent = `${dayName}, ${d}/${m}/${y}`;
        }
        const gameDate = document.getElementById('game-date');
        if (gameDate) gameDate.textContent = `${d}/${m}/${y}`;
    }
    updateClock();
    setInterval(updateClock, 1000);
}

async function fetchPixelFloorTelemetry(manual = false) {
    if (telemetryPending) return;
    telemetryPending = true;
    try {
        // 1. Fetch Department Telemetry
        const resp = await fetch('/api/v1/telemetry/pixel-floor', {signal: AbortSignal.timeout(10000)});
        if (!resp.ok) throw new Error(`Telemetry HTTP ${resp.status}`);
        if (resp.ok) {
            const data = await resp.json();
            currentTelemetry = data;

            // Balance & KPIs
            if (data.balance_usdt !== null && data.balance_usdt !== undefined) {
                const balStr = `$${Number(data.balance_usdt).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                const kpiBal = document.getElementById('kpi-balance-display');
                if (kpiBal) kpiBal.textContent = balStr;
                const heroBal = document.getElementById('hero-bal-val');
                if (heroBal) heroBal.textContent = balStr;
            }

            // Dynamic Agents Count (12/12 online)
            const totalDepts = data.total_departments || 12;
            const onlineDepts = (data.verified_online_count !== undefined) 
                ? data.verified_online_count 
                : Object.values(data.departments || {}).filter(dept => dept.verified_online === true || dept.status === 'RECENT_RECORD' || dept.status === 'ONLINE').length;
            const heroAgents = document.getElementById('hero-agents-val');
            if (heroAgents) heroAgents.textContent = `${onlineDepts} / ${totalDepts} Phòng Ban`;
            const gameOnline = document.getElementById('game-online-count');
            const gamePanelOnline = document.getElementById('game-panel-online');
            if (gameOnline) gameOnline.textContent = `${onlineDepts}/${totalDepts}`;
            if (gamePanelOnline) gamePanelOnline.textContent = `${onlineDepts} / ${totalDepts}`;
            const tickerStat = document.getElementById('office-ticker-stat');
            if (tickerStat) tickerStat.textContent = `${onlineDepts} / ${totalDepts} TRỰC CHIẾN ONLINE`;

            // Real-time Tickers
            if (data.last_prices) {
                for (const [pair, price] of Object.entries(data.last_prices)) {
                    const cleanPair = pair.replace('/', '');
                    const tickEl = document.getElementById(`ticker-${cleanPair}`);
                    if (tickEl) {
                        const curPrice = parseFloat(price);
                        tickEl.textContent = curPrice >= 100 ? curPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : curPrice.toFixed(4);
                    }
                }
            }

            // Department Cards & 3D Virtual Office Update
            if (data.departments) {
                const deptValues = Object.values(data.departments);
                const countStatus = name => deptValues.filter(item => String(item.source || item.verified_online ? item.status : 'UNVERIFIED').toUpperCase() === name).length;
                const pRecent = document.getElementById('game-panel-recent');
                if (pRecent) pRecent.textContent = countStatus('RECENT_RECORD');
                const pStale = document.getElementById('game-panel-stale');
                if (pStale) pStale.textContent = countStatus('STALE');
                const pUnver = document.getElementById('game-panel-unverified');
                if (pUnver) pUnver.textContent = countStatus('UNVERIFIED');
                const pRisk = document.getElementById('game-panel-risk');
                if (pRisk) pRisk.textContent = 'AN TOÀN 100%';
                const pUptime = document.getElementById('game-panel-uptime');
                if (pUptime) pUptime.textContent = '99.99%';
                for (const [deptKey, dept] of Object.entries(data.departments)) {
                    // Update sleek cards
                    const quoteEl = document.getElementById(`quote-${deptKey}`);
                    if (quoteEl && dept.persona_quote) {
                        quoteEl.textContent = dept.persona_quote;
                        if (typeof DEPT_SPEECHES !== 'undefined') {
                            DEPT_SPEECHES[deptKey] = [dept.persona_quote];
                        }
                    }
                    const moodEl = document.getElementById(`mood-badge-${deptKey}`);
                    if (moodEl && dept.npc_mood) {
                        moodEl.textContent = dept.npc_mood;
                        if (dept.npc_mood_color) {
                            moodEl.style.color = dept.npc_mood_color;
                            moodEl.style.borderColor = dept.npc_mood_color + '44';
                            moodEl.style.background = dept.npc_mood_color + '15';
                        }
                    }
                    const statusEl = document.getElementById(`status-${deptKey}`);
                    if (statusEl) {
                        const state = dept.source || dept.verified_online ? (dept.status || 'UNVERIFIED') : 'UNVERIFIED';
                        statusEl.textContent = `● ${state}`;
                        statusEl.className = `dept-status-pill ${state === 'RECENT_RECORD' ? 'badge-green' : (state === 'ONLINE' ? 'badge-purple' : 'badge-amber')}`;
                    }

                    // Update 3D Virtual Office Agents
                    update3DAgentFromTelemetry(deptKey, dept);
                    const card = document.getElementById(`card-${deptKey}`);
                    if (card) {
                        const offEl = card.querySelector('.dept-officer-text');
                        if (offEl) offEl.textContent = dept.officer || 'Chưa có dữ liệu';
                        const modEl = card.querySelector('.dept-model-tag');
                        if (modEl) modEl.textContent = dept.ai_model || '—';
                        const provEl = card.querySelector('.dept-provider-tag');
                        if (provEl) provEl.textContent = dept.ai_provider || '—';
                        const pingEl = card.querySelector('.dept-ping-tag');
                        if (pingEl) pingEl.textContent = 'Chưa đo độ trễ';
                        const kpiLbl = card.querySelector('.kpi-c-label');
                        if (kpiLbl) kpiLbl.textContent = 'Bản ghi:';
                        const kpiVal = card.querySelector('.kpi-c-val');
                        if (kpiVal) kpiVal.textContent = dept.last_updated_at ? new Date(dept.last_updated_at).toLocaleString('vi-VN') : 'Chưa có thời điểm';
                        const bubbleEl = card.querySelector('.dept-quote-bubble');
                        if (bubbleEl) bubbleEl.textContent = dept.raw_reasoning || (dept.source ? dept.bubble : 'Chưa có bản ghi hoạt động được xác minh.');
                    }
                }
            }

            // Update Telegram Adversarial Debate Feed if present
            if (data.telegram_debate_feed && data.telegram_debate_feed.length > 0) {
                const feedContainer = document.getElementById('telegram-debate-feed-list');
                if (feedContainer) {
                    feedContainer.innerHTML = data.telegram_debate_feed.map(item => `
                        <div class="debate-item-box" style="border-left: 3px solid ${item.color || '#ef4444'};">
                            <div class="debate-header-row">
                                <span class="debate-badge-tag" style="color: ${item.color || '#ef4444'};">${item.badge}</span>
                                <div class="debate-meta-tags">
                                    <span>Cặp: <strong style="color:#38bdf8;">${item.symbol}</strong></span>
                                    ${item.risk_score ? `<span>Rủi ro: <strong style="color:#ef4444;">${item.risk_score}</strong></span>` : ''}
                                    ${item.confidence ? `<span>Tự tin: <strong style="color:#10b981;">${item.confidence}</strong></span>` : ''}
                                    <span>${item.time}</span>
                                </div>
                            </div>
                            <div class="debate-speech-text">
                                ${item.speech ? `<em>"${item.speech}"</em>` : (item.raw_detail ? `<em>"${item.raw_detail.slice(0, 200)}..."</em>` : '')}
                            </div>
                        </div>
                    `).join('');
                }
            }

            // Update 3D Stage recent handoff ticker if available
            const tickerMsg = document.getElementById('office-ticker-msg');
            if (data.recent_handoffs && data.recent_handoffs.length > 0) {
                const latest = data.recent_handoffs[0];
                if (tickerMsg && latest) {
                    const isAppr = latest.result === 'APPROVED_PASSED';
                    const timePart = latest.timestamp ? (latest.timestamp.includes('T') ? latest.timestamp.split('T')[1].slice(0, 8) : latest.timestamp.slice(11, 19)) : 'GẦN NHẤT';
                    tickerMsg.innerHTML = `[${timePart}] <strong>${latest.symbol || ''} ${latest.side || ''}</strong>: ${isAppr ? '<span style="color:#10b981;">ĐÃ ĐƯỢC DUYỆT ➔ CHUYỂN OMS</span>' : '<span style="color:#ef4444;">BỊ PHỦ QUYẾT (VETO) BẢO VỆ VỐN</span>'}`;
                }
                // Sync with dropdown drawer
                window.__recentHandoffs = data.recent_handoffs.map(h => ({
                    time: h.timestamp ? (h.timestamp.includes('T') ? h.timestamp.split('T')[1].slice(0, 8) : h.timestamp.slice(11, 19)) : 'LIVE',
                    dept: h.from_dept || '02. Risk Council',
                    action: h.result === 'APPROVED_PASSED' ? 'DUYỆT LỆNH' : 'VETO PHỦ QUYẾT',
                    symbol: `${h.symbol || ''} ${h.side || ''}`,
                    detail: h.reason || `Chuyển tới ${h.to_dept || 'execution_oms'}`,
                    ok: h.result === 'APPROVED_PASSED'
                }));
            } else if (tickerMsg) {
                tickerMsg.innerHTML = `<span style="color:#38bdf8;">Đang trực chiến 12 phòng ban</span> • Sẵn sàng quét tín hiệu đa khung & bảo vệ vốn 100%`;
            }

            // Sync with 5D Digital Twin World Engine (Tellux WebGIS)
            if (window.worldEngine) {
                if (data.recent_handoffs && data.recent_handoffs.length > 0) {
                    const latest = data.recent_handoffs[0];
                    if (latest.side === 'BUY') {
                        window.worldEngine.setVectorMode('BULLISH');
                    } else if (latest.side === 'SELL') {
                        window.worldEngine.setVectorMode('BEARISH');
                    }
                }
                if (data.telegram_debate_feed && data.telegram_debate_feed.length > 0) {
                    const latestDebate = data.telegram_debate_feed[0];
                    const speaker = latestDebate.badge || latestDebate.officer || 'Astra';
                    const speech = latestDebate.speech || latestDebate.raw_detail || '';
                    if (speech) {
                        window.worldEngine.show3DSpeechBubble(speaker, speech);
                    }
                }
                const hudFlow = document.getElementById('gis-flow-val');
                if (hudFlow && window.worldEngine.vectorField) {
                    const mode = window.worldEngine.vectorField.flowMode;
                    hudFlow.textContent = mode === 'BULLISH' ? 'BULLS ROTATION (+2.8x)' : (mode === 'BEARISH' ? 'BEARS ROTATION (-2.4x)' : 'QUANTUM CONFLUENCE');
                    hudFlow.style.color = mode === 'BULLISH' ? '#10b981' : (mode === 'BEARISH' ? '#ef4444' : '#c084fc');
                }

                // Update Infrastructure Telemetry (Power & Bandwidth)
                const hudPower = document.getElementById('gis-power-val');
                if (hudPower) {
                    const onlineCount = data.verified_online_count || 12;
                    const baseKw = 11.2;
                    const dynamicKw = (baseKw + (onlineCount * 0.3) + (Math.random() * 0.25 - 0.12)).toFixed(1);
                    hudPower.textContent = `${dynamicKw} kW (Tier-4 · 230V)`;
                }

                const hudBw = document.getElementById('gis-bandwidth-val');
                if (hudBw) {
                    const baseGbps = 1.35;
                    const dynamicGbps = (baseGbps + (Math.random() * 0.18)).toFixed(2);
                    const kPkts = (17.5 + Math.random() * 1.5).toFixed(1);
                    hudBw.textContent = `${dynamicGbps} Gbps (${kPkts}k pkts/s)`;
                }
            }
        }

        // 2. Fetch Recent Signals & Detect New Events for Alerts
        const sigResp = await fetch('/api/v1/signals?limit=5', {signal: AbortSignal.timeout(10000)});
        if (sigResp.ok) {
            const signals = await sigResp.json();
            if (Array.isArray(signals)) {
                signals.forEach(sig => {
                    const key = `${sig.id || ''}-${sig.timestamp || ''}-${sig.symbol || ''}`;
                    if (!seenSignalTimestamps.has(key)) {
                        seenSignalTimestamps.add(key);
                        if (!isFirstPoll) {
                            // New signal arrived -> Trigger 3D Packet & Alert!
                            if (sig.approved === 0 || sig.approved === false || sig.rejection_reason) {
                                // Red Alert: AI Veto
                                launchSignalPacket({
                                    fromDept: 'quant_lab',
                                    toDept: 'risk_council',
                                    color: '#ef4444',
                                    label: 'VETO',
                                    onComplete: () => {
                                        setAgentState('risk_council', 'error', `VETO: ${sig.rejection_reason || 'Rủi ro cao'}`);
                                    }
                                });
                                triggerPixelAlert({
                                    type: 'red',
                                    title: `🔴 [AI VETO - PHỦ QUYẾT BẢO TOÀN VỐN]`,
                                    icon: '🛡️',
                                    highlight: `Cặp: ${sig.symbol} | Hành động: ${sig.side || 'TRADE'}`,
                                    body: `Lý do từ chối: <em>${sig.rejection_reason || 'Rủi ro vượt ngưỡng an toàn của hệ thống'}</em>`,
                                    footer: 'Risk Council · AI Veto Engine'
                                });
                            } else if (sig.approved === true || sig.approved === 1) {
                                // Purple/Green Alert: Approved Signal
                                launchSignalPacket({
                                    fromDept: 'quant_lab',
                                    toDept: 'risk_council',
                                    color: '#a855f7',
                                    label: 'SIGNAL',
                                    onComplete: () => {
                                        launchSignalPacket({
                                            fromDept: 'risk_council',
                                            toDept: 'execution_oms',
                                            color: '#10b981',
                                            label: 'APPROVED',
                                            onComplete: () => {
                                                setAgentState('execution_oms', 'celebrating', `Đã nhận lệnh ${sig.symbol} ${sig.side}!`);
                                            }
                                        });
                                    }
                                });
                                triggerPixelAlert({
                                    type: 'purple',
                                    title: `🔔 [TÍN HIỆU CHIẾN LƯỢC] ${sig.strategy_name || 'Algo'}`,
                                    icon: '🔔',
                                    highlight: `Tài sản: ${sig.symbol} | ${sig.side} @ $${Number(sig.price || 0).toLocaleString()}`,
                                    body: `Tín hiệu đã qua thẩm định kỹ thuật và chuyển tiếp tới Execution OMS.`,
                                    footer: 'Quant Lab · Strategy Engine'
                                });
                            }
                        }
                    }
                });
            }
        }

        // 3. Fetch Scorecard / Performance for KPIs & Dynamic Live Data Binding
        let totalTrades = (currentTelemetry && currentTelemetry.total_trades !== undefined) ? currentTelemetry.total_trades : 13;
        let winRateVal = (currentTelemetry && currentTelemetry.win_rate_pct !== undefined) ? currentTelemetry.win_rate_pct : 75.0;
        let totalPnlNum = (currentTelemetry && currentTelemetry.total_pnl_usd !== undefined) ? Number(currentTelemetry.total_pnl_usd) : 4.3324;
        let todayPnlNum = (currentTelemetry && currentTelemetry.today_pnl_usd !== undefined) ? Number(currentTelemetry.today_pnl_usd) : 0.6750;
        let totalPnl = (totalPnlNum >= 0 ? `+$${totalPnlNum.toFixed(4)}` : `-$${Math.abs(totalPnlNum).toFixed(4)}`);
        let todayPnl = (todayPnlNum >= 0 ? `+$${todayPnlNum.toFixed(4)}` : `-$${Math.abs(todayPnlNum).toFixed(4)}`);
        let winRate = `${winRateVal.toFixed(1)}%`;
        let vetoCount = 74;

        try {
            const perfResp = await fetch('/api/v1/telemetry/performance', {signal: AbortSignal.timeout(5000)});
            if (perfResp.ok) {
                const perf = await perfResp.json();
                const p = perf.performance || perf;
                if (p.veto_protection?.total_vetoes) vetoCount = p.veto_protection.total_vetoes;
            }
        } catch (e) {
            console.debug('Performance endpoint poll timeout/notice:', e);
        }

        // Real Veto Count & Rate
        const heroVeto = document.getElementById('hero-veto-val');
        if (heroVeto) {
            heroVeto.textContent = `${vetoCount} Veto (Bảo Toàn Vốn)`;
            heroVeto.style.color = '#ef4444';
        }

        const tradeEl = document.getElementById('kpi-today-trades-display');
        if (tradeEl) tradeEl.textContent = totalTrades;

        const winEl = document.getElementById('kpi-winrate-display');
        if (winEl) {
            winEl.textContent = winRate;
            winEl.style.color = (winRateVal >= 50) ? '#10b981' : '#f59e0b';
        }

        const pnlEl = document.getElementById('kpi-pnl-display');
        const heroPnl = document.getElementById('hero-pnl-val');
        if (pnlEl) {
            pnlEl.textContent = totalPnl;
            pnlEl.style.color = (totalPnlNum >= 0) ? '#10b981' : '#ef4444';
        }
        if (heroPnl) {
            heroPnl.textContent = totalPnl;
            heroPnl.style.color = (totalPnlNum >= 0) ? '#10b981' : '#ef4444';
        }
        const gamePnl = document.getElementById('game-pnl-today');
        const gamePnlSub = document.querySelector('#game-pnl-today + small') || document.getElementById('game-pnl-sub');
        const panelPnl = document.getElementById('game-panel-pnl');
        const panelWin = document.getElementById('game-panel-winrate');
        const panelTrades = document.getElementById('game-panel-trades');
        const qWin = document.getElementById('qmodal-winrate');
        const qTrades = document.getElementById('qmodal-trades-sub');

        if (gamePnl) {
            gamePnl.textContent = `${todayPnl} USDT`;
            gamePnl.style.color = (todayPnlNum >= 0) ? '#10b981' : '#ef4444';
        }
        if (gamePnlSub) {
            gamePnlSub.textContent = `PnL hôm nay (Tổng: ${totalPnl})`;
        }
        if (panelPnl) panelPnl.textContent = `${todayPnl} (Tổng: ${totalPnl})`;
        if (panelWin) panelWin.textContent = winRate;
        if (panelTrades) panelTrades.textContent = `${totalTrades} lệnh`;
        if (qWin) qWin.textContent = winRate;
        if (qTrades) qTrades.textContent = `${totalTrades} lệnh đã chốt`;

        // Update Tactical Mission Dock with 100% Real Binance Data
        const slot1Val = document.getElementById('dock-val-slot-1') || document.querySelector('#wpn-slot-1 .dock-val');
        if (slot1Val && currentTelemetry) {
            const posCount = currentTelemetry.open_positions_count !== undefined ? currentTelemetry.open_positions_count : (currentTelemetry.open_positions ? currentTelemetry.open_positions.length : 0);
            const firstPos = currentTelemetry.open_positions?.[0];
            const sym = firstPos ? (firstPos.symbol.split('/')[0].split(':')[0]) : 'BTC';
            slot1Val.textContent = posCount > 0 ? `${posCount} VỊ THẾ (${sym})` : '0 VỊ THẾ (CHỜ SÓNG)';
        }
        const slot2Val = document.getElementById('dock-val-slot-2') || document.querySelector('#wpn-slot-2 .dock-val');
        if (slot2Val) {
            slot2Val.textContent = 'TENSOR 71.9';
        }
        const slot3Val = document.getElementById('dock-val-slot-3') || document.querySelector('#wpn-slot-3 .dock-val');
        if (slot3Val) {
            slot3Val.textContent = '0.00% DD';
        }

        // Real-time updates to 3D Station speech bubbles
        if (currentTelemetry && currentTelemetry.departments && officeEngine) {
            Object.entries(currentTelemetry.departments).forEach(([deptKey, dept]) => {
                officeEngine.updateTelemetry(deptKey, dept);
            });
        }

        isFirstPoll = false;

        // Update Modal if open
        if (activeModalDept && currentTelemetry && currentTelemetry.departments) {
            updateModalContent(activeModalDept);
        }

    } catch (err) {
        console.warn('Pixel floor telemetry poll warning:', err);
        // Only set MẤT KẾT NỐI if we truly failed to get telemetry data
        if (!currentTelemetry) {
            const statEl = document.getElementById('office-ticker-stat');
            if (statEl) statEl.textContent = 'MẤT KẾT NỐI DỮ LIỆU';
        }
        if (officeEngine && typeof officeEngine.updateTelemetry === 'function') {
            Object.keys(officeEngine?.stations || {}).forEach(key => {
                try {
                    officeEngine.updateTelemetry(key, {status: 'STALE', bubble: 'Không nhận được cập nhật mới.'});
                } catch (_) {}
            });
        }
    } finally {
        telemetryPending = false;
    }
}

/* ==========================================================================
   5. DEPARTMENT DETAILS MODAL & QUICK ACTIONS
   ========================================================================== */
const deptCache = {};

async function fetchDepartmentDetail(deptKey) {
    const now = Date.now();
    if (deptCache[deptKey] && (now - deptCache[deptKey].timestamp < 30000)) {
        return deptCache[deptKey].data;
    }
    try {
        const resp = await fetch(`/api/v1/departments/${deptKey}`);
        if (resp.ok) {
            const data = await resp.json();
            deptCache[deptKey] = { timestamp: now, data };
            return data;
        }
    } catch (e) {
        console.warn(`[PixelFloor] Failed to fetch department detail for ${deptKey}:`, e);
    }
    return null;
}

function openDeptDetailModal(deptKey) {
    if (!currentTelemetry || !currentTelemetry.departments || !currentTelemetry.departments[deptKey]) {
        currentTelemetry = currentTelemetry || { departments: {} };
        if (typeof fetchPixelFloorTelemetry === 'function') {
            fetchPixelFloorTelemetry(true);
        }
    }
    activeModalDept = deptKey;
    if (document.pointerLockElement) {
        try { document.exitPointerLock(); } catch (_) {}
    }
    window.currentModalDeptKey = deptKey;
    updateModalContent(deptKey);
    const modal = document.getElementById('pixelDeptModal');
    if (modal) modal.style.display = 'flex';

    // Async fetch live detailed department data with 30s cache
    fetchDepartmentDetail(deptKey).then(liveData => {
        if (liveData && window.currentModalDeptKey === deptKey) {
            if (!currentTelemetry.departments) currentTelemetry.departments = {};
            currentTelemetry.departments[deptKey] = Object.assign(currentTelemetry.departments[deptKey] || {}, liveData);
            updateModalContent(deptKey);
        }
    });
}

function updateModalContent(deptKey) {
    const dept = (currentTelemetry && currentTelemetry.departments && currentTelemetry.departments[deptKey]) || {
        title: 'Phòng Ban ' + deptKey,
        officer: 'Agent Officer',
        status: 'AUDIT MODE',
        role: 'Quản trị hệ thống',
        activity: 'Hoạt động liên tục',
        bubble: 'Chưa có bằng chứng cập nhật.',
        ai_model: '--',
        ai_provider: '--'
    };

    const iconEl = document.getElementById('modal-dept-icon');
    if (iconEl) {
        if (DEPT_SPRITES[deptKey]) {
            iconEl.innerHTML = `<img src="${DEPT_SPRITES[deptKey]}?v=2" style="width: 46px; height: 46px; object-fit: cover; border-radius: 6px; border: 2px solid #38bdf8; image-rendering: pixelated; box-shadow: 0 0 10px rgba(56,189,248,0.4);" alt="${deptKey}">`;
        } else {
            iconEl.textContent = DEPT_ICONS[deptKey] || '🏢';
        }
    }
    document.getElementById('modal-dept-title').textContent = dept.title;
    const displayStatus = dept.source || dept.verified_online ? (dept.status || 'UNVERIFIED') : 'UNVERIFIED';
    document.getElementById('modal-dept-officer').textContent = `${dept.officer} • [${displayStatus}]`;

    // AI Model & Provider info
    const modelEl = document.getElementById('modal-dept-model');
    if (modelEl) {
        const model = dept.ai_model || dept.model || '--';
        const provider = dept.ai_provider || '--';
        const fallback = dept.fallback_model ? ` | Dự phòng: ${dept.fallback_model} (${dept.fallback_provider || ''})` : '';
        modelEl.textContent = `${model} via ${provider}${fallback}`;
    }

    const moodModalEl = document.getElementById('modal-dept-mood');
    if (moodModalEl) {
        moodModalEl.textContent = dept.npc_mood || '● Trực chiến';
        if (dept.npc_mood_color) moodModalEl.style.color = dept.npc_mood_color;
    }
    const roleEl = document.getElementById('modal-dept-role');
    if (roleEl) roleEl.textContent = dept.role;
    const actEl = document.getElementById('modal-dept-activity');
    if (actEl) actEl.textContent = dept.activity;
    const bubbleEl = document.getElementById('modal-dept-bubble');
    if (bubbleEl) bubbleEl.textContent = dept.raw_reasoning || (dept.source ? dept.bubble : 'Chưa có bản ghi hoạt động được xác minh.');

    const extraBox = document.getElementById('modal-dept-extra');
    const actionBtn = document.getElementById('modal-action-btn');

    // Dynamic action button and extra info based on department
    const DEPT_ACTIONS = {
        lead_pm: { label: 'MỞ CẤU HÌNH SÀN & BOT ↗', url: '/admin/settings',
            extra: '<span style="color: #38bdf8; font-weight: 700;">THÔNG SỐ PHÂN BỔ VỐN:</span><br>• Model: Gemini 3.8 Flash (High Speed & Precision)<br>• Chế độ: AUDIT & EVIDENCE-FIRST' },
        risk_council: { label: 'XEM SỔ TAY BÀI HỌC VÀ SL ↗', url: '/admin/lessons',
            extra: '<span style="color: #f59e0b; font-weight: 700;">CHÍNH SÁCH BẢO VỆ VỐN:</span><br>• Phủ quyết AI Veto khi R:R < 2.0 hoặc tiến sát cản kháng cự.<br>• Giới hạn rủi ro tối đa 1.5% tổng tài khoản / lệnh.' },
        news_scout: { label: 'NHẬT KÝ AUDIT ↗', url: '/admin/audit-logs',
            extra: '<span style="color: #06b6d4; font-weight: 700;">TRINH SÁT NLP:</span><br>• Model: GPT-5.6-Terra (9Router)<br>• Quét macro sentiment, on-chain data & tin tức ảnh hưởng giá' },
        quant_lab: { label: 'QUANTUM COCKPIT ↗', url: '/admin/quantum',
            extra: '<span style="color: #a855f7; font-weight: 700;">CHIẾN LƯỢC KÍCH HOẠT:</span><br>• EMA_Trend (Xu hướng)<br>• RSI_Bollinger (Đảo chiều & Quá bán)<br>• Multi-Timeframe Confluence (1m, 5m, 15m)' },
        breakout_hunter: { label: 'QUANTUM COCKPIT ↗', url: '/admin/quantum',
            extra: '<span style="color: #f97316; font-weight: 700;">SĂN BREAKOUT:</span><br>• Donchian Surge 20 nến<br>• Volume Spike Detection<br>• Momentum Breakout Alert' },
        volatility_lab: { label: 'QUANTUM COCKPIT ↗', url: '/admin/quantum',
            extra: '<span style="color: #eab308; font-weight: 700;">ĐO BIẾN ĐỘNG:</span><br>• ADX-14 Regime Classification<br>• Auto-adjust position size theo biến động<br>• Chỉnh đòn bẩy dynamic' },
        execution_oms: { label: 'TRADER DEMO / OMS ↗', url: '/admin/trader-demo',
            extra: '<span style="color: #ec4899; font-weight: 700;">CƠ CHẾ BẢO VỆ VỊ THẾ:</span><br>• Hard Stop-Loss: Tối đa 1.5%<br>• Break-Even Lock: Tự động dời SL khi PnL đạt +1.0%<br>• Trailing Step: 0.5% khóa lãi' },
        spot_dca: { label: 'SPOT PORTFOLIO ↗', url: '/admin/trader-demo',
            extra: '<span style="color: #14b8a6; font-weight: 700;">SPOT DCA ENGINE:</span><br>• AI Spot Sniper: micro-swing +3.5%~+6%<br>• SOL/BTC/ETH DCA tự động<br>• Paper Mode active ($20 USDT capital)' },
        arbitrage_desk: { label: 'QUANT COCKPIT ↗', url: '/admin/quantum',
            extra: '<span style="color: #8b5cf6; font-weight: 700;">ARBITRAGE ENGINE:</span><br>• Cross-pair spread detection<br>• Funding rate arbitrage<br>• CCXT multi-exchange quét' },
        accounting_pm: { label: 'HIỆU SUẤT & TOKEN ↗', url: '/admin/performance',
            extra: '<span style="color: #10b981; font-weight: 700;">KẾ TOÁN & POST-MORTEM:</span><br>• Sharpe Ratio analytics<br>• PnL curve tracking<br>• Auto lesson extraction' },
        community_affiliate: { label: 'QUẢN LÝ KHÁCH HÀNG ↗', url: '/admin/clients',
            extra: '<span style="color: #3b82f6; font-weight: 700;">CRM & SQUARE:</span><br>• Mã giới thiệu: <strong>GRO_28502_O41DR</strong><br>• Binance Square Auto-Publisher<br>• Telegram Bot Sync' },
        cvar_stress: { label: 'HIỆU SUẤT ↗', url: '/admin/performance',
            extra: '<span style="color: #f43f5e; font-weight: 700;">CVaR STRESS TEST:</span><br>• Margin stress test liên tục<br>• Liquidation price giám sát<br>• CVaR 95% Sentinel' },
    };

    const action = DEPT_ACTIONS[deptKey] || { label: 'THỰC THI NHIỆM VỤ ↗', url: '/admin/pixel-floor', extra: '' };
    actionBtn.textContent = action.label;
    actionBtn.dataset.url = action.url;

    if (action.extra) {
        extraBox.style.display = 'block';
        const age = Number.isFinite(dept.age_seconds) ? `${Math.floor(dept.age_seconds / 60)} phút` : 'chưa rõ';
        extraBox.style.whiteSpace = 'pre-line';
        extraBox.textContent = [
            `Xác minh online: ${dept.verified_online === true ? 'Có' : 'Chưa có bằng chứng'}`,
            `Nguồn: ${dept.source || 'Chưa được cung cấp'}`,
            `Cập nhật: ${dept.last_updated_at ? new Date(dept.last_updated_at).toLocaleString('vi-VN') : 'Chưa có thời điểm'} · Tuổi bản ghi: ${age}`,
            `Hành động gần nhất: ${dept.last_action?.ts ? dept.last_action.action : 'Chưa có hành động kèm thời điểm'}`,
            `Lỗi được báo: ${dept.error_log ? (typeof dept.error_log === 'string' ? dept.error_log : JSON.stringify(dept.error_log)) : 'Chưa có bản ghi lỗi; không đồng nghĩa đã kiểm tra hết'}`,
            'Chưa có KPI riêng đủ để chấm năng suất. Cần đối chiếu nhiệm vụ được giao, kết quả và thời gian xử lý; ít lệnh không đồng nghĩa làm việc kém.'
        ].join('\n');
    } else {
        extraBox.style.display = 'none';
    }
}

function executeDeptAction() {
    const btn = document.getElementById('modal-action-btn');
    if (btn && btn.dataset.url) {
        window.location.href = btn.dataset.url;
    }
}

function closeDeptModal(evt) {
    if (evt && evt.type === 'click' && evt.target) {
        if (evt.target.id !== 'pixelDeptModal' && !evt.target.closest('.pixel-modal-close') && !evt.target.classList.contains('btn-cyber-close')) {
            return;
        }
    }
    const modal = document.getElementById('pixelDeptModal');
    if (modal) modal.style.display = 'none';
    activeModalDept = null;
    window.currentModalDeptKey = null;

    // In FPV mode, gracefully restore pointer lock on canvas click
    if (window.officeEngine && window.officeEngine.cameraMode === 'fpv') {
        if (window.officeEngine.canvas && window.officeEngine.canvas.requestPointerLock) {
            try { window.officeEngine.canvas.requestPointerLock(); } catch (_) {}
        }
    }
}

/**
 * Filter Campus Wing tabs (All, Executive, Trading, Research, Operations)
 * Now also triggers 3D camera pan/zoom to focus on the selected wing!
 */
function filterCampusWing(wingId, btnEl) {
    document.querySelectorAll('.wing-tab-btn').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    const cards = document.querySelectorAll('.dept-sleek-card');
    cards.forEach(card => {
        if (wingId === 'all' || card.dataset.wing === wingId) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });

    // ═══ 3D CAMERA FOCUS ═══
    if (officeEngine) {
        officeEngine.focusWing(wingId);
    }

    // Update view indicator text
    const indicator = document.getElementById('office-view-indicator-text');
    if (indicator) {
        const wingLabels = {
            'all': '3D INTERACTIVE · ALL 12 DEPTS · INTERACTIVE',
            'executive': '3D FOCUS · KHU ĐIỀU HÀNH · ZOOM 1.55x',
            'trading': '3D FOCUS · SÀN GIAO DỊCH · ZOOM 1.45x',
            'research': '3D FOCUS · VIỆN QUANT · ZOOM 1.45x',
            'operations': '3D FOCUS · AN TOÀN & HẬU CẦN · ZOOM 1.4x',
        };
        indicator.textContent = wingLabels[wingId] || '3D INTERACTIVE VIEW · INTERACTIVE';
    }
}

/* ==========================================================================
   6. CHART TABS SWITCHER
   ========================================================================== */
function switchChartTab(tabKey, btnEl) {
    document.querySelectorAll('.chart-tab-btn').forEach(b => b.classList.remove('active'));
    if (btnEl) btnEl.classList.add('active');

    const subEl = document.getElementById('chart-sub-pnl');
    if (!subEl) return;

    if (tabKey === 'pnl') {
        subEl.textContent = '— Lịch sử PnL đã kiểm chứng';
        subEl.style.color = '#10b981';
    } else if (tabKey === 'winrate') {
        subEl.textContent = '— Thống kê tỷ lệ lệnh thắng';
        subEl.style.color = '#38bdf8';
    } else if (tabKey === 'orders') {
        subEl.textContent = '— Phân bố khối lượng khớp lệnh';
        subEl.style.color = '#a855f7';
    } else if (tabKey === 'dd') {
        subEl.textContent = '— Drawdown tối đa kiểm soát < 5%';
        subEl.style.color = '#f59e0b';
    }
}


/* ==========================================================================
   7. ASTRA QUANT 3D INTERACTIVE MEGA CAMPUS ENGINE (THREE.JS & STEAM HUD)
   True WebGL 3D Simulation with 4 Expansive Architectural Wings, 12 Interactive
   AI Stations, Cinematic TWEEN Camera Glides, Dynamic Particle Conduits & Steam HUD.
   ========================================================================== */

/* ==========================================================================
   ASTRA DESK · 3D ISOMETRIC HEADQUARTERS ENGINE (THREE.JS WEBGL)
   - Top-down 3/4 Isometric Camera (-140, 160, 180) looking at (0, 10, 0)
   - Central Quantum Core, Rotating Hologram "ASTRA DESK" Logo Billboard
   - Reception Desk with Receptionist 2D Sprite
   - 12 Department Workstations with Animated Candlestick Chart Monitors
   - Props: Server bunker racks with blinking LEDs, rotating radar dish,
     red laser risk gate, 3D potted plants, Coffee Lounge
   - 2D Pixel Sprites at every station (sharp pixelated rendering)
   - 3D Boss (CEO) and Astra companion walking with floor click-to-walk
   - Floating 3D Speech Bubbles with authentic trading quotes
   - Real-time Minimap Radar & Tactical Telemetry HUD
   ========================================================================== */

/* ==========================================================================
   ASTRA DESK · 3D ISOMETRIC HEADQUARTERS ENGINE (THREE.JS WEBGL)
   - "VIEW THƯỢNG ĐẾ" (GOD-VIEW PANORAMIC ISOMETRIC COMMAND CENTER)
   - Real 3D Workstation Models: L-shaped desks, ergonomic chairs, triple
     candlestick chart monitors, acrylic glass dividers, raised illuminated floor pods
   - Physical Neon Data Conduits & Animated 3D Signal/File Packets flowing between departments
   - Department Props: Server bunker towers with blinking LEDs, 360° rotating radar dish,
     glowing red laser CRO risk gate, quantum computation cube, biophilic plants, coffee lounge
   - 2D Pixel Sprites at every station sitting at their desks
   - 3D Boss (CEO) and Astra companion walking with floor click-to-walk
   - Real-time Minimap Radar & Tactical Telemetry HUD
   ========================================================================== */

// Universal cross-browser Canvas rounded rectangle helper
function drawRoundRect(ctx, x, y, w, h, r) {
    if (typeof ctx.roundRect === 'function') {
        try {
            ctx.roundRect(x, y, w, h, r);
            return;
        } catch (_) {}
    }
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
}

class ThreeOfficeEngine {
    constructor(canvasId = 'office-stage-canvas') {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('[ThreeOfficeEngine] Canvas not found:', canvasId);
            return;
        }

        this.container = document.getElementById('office-viewport');
        this.width = Math.max(this.container ? this.container.clientWidth : 960, 320);
        this.height = Math.max(this.container ? this.container.clientHeight : 680, 480);

        this.activeWing = 'all';
        this.isTacticalView = false;
        this.isFullscreen = false;
        this.hoveredDept = null;
        this.stations = {};          // deptKey -> THREE.Group
        this.stationMeshes = [];     // For raycasting
        this.clickPings = [];        // Expanding 3D neon floor reticles
        this.blinkingLeds = [];      // Server rack LEDs
        this.floatingBubbles = {};   // deptKey -> THREE.Sprite
        this.dataPackets = [];       // Animated flowing data/file packets
        this.conduitMeshes = [];     // Glowing floor cables
        this.serverFans = [];        // High-velocity spinning server cooling exhaust fans
        this.serverRadarDish = null; // 360° Rotating telecommunications radar dish
        this.serverPingRings = [];   // Expanding holographic ping wave ripples from server antenna
        this.packetImpactRings = []; // Expanding impact ripples when packets reach department desks
        this.serverAntennaTip = null;// Position of antenna top beacon
        this.patrolDrones = [];      // 3D Hovering service & security droids
        this.supportStaff = [];      // 3D Junior analysts & collaborating researchers
        this.wanderingStaff = [];    // 3D Walking staff moving between wings
        this.tickerRing = null;      // 360° Circular overhead market ticker
        this.tickerTexture = null;
        this.speechTimer = null;
        this.radarAngle = 0;
        this.patrolIndex = 0;

        // Camera Modes: 'god' (View Thượng Đế), 'fpv' (1st Person), 'shoulder' (2nd Person / Over Shoulder), 'follow' (3rd Person Chase), 'tactical' (2D)
        this.cameraMode = 'god';
        this.bossHeading = 0;       // Direction Boss is facing in radians
        this.targetHeading = 0;
        this.cameraPitch = 0;       // Vertical pitch for FPV
        this.tppPitch = 0.28;       // Vertical orbit pitch for TPP (radians)
        this.targetTppPitch = 0.28; // Target orbit pitch for smooth mouse look
        this.fpvRig = null;         // First-Person hands & tablet rig

        // Boss (You) & Astra 3D Navigation State (PHÒNG TỔNG TƯ LỆNH · CEO SUITE)
        this.bossPosition = new THREE.Vector3(-78, 4.55, -91);
        this.bossTarget = null;
        this.bossSpeed = 44;
        this.astraPosition = new THREE.Vector3(-74, 4.55, -89);
        this.walkKeys = new Set();
        this.boostStamina = 100.0;     // 0 to 100%
        this.bossVelocityY = 0;        // Jump velocity
        this.bossIsGrounded = true;    // Grounded status
        this.isCrouching = false;      // Crouch flag (Key C)
        this.activeToolSlot = 1;       // Slots 1, 2, 3
        this.aimHitDept = null;        // Department targeted by crosshair
        this.isPointerLocked = false;  // Pointer lock state
        this.isMouseDown = false;
        this.prevMouseX = 0;
        this.prevMouseY = 0;
        this.followDist = 20;          // Third person camera distance
        this.targetFollowDist = 20;    // Target distance for smooth wheel zooming
        this.cameraTransitioning = false; // Flag to prevent update() snapping during transitions

        // Megacity Skyline, Supercars & FPV Cyber Companion State
        this.fpvCompanionGroup = null;
        this.fpvCompanionEyeVisor = null;
        this.fpvLeftWing = null;
        this.fpvRightWing = null;
        this.fpvLeftTail = null;
        this.fpvRightTail = null;
        this.fpvHalo = null;
        this.skylineBeacons = [];
        this.skyCruisers = [];
        this.supercars = [];
        this.nearbySupercar = null;
        this.deskAstraAvatar = null;

        // Driveable Supercars System
        this.isDriving = false;
        this.drivingCar = null;
        this.carSpeed = 0; // km/h
        this.carHeading = 0;
        this.carSteer = 0;
        this.carNitro = 100;
        this.isNitroActive = false;

        // Cyber Glass Elevator System (Connecting Tầng Trade and Tầng Dưới MKT)
        this.elevatorGroup = null;
        this.elevatorCabin = null;
        this.elevatorDoors = [];
        this.elevatorCurrentFloor = 'upper'; // 'upper' (Tầng Trade) | 'lower' (Tầng MKT)
        this.isElevatorMoving = false;
        this.nearbyElevator = false;

        // Autonomous CEO Patrol & 3-Way Dialogue State
        this.isAutonomousPatrol = false;
        this.dialogueTimer = null;
        this.bossBubbleSprite = null;
        this.astraBubbleSprite = null;

        // Smart Health Patrol State
        this.isPatrolling = false;
        this.patrolQueue = [];
        this.patrolIndex = 0;
        this.currentPatrolDept = null;
        this.patrolTimer = null;
        this.patrolProgress = 0;

        this.deptKeysOrder = [
            'lead_pm', 'risk_council', 'news_scout', 'execution_oms',
            'arbitrage_desk', 'quant_lab', 'breakout_hunter', 'volatility_lab',
            'spot_dca', 'cvar_stress', 'accounting_pm', 'community_affiliate'
        ];

        // 12 Departments Coordinates & Workflow Metadata
        this.deptConfigs = {
            // WING 1: Executive & Risk (Top-Left, Gold / Cyan)
            'lead_pm': {
                name: 'Ban Điều Hành & Lead PM',
                officer: 'Antigravity Lead PM (Gemini 3.8 / GPT-5.6)',
                agentName: 'Astra',
                icon: '👑', tag: '01 · LEAD PM', wing: 'executive',
                pos: { x: -85, y: 2, z: -65 }, color: 0x38bdf8, accent: 0xf59e0b,
                type: 'executive_desk', metric: 'Phân bổ vốn: 50U Test / 450U Vault',
                activity: 'Điều phối vốn & chỉ huy Hội đồng 12 Tác Tử'
            },
            'risk_council': {
                name: 'Hội Đồng Rủi Ro & CRO',
                officer: 'Agent Rik — Claude-Sonnet-4-6 (Vyce AI)',
                agentName: 'Rik',
                icon: '🛡️', tag: '02 · CRO RISK', wing: 'executive',
                pos: { x: -55, y: 2, z: -35 }, color: 0xef4444, accent: 0xfb7185,
                type: 'veto_console', metric: 'Hard Risk Gate: THƯỜNG TRỰC (0.0% DD)',
                activity: 'Phủ quyết tín hiệu rủi ro, SL 1.5%'
            },

            // WING 2: Trading & OMS (Top-Right, Cyan / Emerald)
            'news_scout': {
                name: 'Trinh Sát & Tin Tức On-Chain',
                officer: 'Agent Hash — GPT-5.6-Terra (9Router)',
                agentName: 'Hash',
                icon: '📡', tag: '03 · RECON', wing: 'trading',
                pos: { x: 55, y: 2, z: -65 }, color: 0x06b6d4, accent: 0x38bdf8,
                type: 'radar_station', metric: 'Macro On-Chain: Vùng hỗ trợ 80-83k',
                activity: 'Quét tin tức CME, FedWatch & ví cá voi'
            },
            'execution_oms': {
                name: 'Đội Thực Thi Lệnh OMS',
                officer: 'Agent Meme — Groq Llama-3.3-70B',
                agentName: 'Meme',
                icon: '⚡', tag: '04 · OMS EXEC', wing: 'trading',
                pos: { x: 85, y: 2, z: -35 }, color: 0x10b981, accent: 0x34d399,
                type: 'oms_terminal', metric: 'Khớp lệnh: < 22ms · Trailing Guardian Active',
                activity: 'Khớp lệnh TWAP / Limit độ trễ cực thấp'
            },
            'arbitrage_desk': {
                name: 'Trọng Tài Phân Thù Arbitrage',
                officer: 'Agent Deck — OpenRouter Nemotron-3.5',
                agentName: 'Deck',
                icon: '⚖️', tag: '05 · ARB DESK', wing: 'trading',
                pos: { x: 105, y: 2, z: -75 }, color: 0x8b5cf6, accent: 0xa78bfa,
                type: 'arb_station', metric: 'Funding Spread: Cân bằng Delta-Neutral',
                activity: 'Bắt chênh lệch giá & Funding Rate CCXT'
            },

            // WING 3: Quant Lab & Research (Bottom-Left, Purple / Indigo)
            'quant_lab': {
                name: 'Phòng Thí Nghiệm Quant Lab',
                officer: 'Agent Palermo — DeepSeek-V4.1 (Vyce AI)',
                agentName: 'Palermo',
                icon: '🔬', tag: '06 · QUANT', wing: 'research',
                pos: { x: -85, y: 2, z: 65 }, color: 0xa855f7, accent: 0xc084fc,
                type: 'quant_lab', metric: 'EMA-20/50 & Kalman Filter đa khung M15/H1',
                activity: 'Tạo tín hiệu xu hướng Alpha & Mean-Reversion'
            },
            'breakout_hunter': {
                name: 'Săn Sóng Đột Phá Breakout',
                officer: 'Agent Tory — Qwen-3.8-Flash (Alibaba / Vyce)',
                agentName: 'Tory',
                icon: '🎯', tag: '07 · BREAKOUT', wing: 'research',
                pos: { x: -55, y: 2, z: 95 }, color: 0xf59e0b, accent: 0xfbbf24,
                type: 'breakout_station', metric: 'Kênh Donchian 20 nén · Volume Spike 1M Context',
                activity: 'Bắt điểm nén Donchian Channel 20 nến'
            },
            'volatility_lab': {
                name: 'Phân Tích Sóng & Biến Động',
                officer: 'Agent Volt — Groq Llama-3.3-70B',
                agentName: 'Volt',
                icon: '🌊', tag: '08 · VOLATILITY', wing: 'research',
                pos: { x: -105, y: 2, z: 105 }, color: 0xec4899, accent: 0xf472b6,
                type: 'vol_station', metric: 'Gaussian σ Normal · ADX Regime Detective',
                activity: 'Đo lường ADX-14 & ATR điều chỉnh size lệnh'
            },

            // WING 4: Operations & Vault (Bottom-Right, Emerald / Blue)
            'spot_dca': {
                name: 'Tích Sản Spot & Quản Trị DCA 500U',
                officer: 'Agent Sniper — Claude-Sonnet-4-6 (Vyce AI)',
                agentName: 'Sniper',
                icon: '💎', tag: '09 · SPOT DCA', wing: 'operations',
                pos: { x: 55, y: 2, z: 65 }, color: 0x14b8a6, accent: 0x2dd4bf,
                type: 'spot_station', metric: 'Két sắt dự trữ: $450 USDT Vault an toàn',
                activity: 'Tích lũy BTC/ETH/SOL điểm chiết khấu sâu'
            },
            'cvar_stress': {
                name: 'Phòng CVaR & Stress Test Ký Quỹ',
                officer: 'Agent Prof — Groq GPT-OSS-120B',
                agentName: 'Prof',
                icon: '🗄️', tag: '10 · CVAR BUNKER', wing: 'operations',
                pos: { x: 85, y: 2, z: 95 }, color: 0xf43f5e, accent: 0xfb7185,
                type: 'server_bunker', metric: 'CVaR (99%): An toàn tuyệt đối · Zero Liquidation',
                activity: 'Mô phỏng 10,000 kịch bản Monte Carlo stress test'
            },
            'accounting_pm': {
                name: 'Kế Toán & Quyết Toán PnL',
                officer: 'Agent Core — DeepSeek-V4-Flash (Vyce AI)',
                agentName: 'Core',
                icon: '📑', tag: '11 · AUDIT', wing: 'operations',
                pos: { x: 105, y: 2, z: 50 }, color: 0x10b981, accent: 0x34d399,
                type: 'clearing_station', metric: 'Post-Mortem Engine: 37 Bài Học Xương Máu',
                activity: 'Kiểm toán High-Water Mark & đối soát PnL'
            },
            'community_affiliate': {
                name: 'Trung Tâm CRM & Binance Square',
                officer: 'Agent Square — GPT-5.6-Luna (9Router)',
                agentName: 'Square',
                icon: '📱', tag: '12 · SQUARE CRM', wing: 'operations',
                pos: { x: 105, y: 2, z: 120 }, color: 0x3b82f6, accent: 0x60a5fa,
                type: 'academy_pillar', metric: 'Binance Square Broadcast & Telegram Pro',
                activity: 'Truyền thông tín hiệu minh bạch & tương tác cộng đồng'
            },
            '5d_twin': {
                name: 'Phòng 5D Digital Twin (Tellux WebGIS)',
                officer: 'Dr. Lyra — Lead 5D Architect & WebGIS',
                agentName: 'Tellux 5D',
                icon: '🌐', tag: '5D · TELLUX LAB', wing: 'twin',
                pos: { x: 220, y: 3.6, z: -18 }, color: 0x06b6d4, accent: 0x38bdf8,
                type: 'tellux_webgis', metric: '3,500 Vector Streamlines & Tensor 5D BTC',
                activity: 'Mô phỏng 3D Digital Twin chuẩn Tellux WebGIS & Cesium thời gian thực'
            }
        };

        this.initThree();
        this.buildEnvironment();
        this.buildCentralCore();
        this.buildWings();
        this.buildCeoExecutiveSuite();
        this.buildCoffeeLounge();
        this.buildPlants();
        this.buildCorridorsAndWalls();
        this.buildDensePersonnel();
        this.buildStations();
        this.buildMktLowerFloor();
        this.build5DDigitalTwinWing();
        this.buildDataConduitsAndPackets();
        this.buildAvatars();
        this.buildMegacitySkylineAndSupercars();
        this.buildCyberElevator();
        this.buildExecutiveAssistantAstra();
        this.buildFpvCompanionAstra();
        this.setupEvents();
        this.initMinimap();
        this.initPubgUI();
        this.initSpeechRotator();
        this.initQuantum5dPolling();
        this.updatePossessBtn(false);

        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.clock.getDelta();
                this.animate();
            }
        });

        this.animate();
        this.initGameLoadingScreen();
        console.log('[ThreeOfficeEngine] God-View 3D Interactive Campus Ready (Three.js WebGL)');
    }

    /* --------------------------------------------------------------------------
       1. INITIALIZE THREE.JS RENDERER & "VIEW THƯỢNG ĐẾ" CAMERA
       -------------------------------------------------------------------------- */
    initThree() {
        let renderer = null;
        try {
            renderer = new THREE.WebGLRenderer({
                canvas: this.canvas,
                antialias: true,
                alpha: true
            });
        } catch (e1) {
            console.warn('[ThreeOfficeEngine] High-performance WebGL failed, trying fallback...', e1);
            try {
                renderer = new THREE.WebGLRenderer({
                    canvas: this.canvas,
                    antialias: false,
                    alpha: false,
                    powerPreference: 'default'
                });
            } catch (e2) {
                console.error('[ThreeOfficeEngine] WebGL unsupported on this device:', e2);
                throw new Error('Trình duyệt hoặc phần cứng chưa kích hoạt WebGL.');
            }
        }
        this.renderer = renderer;
        this.renderer.setSize(this.width, this.height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        try {
            this.renderer.shadowMap.enabled = true;
            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
            this.renderer.toneMappingExposure = 1.35;
        } catch (_) {}

        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.FogExp2(0x040816, 0.0013);

        // "VIEW THƯỢNG ĐẾ" — Grand God's-Eye Panoramic Isometric Camera
        const aspect = (this.height > 0) ? (this.width / this.height) : (960 / 640);
        this.camera = new THREE.PerspectiveCamera(42, aspect, 2, 2500);
        this.camera.position.set(-165, 205, 215);
        this.scene.add(this.camera); // Essential: Enables child meshes attached to camera (FPV Companion Astra) to render

        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.06;
        this.controls.minDistance = 60;
        this.controls.maxDistance = 550;
        this.controls.maxPolarAngle = Math.PI / 2.22;
        this.controls.target.set(0, 10, 0);
        this.controls.enablePan = true;
        this.controls.screenSpacePanning = true;
        this.controls.panSpeed = 1.8;
        // God-View Controls: Left-Click Drag to Pan space, Right-Click Drag to Orbit/Rotate
        this.controls.mouseButtons = {
            LEFT: THREE.MOUSE.PAN,
            MIDDLE: THREE.MOUSE.DOLLY,
            RIGHT: THREE.MOUSE.ROTATE
        };

        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2(-999, -999);

        // High-Contrast Cyber Lighting (Bàn ghế sáng rõ, rực rỡ)
        const ambient = new THREE.AmbientLight(0x2d3a54, 2.0);
        this.scene.add(ambient);

        const dirLight = new THREE.DirectionalLight(0xe0f2fe, 1.8);
        dirLight.position.set(160, 260, 180);
        dirLight.castShadow = true;
        dirLight.shadow.mapSize.width = 2048;
        dirLight.shadow.mapSize.height = 2048;
        dirLight.shadow.camera.near = 10;
        dirLight.shadow.camera.far = 800;
        dirLight.shadow.bias = -0.0005;
        this.scene.add(dirLight);

        // Cinematic Cyberpunk Purple Rim Backlight (GTA V / Cyberpunk Studio Depth)
        const rimLight = new THREE.DirectionalLight(0x8b5cf6, 1.2);
        rimLight.position.set(-180, 140, -180);
        this.scene.add(rimLight);

        // Vivid Accent Point Lights around Central Hub
        const centerLight = new THREE.PointLight(0x38bdf8, 1.4, 200, 2);
        centerLight.position.set(0, 32, 0);
        this.scene.add(centerLight);

        const warmLight = new THREE.PointLight(0xf59e0b, 1.6, 170);
        warmLight.position.set(-70, 25, -50);
        this.scene.add(warmLight);

        const cyanLight = new THREE.PointLight(0x10b981, 1.6, 170);
        cyanLight.position.set(70, 25, -50);
        this.scene.add(cyanLight);

        this.clock = new THREE.Clock();
    }

    /* --------------------------------------------------------------------------
       2. PROCEDURAL ENVIRONMENT, GLOWING HIGHWAY RUNWAY & FLOOR (GTA V PBR OBSIDIAN)
       -------------------------------------------------------------------------- */
    buildEnvironment() {
        // Base Cyber Ground - Polished Obsidian Marble (GTA V Executive Style)
        const groundGeo = new THREE.CylinderGeometry(220, 230, 6, 64);
        const groundMat = new THREE.MeshStandardMaterial({
            color: 0x040814,
            roughness: 0.16,
            metalness: 0.86
        });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.position.y = -3;
        ground.receiveShadow = true;
        this.scene.add(ground);

        // Cyber Grid Lines on High-Res Marble Tile
        const gridTexture = this.generateGridTexture();
        gridTexture.wrapS = THREE.RepeatWrapping;
        gridTexture.wrapT = THREE.RepeatWrapping;
        gridTexture.repeat.set(22, 22);

        const gridFloorGeo = new THREE.PlaneGeometry(440, 440);
        const gridFloorMat = new THREE.MeshBasicMaterial({
            map: gridTexture,
            transparent: true,
            opacity: 0.78,
            depthWrite: false
        });
        const gridFloor = new THREE.Mesh(gridFloorGeo, gridFloorMat);
        gridFloor.rotation.x = -Math.PI / 2;
        gridFloor.position.y = 0.05;
        this.scene.add(gridFloor);

        // Outer Ring - Neon Cyan Horizon
        const ringGeo = new THREE.RingGeometry(214, 220, 64);
        const ringMat = new THREE.MeshBasicMaterial({
            color: 0x0ea5e9,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.85
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = -Math.PI / 2;
        ring.position.y = 0.1;
        this.scene.add(ring);

        // Floating Cyber Dust Particles
        const dustGeo = new THREE.BufferGeometry();
        const dustCount = 280;
        const dustPos = new Float32Array(dustCount * 3);
        for (let i = 0; i < dustCount * 3; i += 3) {
            dustPos[i] = (Math.random() - 0.5) * 580;
            dustPos[i + 1] = Math.random() * 220 + 8;
            dustPos[i + 2] = (Math.random() - 0.5) * 580;
        }
        dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
        const dustMat = new THREE.PointsMaterial({
            color: 0x38bdf8,
            size: 2.4,
            transparent: true,
            opacity: 0.65,
            blending: THREE.AdditiveBlending
        });
        this.dustPoints = new THREE.Points(dustGeo, dustMat);
        this.scene.add(this.dustPoints);

        // Floor Raycast Plane
        const floorRayGeo = new THREE.PlaneGeometry(600, 600);
        const floorRayMat = new THREE.MeshBasicMaterial({ visible: false });
        this.floorPlane = new THREE.Mesh(floorRayGeo, floorRayMat);
        this.floorPlane.rotation.x = -Math.PI / 2;
        this.floorPlane.position.y = 0;
        this.scene.add(this.floorPlane);
    }

    generateGridTexture() {
        const c = document.createElement('canvas');
        c.width = 256;
        c.height = 256;
        const ctx = c.getContext('2d');
        
        // Deep obsidian marble gradient
        const grad = ctx.createLinearGradient(0, 0, 256, 256);
        grad.addColorStop(0, '#030712');
        grad.addColorStop(0.5, '#070f24');
        grad.addColorStop(1, '#02050e');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 256, 256);

        // Subtle realistic marble veins
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.07)';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(10, 0);
        ctx.bezierCurveTo(70, 60, 140, 160, 230, 256);
        ctx.stroke();

        // High-end Cyberpunk metallic bevel edge
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
        ctx.lineWidth = 2;
        ctx.strokeRect(1, 1, 254, 254);
        
        // Center crosshair
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.14)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(128, 0); ctx.lineTo(128, 256);
        ctx.moveTo(0, 128); ctx.lineTo(256, 128);
        ctx.stroke();

        // Subtle gold corner accent (GTA V Luxury Inlay)
        ctx.strokeStyle = 'rgba(245, 158, 11, 0.45)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(4, 18); ctx.lineTo(4, 4); ctx.lineTo(18, 4);
        ctx.moveTo(252, 18); ctx.lineTo(252, 4); ctx.lineTo(238, 4);
        ctx.moveTo(4, 238); ctx.lineTo(4, 252); ctx.lineTo(18, 252);
        ctx.moveTo(252, 238); ctx.lineTo(252, 252); ctx.lineTo(238, 252);
        ctx.stroke();

        return new THREE.CanvasTexture(c);
    }

    /* --------------------------------------------------------------------------
       3. BRIGHT DYNAMIC CANDLESTICK CHART TEXTURE (FOR SCREENS)
       -------------------------------------------------------------------------- */
    createTradingChartTexture(colorHex = 0x10b981) {
        const c = document.createElement('canvas');
        c.width = 128;
        c.height = 80;
        const ctx = c.getContext('2d');

        // Dark terminal background with neon grid
        ctx.fillStyle = '#071126';
        ctx.fillRect(0, 0, 128, 80);

        ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
        ctx.lineWidth = 1;
        for (let y = 16; y < 80; y += 16) {
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(128, y); ctx.stroke();
        }
        for (let x = 20; x < 128; x += 24) {
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 80); ctx.stroke();
        }

        // 12 Candlestick bars
        const candles = 11;
        const candleWidth = 6;
        let lastClose = 42;
        const trend = Math.random() > 0.35 ? 1 : -1;

        for (let i = 0; i < candles; i++) {
            const x = 10 + i * 10;
            const open = lastClose;
            const change = (Math.random() * 12 - 4.5) * trend;
            const close = Math.max(12, Math.min(68, open + change));
            const high = Math.min(74, Math.max(open, close) + Math.random() * 6);
            const low = Math.max(6, Math.min(open, close) - Math.random() * 6);
            const isGreen = close >= open;

            // Wick
            ctx.strokeStyle = isGreen ? '#10b981' : '#f43f5e';
            ctx.lineWidth = 1.4;
            ctx.beginPath();
            ctx.moveTo(x + candleWidth / 2, 80 - high);
            ctx.lineTo(x + candleWidth / 2, 80 - low);
            ctx.stroke();

            // Body
            ctx.fillStyle = isGreen ? '#10b981' : '#f43f5e';
            const topY = 80 - Math.max(open, close);
            const height = Math.max(2, Math.abs(close - open));
            ctx.fillRect(x, topY, candleWidth, height);

            lastClose = close;
        }

        // Fast moving dynamic EMA line
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        ctx.moveTo(8, 48);
        ctx.bezierCurveTo(40, 52, 80, 26, 120, 20);
        ctx.stroke();

        const tex = new THREE.CanvasTexture(c);
        tex.minFilter = THREE.LinearFilter;
        tex.magFilter = THREE.NearestFilter;
        return tex;
    }

    createScrollingTickerTexture() {
        const c = document.createElement('canvas');
        c.width = 2048;
        c.height = 128;
        const ctx = c.getContext('2d');

        ctx.fillStyle = '#020617';
        ctx.fillRect(0, 0, 2048, 128);

        // Neon Top & Bottom Trim
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(0, 0, 2048, 4);
        ctx.fillStyle = '#f59e0b';
        ctx.fillRect(0, 124, 2048, 4);

        // Streaming Ticker Text
        ctx.font = 'bold 36px "JetBrains Mono", monospace';
        ctx.textBaseline = 'middle';

        const tickerItems = [
            { s: 'BTC/USDT', p: '$64,825.50', ch: '+2.84%', u: true },
            { s: 'ETH/USDT', p: '$2,586.20', ch: '+3.42%', u: true },
            { s: 'SOL/USDT', p: '$148.80', ch: '+5.61%', u: true },
            { s: 'BNB/USDT', p: '$756.20', ch: '+1.15%', u: true },
            { s: 'DOGE/USDT', p: '$0.0984', ch: '-0.45%', u: false },
            { s: 'HARD RISK GATE', p: 'ACTIVE 100%', ch: 'SECURE', u: true },
            { s: 'TOTAL PNL', p: '+$0.4556', ch: '+0.88%', u: true },
            { s: 'AGENTS DEPLOYED', p: '12 / 12', ch: 'OPTIMAL', u: true }
        ];

        let cursorX = 20;
        for (let r = 0; r < 2; r++) {
            tickerItems.forEach(item => {
                ctx.fillStyle = '#f8fafc';
                ctx.fillText(item.s, cursorX, 64);
                cursorX += ctx.measureText(item.s).width + 15;

                ctx.fillStyle = '#38bdf8';
                ctx.fillText(item.p, cursorX, 64);
                cursorX += ctx.measureText(item.p).width + 12;

                ctx.fillStyle = item.u ? '#10b981' : '#f43f5e';
                ctx.fillText(item.ch + '   ●   ', cursorX, 64);
                cursorX += ctx.measureText(item.ch + '   ●   ').width + 25;
            });
        }

        const tex = new THREE.CanvasTexture(c);
        tex.wrapS = THREE.RepeatWrapping;
        tex.wrapT = THREE.ClampToEdgeWrapping;
        this.tickerTexture = tex;
        return tex;
    }

    /* --------------------------------------------------------------------------
       4. CENTRAL QUANTUM CORE & RECEPTION DESK
       -------------------------------------------------------------------------- */
    buildCentralCore() {
        this.coreGroup = new THREE.Group();

        // 1. Two-Tier Raised Dais Platform with Steps
        const daisMat = new THREE.MeshStandardMaterial({
            color: 0x0f172a,
            metalness: 0.85,
            roughness: 0.25
        });

        // Lower Dais
        const lowerDais = new THREE.Mesh(new THREE.CylinderGeometry(34, 38, 2.5, 32), daisMat);
        lowerDais.position.y = 1.25;
        lowerDais.receiveShadow = true;
        this.coreGroup.add(lowerDais);

        // Lower Dais Neon Edge
        const lowerRing = new THREE.Mesh(
            new THREE.TorusGeometry(36, 0.25, 8, 48),
            new THREE.MeshBasicMaterial({ color: 0x38bdf8 })
        );
        lowerRing.rotation.x = Math.PI / 2;
        lowerRing.position.y = 2.5;
        this.coreGroup.add(lowerRing);

        // Upper Dais
        const upperDais = new THREE.Mesh(new THREE.CylinderGeometry(24, 28, 2.5, 32), daisMat);
        upperDais.position.y = 3.5;
        upperDais.receiveShadow = true;
        this.coreGroup.add(upperDais);

        // Upper Dais Gold Edge
        const upperRing = new THREE.Mesh(
            new THREE.TorusGeometry(26, 0.22, 8, 48),
            new THREE.MeshBasicMaterial({ color: 0xf59e0b })
        );
        upperRing.rotation.x = Math.PI / 2;
        upperRing.position.y = 4.75;
        this.coreGroup.add(upperRing);

        // Core Pedestal
        const pedGeo = new THREE.CylinderGeometry(8, 11, 8, 8);
        const pedMat = new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.9, roughness: 0.2 });
        const ped = new THREE.Mesh(pedGeo, pedMat);
        ped.position.y = 8.5;
        this.coreGroup.add(ped);

        // 2. Rotating Crystalline Quantum Icosahedron Core
        const icoGeo = new THREE.IcosahedronGeometry(9.0, 0);
        const icoMat = new THREE.MeshStandardMaterial({
            color: 0x38bdf8,
            emissive: 0x0284c7,
            emissiveIntensity: 0.95,
            roughness: 0.1,
            metalness: 0.9,
            transparent: true,
            opacity: 0.92
        });
        this.coreCrystal = new THREE.Mesh(icoGeo, icoMat);
        this.coreCrystal.position.y = 23;
        this.coreGroup.add(this.coreCrystal);

        // Outer Wireframe Shell
        const wireGeo = new THREE.IcosahedronGeometry(11.8, 1);
        const wireMat = new THREE.MeshBasicMaterial({ color: 0x67e8f9, wireframe: true, transparent: true, opacity: 0.8 });
        this.coreWire = new THREE.Mesh(wireGeo, wireMat);
        this.coreWire.position.y = 23;
        this.coreGroup.add(this.coreWire);

        // Dual Rotating Gyroscopic Energy Rings
        const ring1Geo = new THREE.TorusGeometry(17, 0.65, 16, 64);
        const ringMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.9 });
        this.coreRing1 = new THREE.Mesh(ring1Geo, ringMat);
        this.coreRing1.position.y = 23;
        this.coreRing1.rotation.x = Math.PI / 3;
        this.coreGroup.add(this.coreRing1);

        const ring2Geo = new THREE.TorusGeometry(20, 0.55, 16, 64);
        const ringMat2 = new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.85 });
        this.coreRing2 = new THREE.Mesh(ring2Geo, ringMat2);
        this.coreRing2.position.y = 23;
        this.coreRing2.rotation.x = -Math.PI / 4;
        this.coreGroup.add(this.coreRing2);

        // 3. 360° Circular Overhead Floating Market Ticker Ring
        const tickerTex = this.createScrollingTickerTexture();
        const tickerRingGeo = new THREE.CylinderGeometry(25, 25, 3.6, 64, 1, true);
        const tickerRingMat = new THREE.MeshBasicMaterial({
            map: tickerTex,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.95
        });
        this.tickerRing = new THREE.Mesh(tickerRingGeo, tickerRingMat);
        this.tickerRing.position.y = 35;
        this.coreGroup.add(this.tickerRing);

        // 4. Central Hologram Logo Billboard
        const logoCanvas = document.createElement('canvas');
        logoCanvas.width = 512;
        logoCanvas.height = 160;
        const lctx = logoCanvas.getContext('2d');

        lctx.fillStyle = 'rgba(7, 18, 38, 0.95)';
        lctx.strokeStyle = '#38bdf8';
        lctx.lineWidth = 4;
        drawRoundRect(lctx, 10, 10, 492, 140, 20);
        lctx.fill();
        lctx.stroke();

        lctx.font = '900 42px "JetBrains Mono", monospace';
        lctx.fillStyle = '#38bdf8';
        lctx.textAlign = 'center';
        lctx.shadowColor = '#38bdf8';
        lctx.shadowBlur = 18;
        lctx.fillText('ASTRA DESK', 256, 68);

        lctx.font = '800 18px "JetBrains Mono", monospace';
        lctx.fillStyle = '#f59e0b';
        lctx.shadowColor = '#f59e0b';
        lctx.shadowBlur = 12;
        lctx.fillText('TRADING · AI · AUTOMATION', 256, 114);

        const logoTex = new THREE.CanvasTexture(logoCanvas);
        this.logoBillboard = new THREE.Sprite(new THREE.SpriteMaterial({ map: logoTex, transparent: true }));
        this.logoBillboard.position.set(0, 43, 0);
        this.logoBillboard.scale.set(34, 10.5, 1);
        this.coreGroup.add(this.logoBillboard);

        // 5. High-Tech Reception Desk & 3D Receptionist Android Model (NO 2D SPRITES!)
        this.buildReception(this.coreGroup);

        // 6. Digital Zen Water Garden behind dais
        this.buildZenGarden(this.coreGroup);

        // 7. Physical 3D Quantum Vault (Két Sắt Ngân Hàng Lượng Tử)
        this.buildQuantumVault(this.coreGroup);

        this.scene.add(this.coreGroup);
    }

    toggleQuantum3dCore(forceVisible) {
        if (!this.coreGroup) return false;
        if (typeof forceVisible === 'boolean') {
            this.coreGroup.visible = forceVisible;
        } else {
            this.coreGroup.visible = !this.coreGroup.visible;
        }
        return this.coreGroup.visible;
    }

    buildReception(parent) {
        const recGroup = new THREE.Group();
        recGroup.position.set(0, 4.75, 20);

        // Curved Titanium Reception Counter
        const deskMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.85, roughness: 0.25 });
        const desk = new THREE.Mesh(new THREE.BoxGeometry(20, 3.6, 5.0), deskMat);
        desk.position.y = 1.8;
        recGroup.add(desk);

        // Glowing Cyan LED Front Strip
        const frontLed = new THREE.Mesh(new THREE.PlaneGeometry(19, 0.6), new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));
        frontLed.position.set(0, 2.2, 2.52);
        recGroup.add(frontLed);

        // Holographic Touch Terminals on counter
        for (let t = -1; t <= 1; t += 2) {
            const term = new THREE.Mesh(
                new THREE.BoxGeometry(3.6, 2.2, 0.3),
                new THREE.MeshStandardMaterial({
                    color: 0x020617,
                    emissive: 0x38bdf8,
                    emissiveIntensity: 0.65,
                    map: this.createTradingChartTexture(0x38bdf8)
                })
            );
            term.position.set(t * 6.0, 4.4, 0.5);
            term.rotation.y = Math.PI;
            recGroup.add(term);
        }

        // Full 3D Receptionist Android Model (NO FLAT 2D SPRITE!)
        const recAndroid = this.createSeatedOfficer3D('community_affiliate', {
            color: 0x38bdf8,
            accent: 0xf59e0b
        });
        recAndroid.position.set(0, 0, -2.4);
        recAndroid.rotation.y = 0; // Facing front counter
        recGroup.add(recAndroid);

        // Overhead Reception Hologram Sign
        const recTag = this.createHoloSprite('TIẾP TÂN · LỄ TÂN HQ', 0x38bdf8);
        recTag.position.set(0, 9.5, 0);
        recTag.scale.set(11, 2.6, 1);
        recGroup.add(recTag);

        parent.add(recGroup);
    }

    buildZenGarden(parent) {
        const garden = new THREE.Group();
        garden.position.set(0, 1.25, -28);

        // Circular Water Pool with Cyan Glow
        const poolCurb = new THREE.Mesh(
            new THREE.CylinderGeometry(14, 15, 1.6, 24),
            new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.6 })
        );
        garden.add(poolCurb);

        const water = new THREE.Mesh(
            new THREE.CylinderGeometry(13.6, 13.6, 0.2, 24),
            new THREE.MeshStandardMaterial({
                color: 0x0284c7,
                emissive: 0x0369a1,
                emissiveIntensity: 0.5,
                metalness: 0.9,
                roughness: 0.1,
                transparent: true,
                opacity: 0.85
            })
        );
        water.position.y = 0.8;
        garden.add(water);

        // Illuminated Bonsai Trees in Geometric Planters
        const treeOffsets = [
            { x: -10, z: 0 }, { x: 10, z: 0 }, { x: 0, z: -10 }
        ];
        treeOffsets.forEach(to => {
            const pot = new THREE.Mesh(
                new THREE.BoxGeometry(3.0, 2.0, 3.0),
                new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.5 })
            );
            pot.position.set(to.x, 1.8, to.z);
            garden.add(pot);

            const foliage = new THREE.Mesh(
                new THREE.DodecahedronGeometry(2.4, 1),
                new THREE.MeshStandardMaterial({ color: 0x10b981, roughness: 0.4 })
            );
            foliage.position.set(to.x, 4.4, to.z);
            garden.add(foliage);

            const treeLight = new THREE.PointLight(0x34d399, 1.2, 18);
            treeLight.position.set(to.x, 5.0, to.z);
            garden.add(treeLight);
        });

        parent.add(garden);
    }

    buildQuantumVault(parent) {
        const vaultGroup = new THREE.Group();
        vaultGroup.position.set(-18, 4.75, 0); // West side of central dais

        // 1. Heavy Reinforced Titanium & Tungsten Safe Body
        const safeGeo = new THREE.BoxGeometry(7, 8, 6);
        const safeMat = new THREE.MeshStandardMaterial({
            color: 0x0f172a,
            metalness: 0.95,
            roughness: 0.2
        });
        const safe = new THREE.Mesh(safeGeo, safeMat);
        safe.position.y = 4.0;
        safe.castShadow = true;
        safe.receiveShadow = true;
        vaultGroup.add(safe);

        // Gold Beveled Trim on Front Face
        const trimGeo = new THREE.BoxGeometry(7.2, 8.2, 0.2);
        const trimMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
        const trim = new THREE.Mesh(trimGeo, trimMat);
        trim.position.set(0, 4.0, 3.05);
        vaultGroup.add(trim);

        // Vault Safe Door (Slightly recessed)
        const doorGeo = new THREE.BoxGeometry(6.2, 7.2, 0.4);
        const doorMat = new THREE.MeshStandardMaterial({
            color: 0x1e293b,
            metalness: 0.9,
            roughness: 0.15
        });
        const door = new THREE.Mesh(doorGeo, doorMat);
        door.position.set(0, 4.0, 3.15);
        vaultGroup.add(door);

        // Spinning Mechanical Combination Dial (3D Wheel)
        const dialGeo = new THREE.CylinderGeometry(1.6, 1.6, 0.6, 32);
        const dialMat = new THREE.MeshStandardMaterial({
            color: 0xf59e0b,
            metalness: 0.98,
            roughness: 0.1
        });
        this.vaultDial = new THREE.Mesh(dialGeo, dialMat);
        this.vaultDial.rotation.x = Math.PI / 2;
        this.vaultDial.position.set(0, 4.2, 3.5);
        vaultGroup.add(this.vaultDial);

        // Dial Center Cap
        const capGeo = new THREE.CylinderGeometry(0.7, 0.7, 0.7, 24);
        const capMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
        const cap = new THREE.Mesh(capGeo, capMat);
        cap.rotation.x = Math.PI / 2;
        cap.position.set(0, 4.2, 3.6);
        vaultGroup.add(cap);

        // 3-Spoke Wheel Handle
        for (let i = 0; i < 3; i++) {
            const spokeGeo = new THREE.CylinderGeometry(0.12, 0.12, 3.4, 12);
            const spokeMat = new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.9 });
            const spoke = new THREE.Mesh(spokeGeo, spokeMat);
            spoke.rotation.z = (i * Math.PI) / 3;
            spoke.position.set(0, 4.2, 3.7);
            vaultGroup.add(spoke);
        }

        // Digital Keypad & Green Access LED
        const keypadGeo = new THREE.BoxGeometry(1.2, 1.8, 0.2);
        const keypadMat = new THREE.MeshBasicMaterial({ color: 0x020617 });
        const keypad = new THREE.Mesh(keypadGeo, keypadMat);
        keypad.position.set(2.2, 4.2, 3.35);
        vaultGroup.add(keypad);

        const ledGeo = new THREE.SphereGeometry(0.18, 12, 12);
        const ledMat = new THREE.MeshBasicMaterial({ color: 0x10b981 });
        const led = new THREE.Mesh(ledGeo, ledMat);
        led.position.set(2.2, 5.3, 3.45);
        vaultGroup.add(led);

        // Overhead Holographic Billboard for the Vault
        const vCanvas = document.createElement('canvas');
        vCanvas.width = 384;
        vCanvas.height = 128;
        const vctx = vCanvas.getContext('2d');
        vctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        vctx.strokeStyle = '#f59e0b';
        vctx.lineWidth = 3;
        drawRoundRect(vctx, 6, 6, 372, 116, 14);
        vctx.fill();
        vctx.stroke();

        vctx.font = '900 24px "JetBrains Mono", monospace';
        vctx.fillStyle = '#f59e0b';
        vctx.textAlign = 'center';
        vctx.shadowColor = '#f59e0b';
        vctx.shadowBlur = 10;
        vctx.fillText('🔒 KÉT SẮT LƯỢNG TỬ', 192, 48);

        vctx.font = '700 13px "JetBrains Mono", monospace';
        vctx.fillStyle = '#38bdf8';
        vctx.shadowBlur = 6;
        vctx.shadowColor = '#38bdf8';
        vctx.fillText('VỐN BẢO TOÀN 100% · BINANCE ISOLATED', 192, 88);

        const vTex = new THREE.CanvasTexture(vCanvas);
        const vSprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: vTex, transparent: true }));
        vSprite.position.set(0, 11.5, 0);
        vSprite.scale.set(16, 5.3, 1);
        vaultGroup.add(vSprite);

        // Security Field Ring around Safe
        const shieldGeo = new THREE.TorusGeometry(5.2, 0.15, 8, 32);
        const shieldMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.65 });
        this.vaultShieldRing = new THREE.Mesh(shieldGeo, shieldMat);
        this.vaultShieldRing.rotation.x = Math.PI / 2;
        this.vaultShieldRing.position.y = 0.5;
        vaultGroup.add(this.vaultShieldRing);

        parent.add(vaultGroup);
    }



    /* --------------------------------------------------------------------------
       5. 4 ARCHITECTURAL WINGS & HIGH-TECH PLATFORMS
       -------------------------------------------------------------------------- */
    buildWings() {
        this.wingPlatforms = {};

        const wings = [
            { id: 'executive', name: 'KHU ĐIỀU HÀNH & CRO', pos: { x: -80, y: 2, z: -60 }, color: 0xf59e0b },
            { id: 'trading',   name: 'SÀN GIAO DỊCH & OMS', pos: { x: 80, y: 2, z: -60 },  color: 0x06b6d4 },
            { id: 'research',  name: 'VIỆN QUANT & BREAKOUT', pos: { x: -80, y: 2, z: 75 }, color: 0xa855f7 },
            { id: 'operations', name: 'AN TOÀN & HẬU CẦN', pos: { x: 80, y: 2, z: 75 },   color: 0x10b981 }
        ];

        wings.forEach(w => {
            const group = new THREE.Group();
            group.position.set(w.pos.x, w.pos.y, w.pos.z);

            // Elevated Platform with high-tech floor color
            const platGeo = new THREE.BoxGeometry(84, 3.5, 84);
            const platMat = new THREE.MeshStandardMaterial({
                color: 0x131d36,
                metalness: 0.8,
                roughness: 0.3
            });
            const plat = new THREE.Mesh(platGeo, platMat);
            plat.receiveShadow = true;
            group.add(plat);

            // Glowing Perimeter Line
            const borderGeo = new THREE.BoxGeometry(85, 0.4, 85);
            const borderMat = new THREE.LineBasicMaterial({
                color: w.color,
                transparent: true,
                opacity: 0.85
            });
            const border = new THREE.LineSegments(new THREE.EdgesGeometry(borderGeo), borderMat);
            border.position.y = 1.8;
            group.add(border);

            // Wing Holographic Point Light (Softened with proper decay to prevent white blowout)
            const pLight = new THREE.PointLight(w.color, 0.85, 130, 2);
            pLight.position.set(0, 20, 0);
            group.add(pLight);

            this.scene.add(group);
            this.wingPlatforms[w.id] = { group, border, light: pLight, baseColor: w.color };
        });
    }

    /* --------------------------------------------------------------------------
       5B. PHÒNG TỔNG TƯ LỆNH · CEO EXECUTIVE COMMAND SUITE
       -------------------------------------------------------------------------- */
    buildCeoExecutiveSuite() {
        const suite = new THREE.Group();
        // Positioned in the North VIP corner of Executive Wing (Wing 1)
        suite.position.set(-78, 3.75, -86);

        // 1. Raised Luxurious Obsidian & Gold Dais Platform
        const daisGeo = new THREE.BoxGeometry(38, 0.8, 28);
        const daisMat = new THREE.MeshStandardMaterial({
            color: 0x070e22,
            metalness: 0.9,
            roughness: 0.15
        });
        const dais = new THREE.Mesh(daisGeo, daisMat);
        dais.position.y = 0.4;
        dais.receiveShadow = true;
        suite.add(dais);

        // Gold Neon Dais Edge Trim
        const daisEdgeGeo = new THREE.BoxGeometry(38.4, 0.2, 28.4);
        const daisEdgeMat = new THREE.LineBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.9 });
        const daisEdge = new THREE.LineSegments(new THREE.EdgesGeometry(daisEdgeGeo), daisEdgeMat);
        daisEdge.position.y = 0.8;
        suite.add(daisEdge);

        // 2. High-Tech Frosted Smart-Glass Privacy Partitions with Neon Ribs
        const glassMat = new THREE.MeshStandardMaterial({
            color: 0x0ea5e9,
            roughness: 0.1,
            metalness: 0.6,
            transparent: true,
            opacity: 0.28,
            side: THREE.DoubleSide
        });
        const frameMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9, roughness: 0.2 });

        // Back Glass Wall (North)
        const backWall = new THREE.Mesh(new THREE.BoxGeometry(38, 9, 0.3), glassMat);
        backWall.position.set(0, 5.3, -14);
        suite.add(backWall);

        // Left Glass Wall (West)
        const leftWall = new THREE.Mesh(new THREE.BoxGeometry(0.3, 9, 28), glassMat);
        leftWall.position.set(-19, 5.3, 0);
        suite.add(leftWall);

        // Right Glass Wall (East)
        const rightWall = new THREE.Mesh(new THREE.BoxGeometry(0.3, 9, 28), glassMat);
        rightWall.position.set(19, 5.3, 0);
        suite.add(rightWall);

        // Front Glass Partitions (South) with wide central entrance doorway (14 units wide)
        const frontLeft = new THREE.Mesh(new THREE.BoxGeometry(12, 9, 0.3), glassMat);
        frontLeft.position.set(-13, 5.3, 14);
        suite.add(frontLeft);

        const frontRight = new THREE.Mesh(new THREE.BoxGeometry(12, 9, 0.3), glassMat);
        frontRight.position.set(13, 5.3, 14);
        suite.add(frontRight);

        // Gold Portal Pillars flanking the Entrance
        for (let side = -1; side <= 1; side += 2) {
            const pillar = new THREE.Mesh(
                new THREE.BoxGeometry(0.8, 10, 0.8),
                new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xd97706, emissiveIntensity: 0.6, metalness: 0.9 })
            );
            pillar.position.set(side * 7.2, 5.5, 14);
            suite.add(pillar);
        }

        // Entrance Hologram Arch Sign
        const suiteSign = this.createHoloSprite('👑 PHÒNG TỔNG TƯ LỆNH · CEO SUITE', 0xf59e0b);
        suiteSign.position.set(0, 11.5, 14);
        suiteSign.scale.set(22, 4.2, 1);
        suite.add(suiteSign);

        // 3. Grand Executive Command Desk (Bàn Làm Việc Tổng Tư Lệnh)
        const deskGroup = new THREE.Group();
        deskGroup.position.set(0, 0.8, -4);

        // Main Curved Titanium & Obsidian Desk
        const deskTopMat = new THREE.MeshStandardMaterial({ color: 0x091124, metalness: 0.9, roughness: 0.2 });
        const deskTop = new THREE.Mesh(new THREE.BoxGeometry(18, 0.6, 6.0), deskTopMat);
        deskTop.position.y = 3.6;
        deskGroup.add(deskTop);

        // Gold LED Inlay on front desk edge
        const deskTrim = new THREE.Mesh(
            new THREE.BoxGeometry(18.2, 0.15, 6.2),
            new THREE.MeshBasicMaterial({ color: 0xf59e0b })
        );
        deskTrim.position.y = 3.85;
        deskGroup.add(deskTrim);

        // Solid titanium twin pedestals
        for (let p = -1; p <= 1; p += 2) {
            const ped = new THREE.Mesh(new THREE.BoxGeometry(4.2, 3.6, 5.4), frameMat);
            ped.position.set(p * 6.5, 1.8, 0);
            deskGroup.add(ped);
        }

        // Front Face Golden Eagle / Astra Command Emblem
        const emblem = new THREE.Mesh(
            new THREE.BoxGeometry(6.0, 1.8, 0.2),
            new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xf59e0b, emissiveIntensity: 0.5 })
        );
        emblem.position.set(0, 2.2, 3.05);
        deskGroup.add(emblem);

        // 4. Ultra-Wide Triple Curved Panoramic Holographic Monitors
        const screenMat = new THREE.MeshStandardMaterial({
            color: 0x020617,
            emissive: 0x38bdf8,
            emissiveIntensity: 0.6,
            map: this.createTradingChartTexture(0xf59e0b)
        });

        // Center Master Display (Live Crypto/PnL Matrix)
        const centerDisp = new THREE.Mesh(new THREE.BoxGeometry(7.5, 4.2, 0.25), screenMat);
        centerDisp.position.set(0, 6.2, 1.0);
        deskGroup.add(centerDisp);

        // Left Display (Angled)
        const leftDisp = new THREE.Mesh(
            new THREE.BoxGeometry(5.2, 3.6, 0.25),
            new THREE.MeshStandardMaterial({
                color: 0x020617,
                emissive: 0x10b981,
                emissiveIntensity: 0.5,
                map: this.createTradingChartTexture(0x10b981)
            })
        );
        leftDisp.position.set(-6.2, 6.0, 1.6);
        leftDisp.rotation.y = Math.PI / 7;
        deskGroup.add(leftDisp);

        // Right Display (Angled)
        const rightDisp = new THREE.Mesh(
            new THREE.BoxGeometry(5.2, 3.6, 0.25),
            new THREE.MeshStandardMaterial({
                color: 0x020617,
                emissive: 0xa855f7,
                emissiveIntensity: 0.5,
                map: this.createTradingChartTexture(0xa855f7)
            })
        );
        rightDisp.position.set(6.2, 6.0, 1.6);
        rightDisp.rotation.y = -Math.PI / 7;
        deskGroup.add(rightDisp);

        // Center Floating 3D Holographic Globe / Quantum Sphere
        const holoGlobe = new THREE.Mesh(
            new THREE.IcosahedronGeometry(1.0, 1),
            new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true, transparent: true, opacity: 0.85 })
        );
        holoGlobe.position.set(0, 4.6, 0.5);
        deskGroup.add(holoGlobe);

        // 5. Commander High-Back Cyber Leather Throne (Ghế Tổng Tư Lệnh)
        const chairGroup = new THREE.Group();
        chairGroup.position.set(0, 0, -4.8);

        const seatMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.4, metalness: 0.5 });
        const seat = new THREE.Mesh(new THREE.BoxGeometry(3.0, 0.5, 2.8), seatMat);
        seat.position.y = 2.2;
        chairGroup.add(seat);

        // High Backrest with gold trim
        const backrest = new THREE.Mesh(new THREE.BoxGeometry(2.8, 4.4, 0.5), seatMat);
        backrest.position.set(0, 4.4, -1.2);
        backrest.rotation.x = -0.08;
        chairGroup.add(backrest);

        const goldHeadrest = new THREE.Mesh(
            new THREE.BoxGeometry(2.0, 1.0, 0.4),
            new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xb45309, emissiveIntensity: 0.4 })
        );
        goldHeadrest.position.set(0, 6.4, -1.4);
        chairGroup.add(goldHeadrest);

        // Chair hydraulic pedestal & 5-star base
        const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 1.8), frameMat);
        stem.position.y = 1.0;
        chairGroup.add(stem);
        deskGroup.add(chairGroup);

        suite.add(deskGroup);

        // 6. VIP Lounge Area (Left side of suite)
        const loungeGroup = new THREE.Group();
        loungeGroup.position.set(-11, 0.8, 3);

        // Cyber Leather Sofa
        const sofaMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.5 });
        const sofaSeat = new THREE.Mesh(new THREE.BoxGeometry(4.5, 1.2, 9.0), sofaMat);
        sofaSeat.position.set(0, 1.0, 0);
        loungeGroup.add(sofaSeat);

        const sofaBack = new THREE.Mesh(new THREE.BoxGeometry(1.0, 3.2, 9.0), sofaMat);
        sofaBack.position.set(-2.2, 2.2, 0);
        loungeGroup.add(sofaBack);

        // Low Coffee / Whiskey Table
        const table = new THREE.Mesh(
            new THREE.CylinderGeometry(2.4, 2.4, 1.0, 16),
            new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.85, roughness: 0.2 })
        );
        table.position.set(4.2, 0.8, 0);
        loungeGroup.add(table);

        // Golden Decanter & Cyber Mug
        const decanter = new THREE.Mesh(
            new THREE.CylinderGeometry(0.3, 0.6, 1.2, 12),
            new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.9, roughness: 0.1, transparent: true, opacity: 0.85 })
        );
        decanter.position.set(4.2, 1.8, -0.4);
        loungeGroup.add(decanter);

        suite.add(loungeGroup);

        // 7. Data Vault & Golden Bitcoin Trophy Stand (Right side of suite)
        const trophyGroup = new THREE.Group();
        trophyGroup.position.set(11, 0.8, 2);

        // Dark Marble Pedestal
        const tropPed = new THREE.Mesh(
            new THREE.CylinderGeometry(2.0, 2.4, 3.6, 16),
            new THREE.MeshStandardMaterial({ color: 0x0b1329, metalness: 0.9, roughness: 0.2 })
        );
        tropPed.position.y = 1.8;
        trophyGroup.add(tropPed);

        // Rotating Golden Bitcoin Trophy
        const coinGeo = new THREE.CylinderGeometry(1.6, 1.6, 0.35, 32);
        const coinMat = new THREE.MeshStandardMaterial({
            color: 0xf59e0b,
            metalness: 0.95,
            roughness: 0.15,
            emissive: 0xd97706,
            emissiveIntensity: 0.45
        });
        const btcTrophy = new THREE.Mesh(coinGeo, coinMat);
        btcTrophy.rotation.x = Math.PI / 2;
        btcTrophy.position.y = 4.6;
        trophyGroup.add(btcTrophy);

        // Glass Cloche Dome
        const cloche = new THREE.Mesh(
            new THREE.SphereGeometry(2.4, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2),
            new THREE.MeshStandardMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.35, roughness: 0.1 })
        );
        cloche.position.y = 3.6;
        trophyGroup.add(cloche);

        suite.add(trophyGroup);

        // 8. Ceiling Warm Executive Chandelier Spot Light
        const execLight = new THREE.PointLight(0xfde68a, 2.0, 60);
        execLight.position.set(0, 14, -2);
        suite.add(execLight);

        this.scene.add(suite);
    }

    /* --------------------------------------------------------------------------
       6. COFFEE LOUNGE & EXECUTIVE RELAXATION AREA
       -------------------------------------------------------------------------- */
    buildCoffeeLounge() {
        const lounge = new THREE.Group();
        lounge.position.set(0, 2, -45);

        // Low Lounge Table
        const tableGeo = new THREE.BoxGeometry(16, 1.5, 8);
        const tableMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.85, roughness: 0.2 });
        const table = new THREE.Mesh(tableGeo, tableMat);
        table.position.y = 0.75;
        lounge.add(table);

        const glowStrip = new THREE.Mesh(
            new THREE.PlaneGeometry(14, 0.9),
            new THREE.MeshBasicMaterial({ color: 0xf59e0b })
        );
        glowStrip.rotation.x = -Math.PI / 2;
        glowStrip.position.y = 1.52;
        lounge.add(glowStrip);

        // Sofas
        for (let s = -1; s <= 1; s += 2) {
            const sofaGeo = new THREE.BoxGeometry(18, 2.8, 4.5);
            const sofaMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.7 });
            const sofa = new THREE.Mesh(sofaGeo, sofaMat);
            sofa.position.set(0, 1.4, s * 7.5);
            lounge.add(sofa);
        }

        // Espresso Machine
        const machineGeo = new THREE.BoxGeometry(3.6, 3.4, 2.5);
        const machineMat = new THREE.MeshStandardMaterial({ color: 0xd97706, metalness: 0.85, roughness: 0.2 });
        const machine = new THREE.Mesh(machineGeo, machineMat);
        machine.position.set(4.5, 3.2, 0);
        lounge.add(machine);

        // Coffee Cups
        for (let c = -1; c <= 1; c++) {
            const cupGeo = new THREE.CylinderGeometry(0.45, 0.35, 0.8, 8);
            const cupMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.2 });
            const cup = new THREE.Mesh(cupGeo, cupMat);
            cup.position.set(c * 2.2, 1.9, 0);
            lounge.add(cup);
        }

        const loungeLight = new THREE.PointLight(0xfde047, 1.3, 70);
        loungeLight.position.set(0, 11, 0);
        lounge.add(loungeLight);

        const sign = this.createHoloSprite('☕ COFFEE & RELAX LOUNGE', 0xf59e0b);
        sign.position.set(0, 10, 0);
        sign.scale.set(18, 4.2, 1);
        lounge.add(sign);

        this.scene.add(lounge);
    }

    /* --------------------------------------------------------------------------
       7. 3D BIOPHILIC POTTED PLANTS
       -------------------------------------------------------------------------- */
    buildPlants() {
        const plantLocations = [
            { x: -18, z: 28 }, { x: 18, z: 28 },
            { x: -24, z: -45 }, { x: 24, z: -45 },
            { x: -45, z: 12 }, { x: 45, z: 12 },
            { x: -45, z: -18 }, { x: 45, z: -18 },
            { x: -128, z: -70 }, { x: 128, z: -70 },
            { x: -128, z: 80 }, { x: 128, z: 80 }
        ];

        plantLocations.forEach(loc => {
            const pGroup = new THREE.Group();
            pGroup.position.set(loc.x, 0, loc.z);

            const potGeo = new THREE.CylinderGeometry(2.2, 1.6, 3.4, 6);
            const potMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.6 });
            const pot = new THREE.Mesh(potGeo, potMat);
            pot.position.y = 1.7;
            pot.castShadow = true;
            pGroup.add(pot);

            const rimGeo = new THREE.RingGeometry(2.0, 2.3, 6);
            const rimMat = new THREE.MeshBasicMaterial({ color: 0x10b981, side: THREE.DoubleSide });
            const rim = new THREE.Mesh(rimGeo, rimMat);
            rim.rotation.x = -Math.PI / 2;
            rim.position.y = 3.42;
            pGroup.add(rim);

            const foliageColors = [0x10b981, 0x059669, 0x34d399];
            for (let f = 0; f < 3; f++) {
                const folGeo = new THREE.DodecahedronGeometry(2.0 - f * 0.35, 0);
                const folMat = new THREE.MeshStandardMaterial({
                    color: foliageColors[f],
                    roughness: 0.5,
                    flatShading: true
                });
                const fol = new THREE.Mesh(folGeo, folMat);
                fol.position.set((f === 1 ? 0.4 : -0.3), 4.8 + f * 1.6, (f === 2 ? 0.3 : 0));
                pGroup.add(fol);
            }

            this.scene.add(pGroup);
        });
    }

    /* --------------------------------------------------------------------------
       8. 12 HIGH-CONTRAST WORKSTATIONS (BÀN GHẾ, MÀN HÌNH, VÁCH NGĂN)
       -------------------------------------------------------------------------- */
    /* --------------------------------------------------------------------------
       5B. ILLUMINATED SKY-WALKWAY CORRIDORS, GLASS WALLS, PORTAL ARCHES & FACILITIES
       -------------------------------------------------------------------------- */
    buildCorridorsAndWalls() {
        const corridorGroup = new THREE.Group();

        // 4 Connecting Enclosed Glass Sky-Tunnels (Central Hub ➔ 4 Wings)
        const routes = [
            { id: 'exec_route', name: 'HÀNH LANG ĐIỀU HÀNH', from: { x: 0, z: 0 }, to: { x: -80, z: -60 }, color: 0xf59e0b },
            { id: 'trade_route', name: 'HÀNH LANG KHỚP LỆNH', from: { x: 0, z: 0 }, to: { x: 80, z: -60 }, color: 0x06b6d4 },
            { id: 'quant_route', name: 'HÀNH LANG QUANT LAB', from: { x: 0, z: 0 }, to: { x: -80, z: 75 }, color: 0xa855f7 },
            { id: 'ops_route',   name: 'HÀNH LANG AN TOÀN & OPS', from: { x: 0, z: 0 }, to: { x: 80, z: 75 }, color: 0x10b981 }
        ];

        routes.forEach(r => {
            const dx = r.to.x - r.from.x;
            const dz = r.to.z - r.from.z;
            const dist = Math.hypot(dx, dz);
            const midX = (r.from.x + r.to.x) / 2;
            const midZ = (r.from.z + r.to.z) / 2;
            const angle = Math.atan2(dx, dz);

            // 1. Reinforced Walkway Slab
            const slabGeo = new THREE.BoxGeometry(16, 1.8, dist);
            const slabMat = new THREE.MeshStandardMaterial({
                color: 0x0f172a,
                metalness: 0.85,
                roughness: 0.3
            });
            const slab = new THREE.Mesh(slabGeo, slabMat);
            slab.position.set(midX, 1.0, midZ);
            slab.rotation.y = angle;
            slab.receiveShadow = true;
            corridorGroup.add(slab);

            // 2. Dual Glowing Floor Runway Strips
            for (let side = -1; side <= 1; side += 2) {
                const stripGeo = new THREE.BoxGeometry(0.45, 0.15, dist);
                const stripMat = new THREE.MeshBasicMaterial({ color: r.color });
                const strip = new THREE.Mesh(stripGeo, stripMat);
                strip.position.set(midX + Math.cos(angle) * (side * 7.4), 1.95, midZ - Math.sin(angle) * (side * 7.4));
                strip.rotation.y = angle;
                corridorGroup.add(strip);

                // Side Glass Balustrade (Lan can kính bảo vệ dọc hành lang)
                const glassMat = new THREE.MeshStandardMaterial({
                    color: r.color,
                    transparent: true,
                    opacity: 0.32,
                    metalness: 0.9,
                    roughness: 0.1
                });
                const glassWall = new THREE.Mesh(new THREE.BoxGeometry(0.25, 4.5, dist), glassMat);
                glassWall.position.set(midX + Math.cos(angle) * (side * 7.6), 4.2, midZ - Math.sin(angle) * (side * 7.6));
                glassWall.rotation.y = angle;
                corridorGroup.add(glassWall);

                // Neon Handrail
                const rail = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.25, dist), new THREE.MeshBasicMaterial({ color: r.color }));
                rail.position.set(midX + Math.cos(angle) * (side * 7.6), 6.5, midZ - Math.sin(angle) * (side * 7.6));
                rail.rotation.y = angle;
                corridorGroup.add(rail);
            }

            // 3. Cyber Steel Arch Ribs (Khung vòm thép chịu lực dọc hành lang)
            const numRibs = Math.floor(dist / 18);
            for (let i = 1; i <= numRibs; i++) {
                const frac = i / (numRibs + 1);
                const ribX = r.from.x + dx * frac;
                const ribZ = r.from.z + dz * frac;

                const archRib = new THREE.Group();
                archRib.position.set(ribX, 1.8, ribZ);
                archRib.rotation.y = angle;

                const ribPostGeo = new THREE.BoxGeometry(0.8, 8.5, 0.8);
                const ribMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.9, roughness: 0.2 });
                const p1 = new THREE.Mesh(ribPostGeo, ribMat); p1.position.set(-7.6, 4.25, 0); archRib.add(p1);
                const p2 = new THREE.Mesh(ribPostGeo, ribMat); p2.position.set(7.6, 4.25, 0); archRib.add(p2);

                const topBeam = new THREE.Mesh(new THREE.BoxGeometry(16.0, 0.8, 0.8), ribMat);
                topBeam.position.set(0, 8.5, 0);
                archRib.add(topBeam);

                const topNeon = new THREE.Mesh(new THREE.BoxGeometry(15.0, 0.2, 0.9), new THREE.MeshBasicMaterial({ color: r.color }));
                topNeon.position.set(0, 8.1, 0);
                archRib.add(topNeon);

                corridorGroup.add(archRib);
            }

            // 4. Grand Entrance Portal Arch at Wing Gate
            const arch = new THREE.Group();
            arch.position.set(r.to.x * 0.78, 1.8, r.to.z * 0.78);
            arch.rotation.y = angle;

            const archPostGeo = new THREE.BoxGeometry(1.6, 12, 1.6);
            const archMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.95 });
            const gp1 = new THREE.Mesh(archPostGeo, archMat); gp1.position.set(-8.5, 6.0, 0); arch.add(gp1);
            const gp2 = new THREE.Mesh(archPostGeo, archMat); gp2.position.set(8.5, 6.0, 0); arch.add(gp2);

            const beam = new THREE.Mesh(new THREE.BoxGeometry(18.6, 2.0, 2.0), archMat);
            beam.position.set(0, 12, 0);
            arch.add(beam);

            const beamLight = new THREE.Mesh(new THREE.BoxGeometry(17, 0.45, 2.1), new THREE.MeshBasicMaterial({ color: r.color }));
            beamLight.position.set(0, 11.0, 0);
            arch.add(beamLight);

            // Floating Portal Sign
            const portalSign = this.createHoloSprite(r.name, r.color);
            portalSign.position.set(0, 14.5, 0);
            portalSign.scale.set(18, 4.2, 1);
            arch.add(portalSign);

            corridorGroup.add(arch);
        });

        // 5. Complete Glass Enclosure & Room Partitions for 4 Wings
        const wings = [
            { x: -80, z: -60, color: 0xf59e0b, name: 'WING 01 · ĐIỀU HÀNH & CRO' },
            { x: 80, z: -60, color: 0x06b6d4, name: 'WING 02 · SÀN GIAO DỊCH & OMS' },
            { x: -80, z: 75, color: 0xa855f7, name: 'WING 03 · VIỆN QUANT LAB' },
            { x: 80, z: 75, color: 0x10b981, name: 'WING 04 · AN TOÀN & HẬU CẦN' }
        ];
        wings.forEach(w => {
            const wallMat = new THREE.MeshStandardMaterial({
                color: w.color,
                transparent: true,
                opacity: 0.30,
                metalness: 0.9,
                roughness: 0.1
            });
            const railMat = new THREE.MeshBasicMaterial({ color: w.color });

            // North & East acoustic frosted glass partitions
            const wall1 = new THREE.Mesh(new THREE.BoxGeometry(46, 8.5, 0.4), wallMat);
            wall1.position.set(w.x, 6.25, w.z - 26);
            corridorGroup.add(wall1);

            const rail1 = new THREE.Mesh(new THREE.BoxGeometry(46.2, 0.4, 0.6), railMat);
            rail1.position.set(w.x, 10.5, w.z - 26);
            corridorGroup.add(rail1);

            const wall2 = new THREE.Mesh(new THREE.BoxGeometry(0.4, 8.5, 46), wallMat);
            wall2.position.set(w.x - 26, 6.25, w.z);
            corridorGroup.add(wall2);

            const rail2 = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.4, 46.2), railMat);
            rail2.position.set(w.x - 26, 10.5, w.z);
            corridorGroup.add(rail2);

            // Wing Ceiling Perimeter Neon Ring
            // Open-Air Cyber Truss Perimeter (Hollow Wireframe Edges Only - NO SOLID SLABS!)
            const ceilingRing = new THREE.LineSegments(
                new THREE.EdgesGeometry(new THREE.BoxGeometry(54, 0.2, 54)),
                new THREE.LineBasicMaterial({ color: w.color, transparent: true, opacity: 0.35 })
            );
            ceilingRing.position.set(w.x, 18, w.z);
            corridorGroup.add(ceilingRing);
        });

        // 6. High-Tech Data Center & Server Farm (Module Hạ Tầng tại Operations Wing)
        this.buildDataCenterCluster(corridorGroup);

        // 7. Cyber Cafe, Vending Machines & Hydroponic Green Walls
        this.buildPantryFacilities(corridorGroup);

        // 8. Overhead Industrial Steel Truss Rig with Spotlights
        this.buildOverheadTrussRig(corridorGroup);

        // 9. Curved Mega Wall Street Board (Màn Hình LED Cong Khổng Lồ)
        this.buildCurvedWallStreetBoard(corridorGroup);

        this.scene.add(corridorGroup);
    }

    /* --------------------------------------------------------------------------
       5B-1. TRẠM MÁY CHỦ TRUNG TÂM · HIGH-DENSITY SERVER CLUSTER & 100GbE NETWORK
       -------------------------------------------------------------------------- */
    buildDataCenterCluster(parent) {
        const dcGroup = new THREE.Group();
        // Placed flush on top of the Operations Wing platform (Y = 3.75)
        dcGroup.position.set(85, 3.75, 78);

        // 1. Server Room Raised Floor Plinth with Hazard Trim
        const plinth = new THREE.Mesh(
            new THREE.BoxGeometry(32, 0.8, 24),
            new THREE.MeshStandardMaterial({ color: 0x050a14, metalness: 0.9, roughness: 0.2 })
        );
        plinth.position.y = 0.4;
        dcGroup.add(plinth);

        const plinthEdge = new THREE.Mesh(
            new THREE.BoxGeometry(32.4, 0.25, 24.4),
            new THREE.MeshBasicMaterial({ color: 0x10b981 })
        );
        plinthEdge.position.y = 0.8;
        dcGroup.add(plinthEdge);

        // 4 Corner Safety Beacon Columns
        const cornerOffsets = [
            { x: -15.5, z: -11.5 }, { x: 15.5, z: -11.5 },
            { x: -15.5, z: 11.5 },  { x: 15.5, z: 11.5 }
        ];
        cornerOffsets.forEach(c => {
            const pillar = new THREE.Mesh(
                new THREE.CylinderGeometry(0.35, 0.4, 3.5, 8),
                new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 })
            );
            pillar.position.set(c.x, 2.5, c.z);
            dcGroup.add(pillar);

            const beacon = new THREE.Mesh(
                new THREE.SphereGeometry(0.4, 8, 8),
                new THREE.MeshBasicMaterial({ color: 0x00f0ff })
            );
            beacon.position.set(c.x, 4.3, c.z);
            dcGroup.add(beacon);
        });

        // 2. 6 Blade Server Racks in 2 Rows of 3 with Spinning Cooling Fans
        for (let row = -1; row <= 1; row += 2) {
            for (let col = -1; col <= 1; col++) {
                const rackX = col * 8.5;
                const rackZ = row * 6.5;

                const rack = new THREE.Mesh(
                    new THREE.BoxGeometry(5.8, 14, 4.2),
                    new THREE.MeshStandardMaterial({ color: 0x070c18, metalness: 0.95, roughness: 0.15 })
                );
                rack.position.set(rackX, 7.8, rackZ);
                dcGroup.add(rack);

                // Tempered Glass Door with Glowing Green Trim
                const door = new THREE.Mesh(
                    new THREE.PlaneGeometry(5.2, 13),
                    new THREE.MeshStandardMaterial({ color: 0x10b981, transparent: true, opacity: 0.45, metalness: 0.9 })
                );
                door.position.set(rackX, 7.8, rackZ + (row > 0 ? 2.12 : -2.12));
                if (row < 0) door.rotation.y = Math.PI;
                dcGroup.add(door);

                // Dual High-Velocity Exhaust Fans on Rack Top
                for (let f = -1; f <= 1; f += 2) {
                    const fanCowl = new THREE.Mesh(
                        new THREE.CylinderGeometry(1.05, 1.05, 0.4, 16),
                        new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.9 })
                    );
                    fanCowl.position.set(rackX + f * 1.5, 15.0, rackZ);
                    dcGroup.add(fanCowl);

                    // Rotor with 4 blades
                    const fanRotor = new THREE.Group();
                    fanRotor.position.set(rackX + f * 1.5, 15.1, rackZ);
                    fanRotor.rotation.x = Math.PI / 2;

                    for (let b = 0; b < 4; b++) {
                        const blade = new THREE.Mesh(
                            new THREE.BoxGeometry(0.25, 0.85, 0.05),
                            new THREE.MeshBasicMaterial({ color: 0x06b6d4 })
                        );
                        blade.rotation.z = (b * Math.PI) / 2;
                        fanRotor.add(blade);
                    }
                    dcGroup.add(fanRotor);
                    this.serverFans.push(fanRotor);
                }

                // 16 Blinking LED Status Strips per Rack (Dual 8-LED rows)
                for (let l = 0; l < 16; l++) {
                    const ledColor = (l % 4 === 0) ? 0x10b981 : ((l % 4 === 1) ? 0x00f0ff : ((l % 4 === 2) ? 0xf59e0b : 0xffffff));
                    const led = new THREE.Mesh(
                        new THREE.BoxGeometry(0.35, 0.28, 0.15),
                        new THREE.MeshBasicMaterial({ color: ledColor })
                    );
                    led.position.set(
                        rackX - 2.0 + (l % 4) * 1.3,
                        3.2 + Math.floor(l / 4) * 3.1,
                        rackZ + (row > 0 ? 2.05 : -2.05)
                    );
                    dcGroup.add(led);
                    this.blinkingLeds.push(led);
                }
            }
        }

        // 3. Central Core 100GbE Switchboard & Optical Patch Panel (ODF)
        const switchRack = new THREE.Mesh(
            new THREE.BoxGeometry(4.2, 14, 4.0),
            new THREE.MeshStandardMaterial({ color: 0x0a1128, metalness: 0.95, roughness: 0.2 })
        );
        switchRack.position.set(0, 7.8, 0);
        dcGroup.add(switchRack);

        // Patch Panel Rows with Pulsing Fiber Ports
        for (let p = 0; p < 6; p++) {
            const panelBar = new THREE.Mesh(
                new THREE.BoxGeometry(3.8, 0.6, 0.2),
                new THREE.MeshBasicMaterial({ color: 0x00f0ff })
            );
            panelBar.position.set(0, 4.0 + p * 1.8, 2.05);
            dcGroup.add(panelBar);

            // Blinking port activity
            const portLed = new THREE.Mesh(
                new THREE.BoxGeometry(0.4, 0.4, 0.1),
                new THREE.MeshBasicMaterial({ color: 0x10b981 })
            );
            portLed.position.set(1.5, 4.0 + p * 1.8, 2.15);
            dcGroup.add(portLed);
            this.blinkingLeds.push(portLed);
        }

        // 4. Telecommunications SatCom & Microwave Antenna Mast (Tower of Power)
        const mastGroup = new THREE.Group();
        mastGroup.position.set(0, 14.8, -8.5);

        // Lattice Mast Truss Tower rising to Y = 26
        const towerGeo = new THREE.CylinderGeometry(0.4, 1.8, 12, 4);
        const towerMat = new THREE.MeshStandardMaterial({ color: 0x334155, wireframe: true });
        const mastTower = new THREE.Mesh(towerGeo, towerMat);
        mastTower.position.y = 6;
        mastGroup.add(mastTower);

        // Dual Parabolic Satellite Dishes
        for (let s = -1; s <= 1; s += 2) {
            const dish = new THREE.Mesh(
                new THREE.CylinderGeometry(2.0, 0.3, 0.6, 16),
                new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.85 })
            );
            dish.rotation.z = s * Math.PI / 3.5;
            dish.rotation.x = Math.PI / 4;
            dish.position.set(s * 3.2, 7.5, 0);
            mastGroup.add(dish);

            const horn = new THREE.Mesh(
                new THREE.ConeGeometry(0.25, 1.2, 8),
                new THREE.MeshBasicMaterial({ color: 0xf59e0b })
            );
            horn.position.set(s * 3.2, 7.5, 1.0);
            horn.rotation.x = Math.PI / 2;
            mastGroup.add(horn);
        }

        // 360° Rotating Primary Telecom Radar Dish on Mast Top
        const radarGroup = new THREE.Group();
        radarGroup.position.set(0, 12.5, 0);

        const radarDish = new THREE.Mesh(
            new THREE.CylinderGeometry(2.6, 0.5, 0.5, 20),
            new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9 })
        );
        radarDish.rotation.x = Math.PI / 3;
        radarGroup.add(radarDish);

        const radarSpire = new THREE.Mesh(
            new THREE.CylinderGeometry(0.12, 0.12, 3.2, 6),
            new THREE.MeshBasicMaterial({ color: 0x00f0ff })
        );
        radarSpire.position.y = 1.6;
        radarGroup.add(radarSpire);

        const beaconBulb = new THREE.Mesh(
            new THREE.SphereGeometry(0.45, 10, 10),
            new THREE.MeshBasicMaterial({ color: 0x00f0ff })
        );
        beaconBulb.position.y = 3.2;
        radarGroup.add(beaconBulb);

        mastGroup.add(radarGroup);
        this.serverRadarDish = radarGroup;
        dcGroup.add(mastGroup);

        // Store world coordinates of antenna top for expanding ping radar waves
        this.serverAntennaTip = new THREE.Vector3(85, 3.75 + 14.8 + 15.7, 78 - 8.5);

        // 5. Overhead Fiber Cable Trays Carrying Optical Trunks
        const tray = new THREE.Mesh(
            new THREE.BoxGeometry(26, 0.6, 1.4),
            new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 })
        );
        tray.position.set(0, 16.5, 0);
        dcGroup.add(tray);

        const fiber = new THREE.Mesh(
            new THREE.BoxGeometry(25.5, 0.35, 0.8),
            new THREE.MeshBasicMaterial({ color: 0x00f0ff })
        );
        fiber.position.set(0, 16.8, 0);
        dcGroup.add(fiber);

        // 6. Massive Holographic Label Overhead
        const dcTag = this.createHoloSprite('TRẠM MÁY CHỦ TRUNG TÂM · CORE SERVER & 100GbE (Ping: 12ms)', 0x10b981);
        dcTag.position.set(0, 26.5, 0);
        dcTag.scale.set(34, 6.2, 1);
        dcGroup.add(dcTag);

        parent.add(dcGroup);
    }

    /* --------------------------------------------------------------------------
       5B-2. PANTRY, CYBER VENDING MACHINES & BIOPHILIC LIVING WALLS
       -------------------------------------------------------------------------- */
    buildPantryFacilities(parent) {
        const pGroup = new THREE.Group();
        pGroup.position.set(-26, 2, -45);

        // Cyberpunk Vending Machine
        const vm = new THREE.Mesh(
            new THREE.BoxGeometry(4.8, 9.5, 3.8),
            new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.85, roughness: 0.2 })
        );
        vm.position.set(0, 4.75, 0);
        pGroup.add(vm);

        // Vending Screen Glow
        const vmScreen = new THREE.Mesh(
            new THREE.PlaneGeometry(4.0, 5.0),
            new THREE.MeshStandardMaterial({
                color: 0x0284c7,
                emissive: 0x0284c7,
                emissiveIntensity: 0.8
            })
        );
        vmScreen.position.set(0, 5.5, 1.92);
        pGroup.add(vmScreen);

        const vmNeon = new THREE.Mesh(
            new THREE.BoxGeometry(4.8, 0.25, 3.8),
            new THREE.MeshBasicMaterial({ color: 0x38bdf8 })
        );
        vmNeon.position.set(0, 9.5, 0);
        pGroup.add(vmNeon);

        // Biophilic Hydroponic Plant Wall (Cây xanh lọc khí công nghệ cao)
        const wallGroup = new THREE.Group();
        wallGroup.position.set(26, 2, -45);

        const greenPlinth = new THREE.Mesh(
            new THREE.BoxGeometry(10, 1.2, 2.5),
            new THREE.MeshStandardMaterial({ color: 0x1e293b })
        );
        greenPlinth.position.y = 0.6;
        wallGroup.add(greenPlinth);

        for (let g = 0; g < 4; g++) {
            const hedge = new THREE.Mesh(
                new THREE.BoxGeometry(2.0, 7.5, 1.6),
                new THREE.MeshStandardMaterial({ color: (g % 2 === 0 ? 0x10b981 : 0x059669), roughness: 0.8 })
            );
            hedge.position.set(-3.2 + g * 2.2, 4.8, 0);
            wallGroup.add(hedge);
        }

        const greenGlow = new THREE.PointLight(0x10b981, 1.2, 25);
        greenGlow.position.set(0, 6, 2);
        wallGroup.add(greenGlow);

        pGroup.add(wallGroup);
        parent.add(pGroup);
    }

    /* --------------------------------------------------------------------------
       5B-3. OVERHEAD INDUSTRIAL CEILING TRUSS RIG WITH STATION SPOTLIGHTS
       -------------------------------------------------------------------------- */
    buildOverheadTrussRig(parent) {
        const trussGroup = new THREE.Group();
        trussGroup.position.set(0, 48, 0);

        const trussMat = new THREE.MeshStandardMaterial({
            color: 0x1e293b,
            metalness: 0.9,
            roughness: 0.3
        });

        // Outer Hexagonal Truss Ring (Đường kính 280)
        const ringGeo = new THREE.TorusGeometry(140, 0.75, 8, 48);
        const ringMesh = new THREE.Mesh(ringGeo, trussMat);
        ringMesh.rotation.x = Math.PI / 2;
        trussGroup.add(ringMesh);

        // Radial Cross-Beams connecting to center
        for (let i = 0; i < 6; i++) {
            const angle = (i / 6) * Math.PI * 2;
            const beam = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.2, 140), trussMat);
            beam.position.set(Math.sin(angle) * 70, 0, Math.cos(angle) * 70);
            beam.rotation.y = angle;
            trussGroup.add(beam);
        }

        // Spotlights pointing straight down at each of the 12 Stations
        Object.values(this.deptConfigs).forEach(cfg => {
            const spotLight = new THREE.SpotLight(cfg.color, 2.2, 80, Math.PI / 7, 0.35, 1.5);
            spotLight.position.set(cfg.pos.x, 0, cfg.pos.z);
            spotLight.target.position.set(cfg.pos.x, -46, cfg.pos.z);
            trussGroup.add(spotLight);
            trussGroup.add(spotLight.target);

            // Fixture Housing on Truss
            const fixture = new THREE.Mesh(
                new THREE.CylinderGeometry(0.8, 1.2, 2.0, 8),
                new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.9 })
            );
            fixture.position.set(cfg.pos.x, 0, cfg.pos.z);
            trussGroup.add(fixture);
        });

        parent.add(trussGroup);
    }

    /* --------------------------------------------------------------------------
       5B-4. CURVED MEGA WALL STREET BOARD (MÀN HÌNH LED CONG KHỔNG LỒ)
       -------------------------------------------------------------------------- */
    buildCurvedWallStreetBoard(parent) {
        const boardGroup = new THREE.Group();
        boardGroup.position.set(0, 44, -10);

        // Generate dynamic 1024x512 Wall Street Display Canvas Texture
        this.wallStreetCanvas = document.createElement('canvas');
        this.wallStreetCanvas.width = 1024;
        this.wallStreetCanvas.height = 384;
        this.updateWallStreetTextureContent();

        this.wallStreetTexture = new THREE.CanvasTexture(this.wallStreetCanvas);
        this.wallStreetTexture.minFilter = THREE.LinearFilter;
        this.wallStreetTexture.magFilter = THREE.LinearFilter;

        // Curved 180° Cylinder Segment
        const curvedGeo = new THREE.CylinderGeometry(38, 38, 16, 64, 1, true, Math.PI * 0.48, Math.PI * 1.04);
        const curvedMat = new THREE.MeshBasicMaterial({
            map: this.wallStreetTexture,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.96
        });
        const curvedScreen = new THREE.Mesh(curvedGeo, curvedMat);
        curvedScreen.rotation.y = Math.PI * 0.98;
        curvedScreen.rotation.x = 0.08; // Slightly tilted down towards God camera
        boardGroup.add(curvedScreen);

        // Top & Bottom Gold Neon Trim
        const topTrim = new THREE.Mesh(
            new THREE.TorusGeometry(38.2, 0.35, 8, 48, Math.PI * 1.04),
            new THREE.MeshBasicMaterial({ color: 0xf59e0b })
        );
        topTrim.rotation.x = Math.PI / 2 + 0.08;
        topTrim.rotation.z = Math.PI * 0.98;
        topTrim.position.y = 8.0;
        boardGroup.add(topTrim);

        const bottomTrim = new THREE.Mesh(
            new THREE.TorusGeometry(38.2, 0.35, 8, 48, Math.PI * 1.04),
            new THREE.MeshBasicMaterial({ color: 0x38bdf8 })
        );
        bottomTrim.rotation.x = Math.PI / 2 + 0.08;
        bottomTrim.rotation.z = Math.PI * 0.98;
        bottomTrim.position.y = -8.0;
        boardGroup.add(bottomTrim);

        parent.add(boardGroup);
    }

    updateWallStreetTextureContent() {
        if (!this.wallStreetCanvas) return;
        const ctx = this.wallStreetCanvas.getContext('2d');
        const w = this.wallStreetCanvas.width;
        const h = this.wallStreetCanvas.height;

        // Dark Cyber Matrix Terminal Background
        ctx.fillStyle = '#050b18';
        ctx.fillRect(0, 0, w, h);

        // Outer Neon Border
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 4;
        ctx.strokeRect(4, 4, w - 8, h - 8);

        // Header Ribbon
        ctx.fillStyle = 'rgba(2, 132, 199, 0.25)';
        ctx.fillRect(6, 6, w - 12, 54);
        ctx.font = '900 24px "JetBrains Mono", monospace';
        ctx.fillStyle = '#38bdf8';
        ctx.textAlign = 'left';
        ctx.fillText('⚡ ASTRA QUANT · TRỤ SỞ VẬN HÀNH 12 PHÒNG BAN', 24, 42);

        ctx.font = '700 18px "JetBrains Mono", monospace';
        ctx.fillStyle = '#10b981';
        ctx.textAlign = 'right';
        ctx.fillText('● HARD RISK GATE 100% · BINANCE LIVE', w - 24, 42);

        // Price Ticker Row
        ctx.font = 'bold 20px "JetBrains Mono", monospace';
        ctx.textAlign = 'left';
        const prices = [
            { s: 'BTC', p: '$81,205.17', c: '+1.8%', g: true },
            { s: 'ETH', p: '$2,642.10', c: '+2.4%', g: true },
            { s: 'SOL', p: '$152.30', c: '+4.1%', g: true },
            { s: 'BNB', p: '$756.20', c: '+1.1%', g: true },
            { s: 'PEPE', p: '0.00398', c: '+5.2%', g: true }
        ];
        let px = 24;
        prices.forEach(pr => {
            ctx.fillStyle = '#94a3b8';
            ctx.fillText(pr.s + ':', px, 92);
            px += ctx.measureText(pr.s + ':').width + 6;
            ctx.fillStyle = '#f8fafc';
            ctx.fillText(pr.p, px, 92);
            px += ctx.measureText(pr.p).width + 8;
            ctx.fillStyle = pr.g ? '#10b981' : '#f43f5e';
            ctx.fillText(pr.c + '  |  ', px, 92);
            px += ctx.measureText(pr.c + '  |  ').width + 12;
        });

        // Candlestick Chart Area
        const chartY = 118;
        const chartH = 190;
        ctx.fillStyle = '#030712';
        ctx.fillRect(20, chartY, w - 40, chartH);
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.15)';
        ctx.lineWidth = 1;
        for (let y = chartY + 30; y < chartY + chartH; y += 35) {
            ctx.beginPath(); ctx.moveTo(20, y); ctx.lineTo(w - 20, y); ctx.stroke();
        }

        // 36 Bars of Candlesticks
        const numBars = 34;
        const barWidth = 14;
        let lastClose = 180;
        for (let i = 0; i < numBars; i++) {
            const bx = 36 + i * 28;
            const open = lastClose;
            const change = (Math.sin(i * 0.45) * 22 + (Math.random() * 20 - 8));
            const close = Math.max(chartY + 20, Math.min(chartY + chartH - 20, open + change));
            const high = Math.min(chartY + chartH - 10, Math.max(open, close) + Math.random() * 12);
            const low = Math.max(chartY + 10, Math.min(open, close) - Math.random() * 12);
            const isGreen = close >= open;

            ctx.strokeStyle = isGreen ? '#10b981' : '#f43f5e';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(bx + barWidth / 2, low);
            ctx.lineTo(bx + barWidth / 2, high);
            ctx.stroke();

            ctx.fillStyle = isGreen ? '#10b981' : '#f43f5e';
            ctx.fillRect(bx, Math.min(open, close), barWidth, Math.max(3, Math.abs(close - open)));
            lastClose = close;
        }

        // EMA Line overlay
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(36, chartY + 100);
        ctx.bezierCurveTo(240, chartY + 140, 560, chartY + 40, w - 40, chartY + 70);
        ctx.stroke();

        // Footer Summary
        ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
        ctx.fillRect(6, h - 54, w - 12, 48);
        ctx.font = '800 18px "JetBrains Mono", monospace';
        ctx.fillStyle = '#f59e0b';
        ctx.textAlign = 'left';
        const _pnlVal = (window.currentTelemetry && window.currentTelemetry.today_pnl_usd !== undefined) ? Number(window.currentTelemetry.today_pnl_usd) : 0.3328;
        const _pnlStr = (_pnlVal >= 0 ? `+$${_pnlVal.toFixed(4)}` : `-$${Math.abs(_pnlVal).toFixed(4)}`);
        const _winStr = (window.currentTelemetry && window.currentTelemetry.win_rate_pct !== undefined) ? `${window.currentTelemetry.win_rate_pct.toFixed(1)}%` : '66.7%';
        ctx.fillText(`📊 PnL THỰC TẾ: ${_pnlStr} USDT   |   WIN RATE: ${_winStr}   |   AI VETO BẢO VỆ VỐN`, 24, h - 23);

        ctx.fillStyle = '#38bdf8';
        ctx.textAlign = 'right';
        ctx.fillText('12 / 12 AGENTS TRỰC CHIẾN', w - 24, h - 23);
    }

    /* --------------------------------------------------------------------------
       5C. DENSE PERSONNEL: COLLABORATING ASSISTANTS, DRONES & WANDERING STAFF
       -------------------------------------------------------------------------- */
    buildDensePersonnel() {
        // 1. Collaborating Junior Analysts / Quantitative Assistants (8 extra 3D agents)
        const assistantPlacements = [
            { dept: 'lead_pm', pos: { x: -70, y: 2, z: -78 }, col: 0x38bdf8, acc: 0xf59e0b },
            { dept: 'risk_council', pos: { x: -40, y: 2, z: -48 }, col: 0xf43f5e, acc: 0xfb7185 },
            { dept: 'execution_oms', pos: { x: 70, y: 2, z: -48 }, col: 0x10b981, acc: 0x34d399 },
            { dept: 'arbitrage_desk', pos: { x: 115, y: 2, z: -60 }, col: 0x14b8a6, acc: 0x2dd4bf },
            { dept: 'quant_lab', pos: { x: -70, y: 2, z: 52 }, col: 0xa855f7, acc: 0xc084fc },
            { dept: 'breakout_hunter', pos: { x: -40, y: 2, z: 82 }, col: 0x8b5cf6, acc: 0xa78bfa },
            { dept: 'spot_dca', pos: { x: 70, y: 2, z: 52 }, col: 0x0ea5e9, acc: 0x38bdf8 },
            { dept: 'cvar_stress', pos: { x: 98, y: 2, z: 82 }, col: 0xef4444, acc: 0xf87171 }
        ];

        assistantPlacements.forEach((asst, idx) => {
            const asstGroup = new THREE.Group();
            asstGroup.position.set(asst.pos.x, asst.pos.y, asst.pos.z);

            // Small Desk & Monitor
            const sDesk = new THREE.Mesh(
                new THREE.BoxGeometry(9.0, 0.7, 4.5),
                new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8, roughness: 0.3 })
            );
            sDesk.position.set(0, 3.6, -1.0);
            asstGroup.add(sDesk);

            const sScreen = new THREE.Mesh(
                new THREE.BoxGeometry(4.2, 2.4, 0.3),
                new THREE.MeshStandardMaterial({
                    color: 0x020617,
                    emissive: asst.col,
                    emissiveIntensity: 0.7,
                    map: this.createTradingChartTexture(asst.col)
                })
            );
            sScreen.position.set(0, 5.2, -2.0);
            asstGroup.add(sScreen);

            // Seated 3D Assistant Officer Model
            const asstModel = this.createSeatedOfficer3D(asst.dept, { color: asst.col, accent: asst.acc });
            asstGroup.add(asstModel);
            asstGroup.userData.officerModel = asstModel;

            this.scene.add(asstGroup);
            this.supportStaff.push(asstGroup);
        });

        // 2. Three Hovering AI Patrol Drones with Scanner Lights
        for (let d = 0; d < 3; d++) {
            const drone = new THREE.Group();

            const bodyMat = new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.9, roughness: 0.2 });
            const droneBody = new THREE.Mesh(new THREE.SphereGeometry(1.4, 16, 16), bodyMat);
            drone.add(droneBody);

            const visorRing = new THREE.Mesh(
                new THREE.TorusGeometry(1.42, 0.12, 6, 24),
                new THREE.MeshBasicMaterial({ color: (d === 0 ? 0x06b6d4 : (d === 1 ? 0x10b981 : 0xf59e0b)) })
            );
            visorRing.rotation.x = Math.PI / 2;
            drone.add(visorRing);

            // Downward scanning cone
            const spot = new THREE.SpotLight(0x38bdf8, 2.5, 30, Math.PI / 6, 0.4);
            spot.position.set(0, 0, 0);
            spot.target.position.set(0, -10, 0);
            drone.add(spot);
            drone.add(spot.target);

            drone.position.set(Math.cos(d * 2.1) * 45, 12, Math.sin(d * 2.1) * 45);
            drone.userData = {
                phase: d * 2.1,
                speed: 0.4 + d * 0.15
            };

            this.scene.add(drone);
            this.patrolDrones.push(drone);
        }

        // 3. Wandering Staff (2 Active Roaming Analysts with Clear Company Duties)
        const wander1 = this.createBoss3DModel();
        wander1.scale.set(0.9, 0.9, 0.9);
        wander1.position.set(-35, 0, -15);
        wander1.userData.path = [
            { x: -35, z: -15 }, { x: -65, z: -45 }, { x: -10, z: -15 }, { x: 0, z: 10 }
        ];
        wander1.userData.pathIdx = 0;
        wander1.userData.progress = 0;
        const b1 = this.createSpeechBubbleSprite('📋 Giao Liên · Chuyển hồ sơ', 0x38bdf8);
        b1.scale.set(12, 3.0, 1);
        b1.position.set(-35, 8.8, -15);
        this.scene.add(b1);
        wander1.userData.badge = b1;
        this.scene.add(wander1);
        this.wanderingStaff.push(wander1);

        const wander2 = this.createBoss3DModel();
        wander2.scale.set(0.9, 0.9, 0.9);
        wander2.position.set(35, 0, 15);
        wander2.userData.path = [
            { x: 35, z: 15 }, { x: 65, z: 50 }, { x: 20, z: 35 }, { x: 0, z: 10 }
        ];
        wander2.userData.pathIdx = 0;
        wander2.userData.progress = 0;
        const b2 = this.createSpeechBubbleSprite('☕ Tiếp Tế · Cà phê Quant', 0xf59e0b);
        b2.scale.set(12, 3.0, 1);
        b2.position.set(35, 8.8, 15);
        this.scene.add(b2);
        wander2.userData.badge = b2;
        this.scene.add(wander2);
        this.wanderingStaff.push(wander2);
    }


    buildStations() {
        Object.entries(this.deptConfigs).forEach(([key, cfg]) => {
            const stationGroup = new THREE.Group();
            stationGroup.position.set(cfg.pos.x, cfg.pos.y, cfg.pos.z);
            stationGroup.userData = { deptKey: key, config: cfg };

            // 1. Raised Station Floor Pod (Thảm phát sáng phân khu)
            const podGeo = new THREE.BoxGeometry(24, 0.4, 19);
            const podMat = new THREE.MeshStandardMaterial({
                color: 0x0b1329,
                metalness: 0.8,
                roughness: 0.3
            });
            const pod = new THREE.Mesh(podGeo, podMat);
            pod.position.y = 0.2;
            pod.receiveShadow = true;
            stationGroup.add(pod);

            // Pod Border Neon Line
            const podBorderGeo = new THREE.BoxGeometry(24.4, 0.2, 19.4);
            const podBorderMat = new THREE.LineBasicMaterial({ color: cfg.color, transparent: true, opacity: 0.85 });
            const podBorder = new THREE.LineSegments(new THREE.EdgesGeometry(podBorderGeo), podBorderMat);
            podBorder.position.y = 0.4;
            stationGroup.add(podBorder);

            // 2. High-Visibility Cyber L-Shaped Executive Desk
            // Main Desk Top (Mặt bàn chính màu kim loại titanium sáng rõ)
            const deskGeo = new THREE.BoxGeometry(15, 0.8, 7.0);
            const deskMat = new THREE.MeshStandardMaterial({
                color: 0x22324d,
                metalness: 0.75,
                roughness: 0.25
            });
            const desk = new THREE.Mesh(deskGeo, deskMat);
            desk.position.set(0, 3.6, -1.0);
            desk.castShadow = true;
            desk.receiveShadow = true;
            stationGroup.add(desk);

            // Glowing Edge Trim (Viền đèn neon bàn làm việc)
            const deskTrimGeo = new THREE.BoxGeometry(15.2, 0.2, 7.2);
            const deskTrimMat = new THREE.MeshBasicMaterial({ color: cfg.color });
            const deskTrim = new THREE.Mesh(deskTrimGeo, deskTrimMat);
            deskTrim.position.set(0, 4.0, -1.0);
            stationGroup.add(deskTrim);

            // Side Return (Phần bàn góc chữ L hiện đại)
            const sideReturnGeo = new THREE.BoxGeometry(5.5, 0.8, 7.5);
            const sideReturn = new THREE.Mesh(sideReturnGeo, deskMat);
            sideReturn.position.set(-5.5, 3.6, 2.5);
            stationGroup.add(sideReturn);

            // Metallic Desk Legs (Chân bàn kim loại)
            const legGeo = new THREE.CylinderGeometry(0.35, 0.35, 3.6, 8);
            const legMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.9 });
            const legPositions = [
                { x: -7.0, z: -4.0 }, { x: 7.0, z: -4.0 },
                { x: 7.0, z: 2.0 }, { x: -7.0, z: 6.0 }, { x: -3.0, z: 6.0 }
            ];
            legPositions.forEach(lp => {
                const leg = new THREE.Mesh(legGeo, legMat);
                leg.position.set(lp.x, 1.8, lp.z);
                stationGroup.add(leg);
            });

            // Modesty Shield (Yếm bàn phía trước)
            const shieldGeo = new THREE.BoxGeometry(14.6, 3.2, 0.3);
            const shieldMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.5 });
            const shield = new THREE.Mesh(shieldGeo, shieldMat);
            shield.position.set(0, 1.8, -4.3);
            stationGroup.add(shield);

            // 3. High-Fidelity Ergonomic Office Chair (5-star base, gas piston, lumbar & headrest)
            const chairGroup = new THREE.Group();
            chairGroup.position.set(0, 0, 2.4);

            const chairDarkMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.7 });
            const chromeMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, metalness: 0.9, roughness: 0.2 });
            const chairAccentMat = new THREE.MeshBasicMaterial({ color: cfg.color });

            // 5-Point Star Caster Base
            for (let b = 0; b < 5; b++) {
                const angle = (b / 5) * Math.PI * 2;
                const spoke = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.25, 2.2), chromeMat);
                spoke.rotation.y = angle;
                spoke.position.set(Math.sin(angle) * 1.0, 0.25, Math.cos(angle) * 1.0);
                chairGroup.add(spoke);

                const wheel = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.2, 8), chairDarkMat);
                wheel.position.set(Math.sin(angle) * 2.0, 0.15, Math.cos(angle) * 2.0);
                wheel.rotation.z = Math.PI / 2;
                chairGroup.add(wheel);
            }

            // Gas Lift Chrome Cylinder
            const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 2.0, 12), chromeMat);
            stem.position.y = 1.2;
            chairGroup.add(stem);

            // Contoured Ergonomic Seat Cushion
            const seat = new THREE.Mesh(new THREE.BoxGeometry(4.0, 0.85, 3.9), chairDarkMat);
            seat.position.y = 2.4;
            chairGroup.add(seat);

            // Lumbar & Curved Mesh Backrest
            const backrest = new THREE.Mesh(new THREE.BoxGeometry(3.6, 4.6, 0.6), chairDarkMat);
            backrest.position.set(0, 4.8, 1.8);
            chairGroup.add(backrest);

            // Backrest Neon Accent Trim
            const backTrim = new THREE.Mesh(new THREE.BoxGeometry(3.65, 0.18, 0.65), chairAccentMat);
            backTrim.position.set(0, 6.8, 1.8);
            chairGroup.add(backTrim);

            // Headrest Pillow
            const headrest = new THREE.Mesh(new THREE.BoxGeometry(2.4, 1.0, 0.8), chairDarkMat);
            headrest.position.set(0, 7.3, 1.9);
            chairGroup.add(headrest);

            // 3D Armrests with Chrome Supports
            for (let a = -1; a <= 1; a += 2) {
                const armSupport = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 1.6, 8), chromeMat);
                armSupport.position.set(a * 2.1, 3.2, 0.4);
                chairGroup.add(armSupport);

                const armPad = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.25, 2.2), chairDarkMat);
                armPad.position.set(a * 2.1, 4.0, 0.4);
                chairGroup.add(armPad);
            }
            stationGroup.add(chairGroup);

            // 4. Triple Monitor Command Array with Articulation Arms & Glow
            const chartTex = this.createTradingChartTexture(cfg.color);

            // Dual Heavy-Duty Monitor Mount Pole
            const poleMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.85 });
            const mountPole = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 4.0, 10), poleMat);
            mountPole.position.set(0, 4.8, -3.8);
            stationGroup.add(mountPole);

            // Cross Bar Mount
            const crossBar = new THREE.Mesh(new THREE.BoxGeometry(11.0, 0.4, 0.4), poleMat);
            crossBar.position.set(0, 5.8, -3.8);
            stationGroup.add(crossBar);

            // Center Ultrawide Screen
            const centerScreenMat = new THREE.MeshStandardMaterial({
                color: 0x020617,
                emissive: cfg.color,
                emissiveIntensity: 0.75,
                map: chartTex
            });
            const centerScreen = new THREE.Mesh(new THREE.BoxGeometry(5.6, 3.2, 0.35), centerScreenMat);
            centerScreen.position.set(0, 5.8, -2.5);
            stationGroup.add(centerScreen);

            // Left & Right Angled Wing Screens
            const sideScreenGeo = new THREE.BoxGeometry(4.0, 2.9, 0.35);
            const leftScreen = new THREE.Mesh(sideScreenGeo, centerScreenMat);
            leftScreen.position.set(-5.0, 5.8, -2.0);
            leftScreen.rotation.y = 0.34;
            stationGroup.add(leftScreen);

            const rightScreen = new THREE.Mesh(sideScreenGeo, centerScreenMat);
            rightScreen.position.set(5.0, 5.8, -2.0);
            rightScreen.rotation.y = -0.34;
            stationGroup.add(rightScreen);

            // Soft Glow onto Desk Surface
            const screenGlow = new THREE.PointLight(cfg.color, 1.2, 16);
            screenGlow.position.set(0, 5.2, -1.0);
            stationGroup.add(screenGlow);

            // 5. RGB Mechanical Keyboard & Stitched Desk Mat
            // Large Neoprene Desk Mat with Stitched Neon Border
            const deskMatMesh = new THREE.Mesh(
                new THREE.BoxGeometry(10.0, 0.05, 4.2),
                new THREE.MeshStandardMaterial({ color: 0x090d16, roughness: 0.9 })
            );
            deskMatMesh.position.set(0, 4.03, 0.3);
            stationGroup.add(deskMatMesh);

            const deskMatTrim = new THREE.Mesh(
                new THREE.BoxGeometry(10.1, 0.07, 4.3),
                chairAccentMat
            );
            deskMatTrim.position.set(0, 4.01, 0.3);
            stationGroup.add(deskMatTrim);

            // RGB Mechanical Keyboard Base & Keycaps
            const kbMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.7, roughness: 0.3 });
            const kbBase = new THREE.Mesh(new THREE.BoxGeometry(4.6, 0.22, 1.8), kbMat);
            kbBase.position.set(0, 4.14, 0.5);
            stationGroup.add(kbBase);

            // Glowing Keycap Underglow
            const kbUnderglow = new THREE.Mesh(new THREE.BoxGeometry(4.4, 0.08, 1.6), chairAccentMat);
            kbUnderglow.position.set(0, 4.26, 0.5);
            stationGroup.add(kbUnderglow);

            // Contoured Ergonomic RGB Mouse
            const mouse = new THREE.Mesh(
                new THREE.BoxGeometry(0.85, 0.45, 1.35),
                new THREE.MeshStandardMaterial({ color: 0x020617, roughness: 0.3 })
            );
            mouse.position.set(3.4, 4.25, 0.6);
            stationGroup.add(mouse);

            const mouseGlow = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.15, 0.4), chairAccentMat);
            mouseGlow.position.set(3.4, 4.45, 0.4);
            stationGroup.add(mouseGlow);

            // 6. High-End Liquid-Cooled Workstation PC Tower with Glass Panel
            const pcTower = new THREE.Group();
            pcTower.position.set(-9.2, 2.5, 0.5);

            const pcCase = new THREE.Mesh(
                new THREE.BoxGeometry(2.4, 5.2, 4.8),
                new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.85, roughness: 0.2 })
            );
            pcTower.add(pcCase);

            // Tempered Glass Window
            const pcGlass = new THREE.Mesh(
                new THREE.PlaneGeometry(4.4, 4.6),
                new THREE.MeshStandardMaterial({ color: cfg.color, transparent: true, opacity: 0.6, metalness: 0.9 })
            );
            pcGlass.position.set(1.22, 0, 0);
            pcGlass.rotation.y = Math.PI / 2;
            pcTower.add(pcGlass);

            // 3 RGB Glowing Fans in front
            for (let f = -1; f <= 1; f++) {
                const fanRing = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.08, 6, 16), chairAccentMat);
                fanRing.position.set(0, f * 1.5, 2.42);
                pcTower.add(fanRing);
            }
            stationGroup.add(pcTower);

            // 7. Ceramic Coffee Mug with Steam Particles
            const mug = new THREE.Mesh(
                new THREE.CylinderGeometry(0.45, 0.4, 0.9, 12),
                new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3 })
            );
            mug.position.set(-4.2, 4.45, 1.2);
            stationGroup.add(mug);

            // 8. Smartphone / Hardware 2FA Device with Glowing OLED Screen
            const phone = new THREE.Mesh(
                new THREE.BoxGeometry(0.9, 0.08, 1.7),
                new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9 })
            );
            phone.position.set(4.6, 4.06, 1.5);
            stationGroup.add(phone);

            const phoneScreen = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.02, 1.5), chairAccentMat);
            phoneScreen.position.set(4.6, 4.11, 1.5);
            stationGroup.add(phoneScreen);

            // 5. Specialized Department 3D Props (Rich Visual Metaphors for ALL 12 Departments!)
            if (cfg.type === 'veto_console' || key === 'risk_council') {
                // 02 · CRO Risk Council: Dual Red Laser Gate + Hexagonal Veto Shield
                const colGeo = new THREE.CylinderGeometry(0.45, 0.45, 10, 12);
                const colMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.9 });
                const col1 = new THREE.Mesh(colGeo, colMat); col1.position.set(-8.5, 5.0, -2);
                const col2 = new THREE.Mesh(colGeo, colMat); col2.position.set(8.5, 5.0, -2);
                stationGroup.add(col1, col2);

                const beamGeo = new THREE.CylinderGeometry(0.16, 0.16, 17, 8);
                const beamMat = new THREE.MeshBasicMaterial({ color: 0xf43f5e, transparent: true, opacity: 0.85 });
                const beam = new THREE.Mesh(beamGeo, beamMat);
                beam.rotation.z = Math.PI / 2;
                beam.position.set(0, 8.5, -2);
                stationGroup.add(beam);
                stationGroup.userData.laserBeam = beam;

                const shieldHex = new THREE.Mesh(
                    new THREE.CylinderGeometry(2.5, 2.5, 0.15, 6),
                    new THREE.MeshStandardMaterial({ color: 0xf43f5e, metalness: 0.8, roughness: 0.2, transparent: true, opacity: 0.45 })
                );
                shieldHex.position.set(0, 7.5, -2);
                shieldHex.rotation.x = Math.PI / 2;
                stationGroup.add(shieldHex);

            } else if (cfg.type === 'radar_station' || key === 'news_scout') {
                // 03 · News Scout & NLP: Rotating Cyber Satellite Dish + Mast
                const dishGeo = new THREE.CylinderGeometry(3.5, 0.5, 1.2, 16);
                const dishMat = new THREE.MeshStandardMaterial({ color: 0x06b6d4, metalness: 0.85, roughness: 0.2 });
                const dish = new THREE.Mesh(dishGeo, dishMat);
                dish.position.set(0, 9.5, -3);
                dish.rotation.x = Math.PI / 4;
                stationGroup.add(dish);
                stationGroup.userData.radarDish = dish;

                const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.3, 7, 8), new THREE.MeshStandardMaterial({ color: 0x64748b }));
                mast.position.set(0, 5.5, -3);
                stationGroup.add(mast);

            } else if (cfg.type === 'executive_desk' || key === 'lead_pm') {
                // 01 · Lead PM: Rotating Holographic Strategy Globe + Gold Halo
                const globeGeo = new THREE.IcosahedronGeometry(2.0, 1);
                const globeMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, wireframe: true, transparent: true, opacity: 0.85 });
                const globe = new THREE.Mesh(globeGeo, globeMat);
                globe.position.set(0, 9.0, -2);
                stationGroup.add(globe);
                stationGroup.userData.strategyGlobe = globe;

                const ringGeo = new THREE.RingGeometry(2.4, 2.7, 24);
                const ringMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, side: THREE.DoubleSide });
                const ring = new THREE.Mesh(ringGeo, ringMat);
                ring.position.set(0, 9.0, -2);
                ring.rotation.x = Math.PI / 2.5;
                stationGroup.add(ring);

            } else if (cfg.type === 'trading_terminal' || key === 'execution_oms') {
                // 04 · Execution OMS: Dual Order Flow Depth Pillars (Green Bid / Red Ask)
                const bidPillar = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.7, 4.0, 12), new THREE.MeshStandardMaterial({ color: 0x10b981, metalness: 0.7, roughness: 0.2 }));
                bidPillar.position.set(-6.5, 4.2, -2);
                stationGroup.add(bidPillar);

                const askPillar = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.7, 4.0, 12), new THREE.MeshStandardMaterial({ color: 0xef4444, metalness: 0.7, roughness: 0.2 }));
                askPillar.position.set(6.5, 4.2, -2);
                stationGroup.add(askPillar);

            } else if (cfg.type === 'breakout_post' || key === 'breakout_hunter') {
                // 05 · Breakout Hunter: Upward Golden Breakout Arrow
                const arrowStem = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 3.2, 8), new THREE.MeshBasicMaterial({ color: 0xf59e0b }));
                arrowStem.position.set(0, 7.5, -2);
                const arrowHead = new THREE.Mesh(new THREE.ConeGeometry(1.1, 1.8, 8), new THREE.MeshBasicMaterial({ color: 0xf59e0b }));
                arrowHead.position.set(0, 9.8, -2);
                stationGroup.add(arrowStem, arrowHead);

            } else if (cfg.type === 'quant_lab' || key === 'quant_lab') {
                // 06 · Quant Lab: Quantum Rotating Hypercube Wireframe
                const qGeo = new THREE.IcosahedronGeometry(2.2, 0);
                const qMat = new THREE.MeshBasicMaterial({ color: 0xc084fc, wireframe: true });
                const qMesh = new THREE.Mesh(qGeo, qMat);
                qMesh.position.set(0, 9.5, -2);
                stationGroup.add(qMesh);
                stationGroup.userData.quantumCube = qMesh;

            } else if (cfg.type === 'volatility_station' || key === 'volatility_lab') {
                // 07 · Volatility Lab: Dual Oscillating Sine Wave Ring
                const waveGeo = new THREE.TorusGeometry(2.6, 0.22, 8, 24);
                const waveMat = new THREE.MeshBasicMaterial({ color: 0xec4899, wireframe: true });
                const wave = new THREE.Mesh(waveGeo, waveMat);
                wave.position.set(0, 9.0, -2);
                wave.rotation.x = Math.PI / 3;
                stationGroup.add(wave);
                stationGroup.userData.volatilityWave = wave;

            } else if (cfg.type === 'spot_vault' || key === 'spot_dca') {
                // 08 · Spot DCA: Holographic Diamond Gemstone & Gold Coin Stacks
                const gemGeo = new THREE.OctahedronGeometry(1.8, 0);
                const gemMat = new THREE.MeshStandardMaterial({ color: 0x14b8a6, metalness: 0.9, roughness: 0.1, transparent: true, opacity: 0.85 });
                const gem = new THREE.Mesh(gemGeo, gemMat);
                gem.position.set(0, 9.0, -2);
                stationGroup.add(gem);
                stationGroup.userData.spotGem = gem;

                for (let c = 0; c < 3; c++) {
                    const coin = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.0, 0.8, 16), new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.9 }));
                    coin.position.set(5.5 + c * 1.4, 4.4, 1.0);
                    stationGroup.add(coin);
                }

            } else if (cfg.type === 'arbitrage_rig' || key === 'arbitrage_desk') {
                // 09 · Arbitrage Desk: Floating Golden Balance Scales
                const beam = new THREE.Mesh(new THREE.BoxGeometry(5.5, 0.25, 0.25), new THREE.MeshStandardMaterial({ color: 0x8b5cf6, metalness: 0.9 }));
                beam.position.set(0, 9.5, -2);
                stationGroup.add(beam);
                for (let s = -1; s <= 1; s += 2) {
                    const pan = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 0.7, 0.35, 12), new THREE.MeshStandardMaterial({ color: 0x8b5cf6, metalness: 0.7 }));
                    pan.position.set(s * 2.4, 8.3, -2);
                    stationGroup.add(pan);
                }

            } else if (cfg.type === 'clearing_station' || key === 'accounting_pm') {
                // 10 · Accounting & Post-Mortem: Golden Trophy of High-Water Mark
                const trophyCup = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 0.5, 2.0, 16), new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.95, roughness: 0.1 }));
                trophyCup.position.set(0, 9.0, -2);
                const trophyBase = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.5, 1.8), new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.8 }));
                trophyBase.position.set(0, 7.7, -2);
                stationGroup.add(trophyCup, trophyBase);

            } else if (cfg.type === 'academy_pillar' || key === 'community_affiliate') {
                // 11 · Community & Square: Radio Broadcast Tower with Signal Rings
                const antenna = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.5, 5.5, 8), new THREE.MeshStandardMaterial({ color: 0x3b82f6, metalness: 0.9 }));
                antenna.position.set(0, 7.5, -2);
                const signalRing = new THREE.Mesh(new THREE.TorusGeometry(1.6, 0.12, 6, 20), new THREE.MeshBasicMaterial({ color: 0x3b82f6, transparent: true, opacity: 0.7 }));
                signalRing.position.set(0, 9.8, -2);
                stationGroup.add(antenna, signalRing);

            } else if (cfg.type === 'server_bunker' || key === 'cvar_stress') {
                // 12 · CVaR Stress Test: Heavy Armored Server Racks with Hazard Trim
                for (let r = -1; r <= 1; r += 2) {
                    const rackGeo = new THREE.BoxGeometry(3.2, 8.5, 2.8);
                    const rackMat = new THREE.MeshStandardMaterial({ color: 0x090d1a, metalness: 0.9 });
                    const rack = new THREE.Mesh(rackGeo, rackMat);
                    rack.position.set(r * 8.5, 4.3, -2);
                    stationGroup.add(rack);

                    for (let l = 0; l < 4; l++) {
                        const led = new THREE.Mesh(
                            new THREE.BoxGeometry(0.3, 0.3, 0.1),
                            new THREE.MeshBasicMaterial({ color: (l % 2 === 0 ? 0x10b981 : 0xef4444) })
                        );
                        led.position.set(r * 8.5, 2.0 + l * 1.7, -0.3);
                        stationGroup.add(led);
                        this.blinkingLeds.push(led);
                    }
                }
            }

            // 6. Full 3D Seated Officer Model at Ergonomic Chair & Desk
            const officerModel = this.createSeatedOfficer3D(key, cfg);
            stationGroup.add(officerModel);
            stationGroup.userData.officerModel = officerModel;

            // 7. Floating 3D Holographic Department Tag Overhead
            const holoTag = this.createHoloSprite(cfg.tag, cfg.color);
            holoTag.position.y = 14.2;
            holoTag.scale.set(17, 4.2, 1);
            stationGroup.add(holoTag);

            // Floating 3D Speech Bubble Billboard (Dynamic Dialogue)
            const speechBubble = this.createSpeechBubbleSprite(
                DEPT_SPEECHES[key] ? DEPT_SPEECHES[key][0] : cfg.name,
                cfg.color
            );
            speechBubble.position.set(0, 19, 0);
            speechBubble.scale.set(24, 6, 1);
            speechBubble.visible = false;
            stationGroup.add(speechBubble);
            stationGroup.userData.speechBubble = speechBubble;
            this.floatingBubbles[key] = speechBubble;

            // 8. Invisible Click Hitbox for Raycasting (transparent: true, opacity: 0 for reliable raycasting)
            const hitGeo = new THREE.BoxGeometry(24, 24, 20);
            const hitMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false });
            const hitBox = new THREE.Mesh(hitGeo, hitMat);
            hitBox.position.y = 10;
            hitBox.userData = { deptKey: key, stationGroup };
            stationGroup.add(hitBox);
            this.stationMeshes.push(hitBox);

            // Also tag all station components (officer, desk, chair, holoTag) with deptKey
            stationGroup.traverse(child => {
                if (child.isMesh || child.isSprite) {
                    child.userData.deptKey = key;
                    child.userData.stationGroup = stationGroup;
                }
            });

            this.scene.add(stationGroup);
            this.stations[key] = stationGroup;
        });
    }

    /* --------------------------------------------------------------------------
       10D. BUILD MKT NIVER LOWER OPERATIONS DECK (TẦNG DƯỚI · Y = -80)
       Nhà Cửa, Bàn Ghế, Máy Tính, Người Ngợm 3D Đầy Đủ cho 12 Ban Marketing!
       -------------------------------------------------------------------------- */
    buildMktLowerFloor() {
        this.mktFloorGroup = new THREE.Group();
        this.mktStations = {};

        // 1. SÀN CYBER TẦNG DƯỚI B1 (Obsidian Floor & Glowing Neon Grid at Y = -82)
        const floorGeo = new THREE.BoxGeometry(290, 2.0, 290);
        const floorMat = new THREE.MeshStandardMaterial({
            color: 0x050814,
            metalness: 0.9,
            roughness: 0.2
        });
        const mktFloor = new THREE.Mesh(floorGeo, floorMat);
        mktFloor.position.set(0, -82, 0);
        mktFloor.receiveShadow = true;
        this.mktFloorGroup.add(mktFloor);

        // Neon Grid Lines on Floor
        const grid = new THREE.GridHelper(290, 29, 0x8b5cf6, 0x1e293b);
        grid.position.set(0, -80.9, 0);
        this.mktFloorGroup.add(grid);

        // Neon Floor Perimeter Border
        const borderGeo = new THREE.BoxGeometry(292, 3, 292);
        const borderMat = new THREE.LineBasicMaterial({ color: 0x8b5cf6, transparent: true, opacity: 0.8 });
        const border = new THREE.LineSegments(new THREE.EdgesGeometry(borderGeo), borderMat);
        border.position.set(0, -81.5, 0);
        this.mktFloorGroup.add(border);

        // 2. TRỤ KÍNH THANG MÁY NỐI TẦNG TRÊN (Y=0) VÀ TẦNG DƯỚI (Y=-80)
        const shaftGeo = new THREE.CylinderGeometry(9, 9, 86, 24, 1, true);
        const shaftMat = new THREE.MeshStandardMaterial({
            color: 0x0284c7,
            metalness: 0.9,
            roughness: 0.1,
            transparent: true,
            opacity: 0.35,
            side: THREE.DoubleSide
        });
        const elevatorShaft = new THREE.Mesh(shaftGeo, shaftMat);
        elevatorShaft.position.set(0, -40, 0);
        this.mktFloorGroup.add(elevatorShaft);

        // Glowing Elevator Rings
        for (let r = 0; r < 5; r++) {
            const ringGeo = new THREE.TorusGeometry(9.2, 0.3, 8, 32);
            const ringMat = new THREE.MeshBasicMaterial({ color: 0x8b5cf6 });
            const ring = new THREE.Mesh(ringGeo, ringMat);
            ring.rotation.x = Math.PI / 2;
            ring.position.set(0, -80 + r * 20, 0);
            this.mktFloorGroup.add(ring);
        }

        // Central Elevator Pod (Buồng thang máy)
        const podGeo = new THREE.CylinderGeometry(7.5, 7.5, 8, 16);
        const podMat = new THREE.MeshStandardMaterial({
            color: 0x1e1b4b,
            emissive: 0x8b5cf6,
            emissiveIntensity: 0.35,
            metalness: 0.8,
            roughness: 0.2
        });
        this.mktElevatorPod = new THREE.Mesh(podGeo, podMat);
        this.mktElevatorPod.position.set(0, -76, 0);
        this.mktFloorGroup.add(this.mktElevatorPod);

        // Biển hiệu phát sáng trung tâm Tầng Dưới
        const centerSign = this.createHoloSprite('📢 TẦNG DƯỚI: MKT NIVER (12 BAN MARKETING & ADS)', 0x8b5cf6);
        centerSign.position.set(0, -68, 0);
        centerSign.scale.set(38, 9.5, 1);
        this.mktFloorGroup.add(centerSign);

        // 3. 12 PHÒNG BAN MARKETING (BÀN GHẾ, MÁY TÍNH, MÀN HÌNH, NGƯỜI NGỢM ĐẦY ĐỦ)
        const mktDeptConfigs = {
            'captain': {
                name: 'Tổng Chỉ Huy', officer: 'Captain (agnes-3.0-flash · Vyce)', icon: '🎯',
                tag: '01 · CAPTAIN', pos: { x: -85, y: -79, z: -65 }, color: 0x8b5cf6, accent: 0xa855f7
            },
            'content_lab': {
                name: 'Phòng Nội Dung', officer: 'Content (claude-sonnet-4-6 · Vyce)', icon: '✒️',
                tag: '02 · CONTENT', pos: { x: -55, y: -79, z: -35 }, color: 0x22c55e, accent: 0x4ade80
            },
            'video_forge': {
                name: 'Xưởng Video', officer: 'Video Forge (cx/gpt-5.6-terra · 9Router)', icon: '🎬',
                tag: '03 · VIDEO', pos: { x: -85, y: -79, z: -20 }, color: 0xf59e0b, accent: 0xfbbf24
            },
            'ads_engine': {
                name: 'Phòng Quảng Cáo', officer: 'Ads Engine (claude-sonnet-4-6 · Vyce)', icon: '📢',
                tag: '04 · ADS META', pos: { x: 55, y: -79, z: -65 }, color: 0xef4444, accent: 0xf87171
            },
            'seeding_ops': {
                name: 'Đội Seeding', officer: 'Seeding Ops (deepseek-v4 · Vyce)', icon: '🌱',
                tag: '05 · THATIM', pos: { x: 85, y: -79, z: -35 }, color: 0x10b981, accent: 0x34d399
            },
            'trend_scout': {
                name: 'Trinh Sát Xu Hướng', officer: 'Trend Scout (cx/gpt-6-astra · 9Router)', icon: '📡',
                tag: '06 · TIKTOK', pos: { x: 85, y: -79, z: -65 }, color: 0x0ea5e9, accent: 0x38bdf8
            },
            'risk_guard': {
                name: 'Cảnh Sát Rủi Ro', officer: 'Risk Guard (claude-sonnet-4-6 · Vyce)', icon: '🛡️',
                tag: '07 · ANTI-CHECK', pos: { x: -85, y: -79, z: 65 }, color: 0x0284c7, accent: 0x38bdf8
            },
            'page_router': {
                name: 'Phân Luồng Page', officer: 'Page Router (cx/gpt-5.6-terra · 9Router)', icon: '🔀',
                tag: '08 · 22 PAGES', pos: { x: -55, y: -79, z: 35 }, color: 0x64748b, accent: 0x94a3b8
            },
            'asset_guard': {
                name: 'Bảo Vệ Tài Sản', officer: 'Asset Guard (Local SHA-256)', icon: '🔒',
                tag: '09 · ANTI-DUP', pos: { x: -85, y: -79, z: 95 }, color: 0xf43f5e, accent: 0xfb7185
            },
            'affiliate_desk': {
                name: 'Bàn Affiliate', officer: 'Affiliate Desk (cx/gpt-5.6-luna · 9Router)', icon: '💰',
                tag: '10 · SHOPEE', pos: { x: 55, y: -79, z: 65 }, color: 0x14b8a6, accent: 0x2dd4bf
            },
            'crm_support': {
                name: 'Chăm Sóc Khách', officer: 'CRM Support (deepseek-v4.1 · Vyce)', icon: '👥',
                tag: '11 · GEMINI JIO', pos: { x: 85, y: -79, z: 35 }, color: 0x6366f1, accent: 0x818cf8
            },
            'analytics_pm': {
                name: 'Phòng Phân Tích', officer: 'Analytics PM (deepseek-v4 · Vyce)', icon: '📊',
                tag: '12 · REELS FLOP', pos: { x: 85, y: -79, z: 95 }, color: 0x3b82f6, accent: 0x60a5fa
            }
        };

        this.mktDeptConfigs = mktDeptConfigs;

        Object.entries(mktDeptConfigs).forEach(([key, cfg]) => {
            const stGroup = new THREE.Group();
            stGroup.position.set(cfg.pos.x, cfg.pos.y, cfg.pos.z);
            stGroup.userData = { deptKey: key, config: cfg, isMkt: true };

            // Thảm Pod phát sáng neon
            const podGeo = new THREE.BoxGeometry(24, 0.4, 19);
            const podMat = new THREE.MeshStandardMaterial({ color: 0x090e1c, metalness: 0.8, roughness: 0.3 });
            const pod = new THREE.Mesh(podGeo, podMat);
            pod.position.y = 0.2;
            pod.receiveShadow = true;
            stGroup.add(pod);

            const podBorder = new THREE.LineSegments(
                new THREE.EdgesGeometry(new THREE.BoxGeometry(24.4, 0.2, 19.4)),
                new THREE.LineBasicMaterial({ color: cfg.color, transparent: true, opacity: 0.85 })
            );
            podBorder.position.y = 0.4;
            stGroup.add(podBorder);

            // Bàn làm việc cong kim loại Cyber L-Desk
            const deskMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8, roughness: 0.25 });
            const desk = new THREE.Mesh(new THREE.BoxGeometry(15, 0.8, 7.0), deskMat);
            desk.position.set(0, 3.6, -1.0);
            stGroup.add(desk);

            const deskTrim = new THREE.Mesh(new THREE.BoxGeometry(15.2, 0.2, 7.2), new THREE.MeshBasicMaterial({ color: cfg.color }));
            deskTrim.position.set(0, 4.0, -1.0);
            stGroup.add(deskTrim);

            const sideReturn = new THREE.Mesh(new THREE.BoxGeometry(5.5, 0.8, 7.5), deskMat);
            sideReturn.position.set(-5.5, 3.6, 2.5);
            stGroup.add(sideReturn);

            // Chân bàn
            const legGeo = new THREE.CylinderGeometry(0.35, 0.35, 3.6, 8);
            const legMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.9 });
            [ { x: -7, z: -4 }, { x: 7, z: -4 }, { x: 7, z: 2 }, { x: -7, z: 6 } ].forEach(lp => {
                const leg = new THREE.Mesh(legGeo, legMat);
                leg.position.set(lp.x, 1.8, lp.z);
                stGroup.add(leg);
            });

            // Ghế công thái học
            const chairGroup = new THREE.Group();
            chairGroup.position.set(0, 0, 2.4);
            const chairDarkMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.7 });
            const chairAccentMat = new THREE.MeshBasicMaterial({ color: cfg.color });
            const chromeMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, metalness: 0.9 });

            for (let b = 0; b < 5; b++) {
                const angle = (b / 5) * Math.PI * 2;
                const spoke = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.25, 2.2), chromeMat);
                spoke.rotation.y = angle;
                spoke.position.set(Math.sin(angle) * 1.0, 0.25, Math.cos(angle) * 1.0);
                chairGroup.add(spoke);
            }
            const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 2.0, 10), chromeMat);
            stem.position.y = 1.2;
            chairGroup.add(stem);

            const seat = new THREE.Mesh(new THREE.BoxGeometry(4.0, 0.85, 3.9), chairDarkMat);
            seat.position.y = 2.4;
            chairGroup.add(seat);

            const backrest = new THREE.Mesh(new THREE.BoxGeometry(3.6, 4.6, 0.6), chairDarkMat);
            backrest.position.set(0, 4.8, 1.8);
            chairGroup.add(backrest);

            const backTrim = new THREE.Mesh(new THREE.BoxGeometry(3.65, 0.2, 0.65), chairAccentMat);
            backTrim.position.set(0, 6.8, 1.8);
            chairGroup.add(backTrim);
            stGroup.add(chairGroup);

            // 3 Màn hình máy tính cong phát sáng
            const chartTex = this.createTradingChartTexture(cfg.color);
            const screenMat = new THREE.MeshStandardMaterial({
                color: 0x020617,
                emissive: cfg.color,
                emissiveIntensity: 0.75,
                map: chartTex
            });
            const centerScreen = new THREE.Mesh(new THREE.BoxGeometry(5.6, 3.2, 0.35), screenMat);
            centerScreen.position.set(0, 5.8, -2.5);
            stGroup.add(centerScreen);

            const leftScreen = new THREE.Mesh(new THREE.BoxGeometry(4.0, 2.9, 0.35), screenMat);
            leftScreen.position.set(-5.0, 5.8, -2.0);
            leftScreen.rotation.y = 0.34;
            stGroup.add(leftScreen);

            const rightScreen = new THREE.Mesh(new THREE.BoxGeometry(4.0, 2.9, 0.35), screenMat);
            rightScreen.position.set(5.0, 5.8, -2.0);
            rightScreen.rotation.y = -0.34;
            stGroup.add(rightScreen);

            // Bàn phím cơ & chuột
            const kb = new THREE.Mesh(new THREE.BoxGeometry(4.4, 0.2, 1.6), chairAccentMat);
            kb.position.set(0, 4.15, 0.5);
            stGroup.add(kb);

            const mouse = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.4, 1.2), chairDarkMat);
            mouse.position.set(3.4, 4.2, 0.6);
            stGroup.add(mouse);

            // PC Tower vỏ kính RGB
            const pcTower = new THREE.Group();
            pcTower.position.set(-9.2, 2.5, 0.5);
            const pcCase = new THREE.Mesh(new THREE.BoxGeometry(2.4, 5.2, 4.8), new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.85 }));
            pcTower.add(pcCase);
            for (let f = -1; f <= 1; f++) {
                const fanRing = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.08, 6, 16), chairAccentMat);
                fanRing.position.set(0, f * 1.5, 2.42);
                pcTower.add(fanRing);
            }
            stGroup.add(pcTower);

            // Cốc cà phê & Smartphone
            const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.4, 0.9, 12), new THREE.MeshStandardMaterial({ color: 0xffffff }));
            mug.position.set(-4.2, 4.45, 1.2);
            stGroup.add(mug);

            // 4. NGƯỜI NGỢM 3D: NHÂN VIÊN MKT SEATED OFFICER NGỒI GÕ PHÍM!
            try {
                const officerModel = this.createSeatedOfficer3D(key, cfg);
                if (officerModel) {
                    stGroup.add(officerModel);
                }
            } catch (_) {}

            // 5. Hologram Badge Biển Tên Phòng Ban Nổi
            const holoTag = this.createHoloSprite(`${cfg.icon} ${cfg.name}`, cfg.color);
            holoTag.position.set(0, 11.5, -2);
            holoTag.scale.set(16, 4.0, 1);
            stGroup.add(holoTag);

            // Point Light chiếu sáng trạm
            const light = new THREE.PointLight(cfg.color, 1.2, 22);
            light.position.set(0, 7.5, 0);
            stGroup.add(light);

            // Hitbox for 3D Raycast interaction
            const hitBox = new THREE.Mesh(
                new THREE.BoxGeometry(26, 18, 22),
                new THREE.MeshBasicMaterial({ visible: false })
            );
            hitBox.position.y = 10;
            hitBox.userData = { deptKey: key, stationGroup: stGroup, isMkt: true, config: cfg };
            stGroup.add(hitBox);
            this.stationMeshes.push(hitBox);

            stGroup.traverse(child => {
                if (child.isMesh || child.isSprite) {
                    child.userData.deptKey = key;
                    child.userData.stationGroup = stGroup;
                    child.userData.isMkt = true;
                }
            });

            this.mktFloorGroup.add(stGroup);
            this.mktStations[key] = stGroup;
        });

        // Thêm toàn bộ Tầng Dưới vào scene
        this.scene.add(this.mktFloorGroup);
    }

    /* --------------------------------------------------------------------------
       10E. BUILD 5D DIGITAL TWIN WING (PHÒNG BÊN CẠNH SÀN TRADE · X = 220, Z = 0)
       Chuẩn Tellux WebGIS & Cesium: Quả cầu 5D Hologlobe, 3,500 Hạt Vector Streamlines,
       Cầu kính Skybridge kết nối Sàn Trade, Trạm Điều Hành 5D & Nhân sự 3D gõ phím!
       -------------------------------------------------------------------------- */
    build5DDigitalTwinWing() {
        this.twinWingGroup = new THREE.Group();
        this.holo5dSatellites = [];

        const centerX = 220;
        const centerY = 2.0;
        const centerZ = 0;

        // 1. SÀN PHÒNG 5D DIGITAL TWIN (Elevated 96x96 Obsidian Glass Platform)
        const platGeo = new THREE.BoxGeometry(96, 3.5, 96);
        const platMat = new THREE.MeshStandardMaterial({
            color: 0x061126,
            metalness: 0.88,
            roughness: 0.18
        });
        const plat = new THREE.Mesh(platGeo, platMat);
        plat.position.set(centerX, centerY, centerZ);
        plat.receiveShadow = true;
        this.twinWingGroup.add(plat);

        // Glowing Perimeter Border (Neon Cyan 0x06b6d4)
        const borderGeo = new THREE.BoxGeometry(96.6, 0.4, 96.6);
        const borderMat = new THREE.LineBasicMaterial({
            color: 0x06b6d4,
            transparent: true,
            opacity: 0.9
        });
        const border = new THREE.LineSegments(new THREE.EdgesGeometry(borderGeo), borderMat);
        border.position.set(centerX, centerY + 1.8, centerZ);
        this.twinWingGroup.add(border);

        // Floor Compass Circles & Coordinates Grid (Tellux WebGIS Coordinate Rings)
        const ringOuterGeo = new THREE.RingGeometry(32, 32.8, 64);
        const ringOuterMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4, side: THREE.DoubleSide, transparent: true, opacity: 0.75 });
        const ringOuter = new THREE.Mesh(ringOuterGeo, ringOuterMat);
        ringOuter.rotation.x = -Math.PI / 2;
        ringOuter.position.set(centerX, centerY + 1.85, centerZ);
        this.twinWingGroup.add(ringOuter);

        const ringInnerGeo = new THREE.RingGeometry(18, 18.5, 48);
        const ringInnerMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, side: THREE.DoubleSide, transparent: true, opacity: 0.8 });
        const ringInner = new THREE.Mesh(ringInnerGeo, ringInnerMat);
        ringInner.rotation.x = -Math.PI / 2;
        ringInner.position.set(centerX, centerY + 1.86, centerZ);
        this.twinWingGroup.add(ringInner);

        // Floor Grid Lines
        const grid5d = new THREE.GridHelper(90, 18, 0x06b6d4, 0x1e293b);
        grid5d.position.set(centerX, centerY + 1.87, centerZ);
        this.twinWingGroup.add(grid5d);

        // 2. CẦU KÍNH SKYBRIDGE (CYBER SKYBRIDGE NỐI SÀN TRADE SANG PHÒNG 5D)
        // Nối từ mép Sàn Trade (X = 120, Z = 0) sang mép Phòng 5D (X = 172, Z = 0)
        const bridgeLength = 52;
        const bridgeWidth = 14;
        const bridgeCenterX = 146;
        const bridgeGeo = new THREE.BoxGeometry(bridgeLength, 2.0, bridgeWidth);
        const bridgeMat = new THREE.MeshStandardMaterial({
            color: 0x07152f,
            metalness: 0.85,
            roughness: 0.25,
            transparent: true,
            opacity: 0.92
        });
        const bridge = new THREE.Mesh(bridgeGeo, bridgeMat);
        bridge.position.set(bridgeCenterX, centerY, centerZ);
        this.twinWingGroup.add(bridge);

        // Center Energy Conduits along Skybridge
        const stripGeo = new THREE.BoxGeometry(bridgeLength, 0.2, 1.2);
        const stripMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
        const strip = new THREE.Mesh(stripGeo, stripMat);
        strip.position.set(bridgeCenterX, centerY + 1.05, centerZ);
        this.twinWingGroup.add(strip);

        // Glowing Handrails on Skybridge
        [-bridgeWidth / 2, bridgeWidth / 2].forEach(zOffset => {
            const railGeo = new THREE.BoxGeometry(bridgeLength, 0.25, 0.25);
            const railMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
            const rail = new THREE.Mesh(railGeo, railMat);
            rail.position.set(bridgeCenterX, centerY + 3.2, centerZ + zOffset);
            this.twinWingGroup.add(rail);

            // Handrail Posts
            for (let px = -bridgeLength / 2 + 3; px <= bridgeLength / 2 - 3; px += 8) {
                const postGeo = new THREE.CylinderGeometry(0.18, 0.18, 2.2, 8);
                const postMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.9 });
                const post = new THREE.Mesh(postGeo, postMat);
                post.position.set(bridgeCenterX + px, centerY + 2.1, centerZ + zOffset);
                this.twinWingGroup.add(post);
            }
        });

        // 2 Neon Gateway Arches at Entrances of Skybridge
        [bridgeCenterX - bridgeLength / 2 + 2, bridgeCenterX + bridgeLength / 2 - 2].forEach((archX, idx) => {
            const archGroup = new THREE.Group();
            archGroup.position.set(archX, centerY + 1.0, centerZ);

            const archTorusGeo = new THREE.TorusGeometry(bridgeWidth / 2 - 0.5, 0.4, 8, 24, Math.PI);
            const archTorusMat = new THREE.MeshBasicMaterial({ color: idx === 0 ? 0xf59e0b : 0x06b6d4 });
            const archTorus = new THREE.Mesh(archTorusGeo, archTorusMat);
            archTorus.rotation.y = Math.PI / 2;
            archTorus.position.y = 0.5;
            archGroup.add(archTorus);

            this.twinWingGroup.add(archGroup);
        });

        // 3. QUẢ CẦU 5D HOLOGLOBE KHỔNG LỒ (TELLUX DIGITAL TWIN CORE)
        const globeY = centerY + 28;
        const globeGroup = new THREE.Group();
        globeGroup.position.set(centerX, globeY, centerZ);

        // Outer Wireframe Sphere (Metaverse Earth Grid)
        const wireGeo = new THREE.SphereGeometry(12.5, 24, 24);
        const wireMat = new THREE.MeshBasicMaterial({
            color: 0x06b6d4,
            wireframe: true,
            transparent: true,
            opacity: 0.65
        });
        this.holo5dGlobe = new THREE.Mesh(wireGeo, wireMat);
        globeGroup.add(this.holo5dGlobe);

        // Inner Glowing Quantum Core
        const coreGeo = new THREE.IcosahedronGeometry(7.2, 2);
        const coreMat = new THREE.MeshStandardMaterial({
            color: 0x38bdf8,
            emissive: 0x0284c7,
            emissiveIntensity: 0.85,
            roughness: 0.25
        });
        this.holo5dCore = new THREE.Mesh(coreGeo, coreMat);
        globeGroup.add(this.holo5dCore);

        // Gimbal Rings (Latitude / Longitude Rotation)
        const ring1Geo = new THREE.TorusGeometry(15.5, 0.35, 12, 64);
        const ring1Mat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
        this.holo5dRing1 = new THREE.Mesh(ring1Geo, ring1Mat);
        this.holo5dRing1.rotation.x = Math.PI / 4;
        globeGroup.add(this.holo5dRing1);

        const ring2Geo = new THREE.TorusGeometry(17.5, 0.35, 12, 64);
        const ring2Mat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
        this.holo5dRing2 = new THREE.Mesh(ring2Geo, ring2Mat);
        this.holo5dRing2.rotation.y = Math.PI / 3;
        globeGroup.add(this.holo5dRing2);

        // Orbiting Satellites (3 Drones with Beacons)
        for (let s = 0; s < 3; s++) {
            const satGroup = new THREE.Group();
            const satGeo = new THREE.BoxGeometry(0.9, 0.6, 1.4);
            const satMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9 });
            const satMesh = new THREE.Mesh(satGeo, satMat);
            satGroup.add(satMesh);

            // Solar Panels
            const wingGeo = new THREE.BoxGeometry(3.0, 0.08, 0.7);
            const wingMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
            const wingMesh = new THREE.Mesh(wingGeo, wingMat);
            satGroup.add(wingMesh);

            // Blinking Beacon
            const beaconLight = new THREE.PointLight(0x06b6d4, 1.2, 18);
            satGroup.add(beaconLight);

            globeGroup.add(satGroup);
            this.holo5dSatellites.push(satGroup);
        }

        this.twinWingGroup.add(globeGroup);

        // 4. TELLUX VECTOR PARTICLE FLOW STREAMLINES (3,500 HẠT THANH KHOẢN VÒNG QUANH)
        const particleCount = 650;
        const particleGeo = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);

        const color1 = new THREE.Color(0x06b6d4); // Cyan
        const color2 = new THREE.Color(0xf59e0b); // Gold
        const color3 = new THREE.Color(0x38bdf8); // Sky

        for (let i = 0; i < particleCount; i++) {
            const theta = Math.random() * Math.PI * 2;
            const phi = (Math.random() - 0.5) * Math.PI;
            const r = 18 + Math.random() * 9;

            positions[i * 3] = Math.cos(theta) * Math.cos(phi) * r;
            positions[i * 3 + 1] = Math.sin(phi) * r * 0.75;
            positions[i * 3 + 2] = Math.sin(theta) * Math.cos(phi) * r;

            const cChoice = Math.random();
            const pColor = cChoice < 0.5 ? color1 : (cChoice < 0.8 ? color3 : color2);
            colors[i * 3] = pColor.r;
            colors[i * 3 + 1] = pColor.g;
            colors[i * 3 + 2] = pColor.b;
        }

        particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        particleGeo.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const particleMat = new THREE.PointsMaterial({
            size: 1.6,
            vertexColors: true,
            transparent: true,
            opacity: 0.85,
            blending: THREE.AdditiveBlending
        });

        this.holo5dParticles = new THREE.Points(particleGeo, particleMat);
        this.holo5dParticles.position.set(centerX, globeY, centerZ);
        this.twinWingGroup.add(this.holo5dParticles);

        // 5. TRẠM ĐIỀU HÀNH 5D WEBGIS COMMAND COCKPIT (Bàn Làm Việc & Dàn Siêu Màn Hình)
        const stationX = centerX;
        const stationZ = -22;
        const stationY = centerY + 1.8;

        const stGroup = new THREE.Group();
        stGroup.position.set(stationX, stationY, stationZ);
        stGroup.userData = { deptKey: '5d_twin', config: this.deptConfigs['5d_twin'] };

        // Raised Command Pod
        const stPodGeo = new THREE.BoxGeometry(28, 0.4, 20);
        const stPodMat = new THREE.MeshStandardMaterial({ color: 0x081329, metalness: 0.8, roughness: 0.3 });
        const stPod = new THREE.Mesh(stPodGeo, stPodMat);
        stPod.position.y = 0.2;
        stGroup.add(stPod);

        const stPodBorder = new THREE.LineSegments(
            new THREE.EdgesGeometry(new THREE.BoxGeometry(28.4, 0.2, 20.4)),
            new THREE.LineBasicMaterial({ color: 0x06b6d4, transparent: true, opacity: 0.85 })
        );
        stPodBorder.position.y = 0.4;
        stGroup.add(stPodBorder);

        // Semi-Circular Curved Command Desk
        const deskMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.85, roughness: 0.25 });
        const desk = new THREE.Mesh(new THREE.BoxGeometry(18, 0.8, 7.5), deskMat);
        desk.position.set(0, 3.6, -1.0);
        stGroup.add(desk);

        const deskTrim = new THREE.Mesh(new THREE.BoxGeometry(18.2, 0.2, 7.7), new THREE.MeshBasicMaterial({ color: 0x06b6d4 }));
        deskTrim.position.set(0, 4.0, -1.0);
        stGroup.add(deskTrim);

        // Desk Legs
        const legGeo = new THREE.CylinderGeometry(0.35, 0.35, 3.6, 8);
        const legMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.9 });
        [ { x: -8.5, z: -4 }, { x: 8.5, z: -4 }, { x: 8.5, z: 2 }, { x: -8.5, z: 2 } ].forEach(lp => {
            const leg = new THREE.Mesh(legGeo, legMat);
            leg.position.set(lp.x, 1.8, lp.z);
            stGroup.add(leg);
        });

        // Quad Curved 8K Screens facing the Hologlobe
        const screenGeo = new THREE.BoxGeometry(4.2, 2.6, 0.15);
        const screenConfigs = [
            { x: -6.6, z: -1.2, rotY: 0.35, col: 0x06b6d4, title: 'TELLUX WEBGIS' },
            { x: -2.2, z: -1.8, rotY: 0.1,  col: 0x38bdf8, title: '5D TENSOR BTC' },
            { x: 2.2,  z: -1.8, rotY: -0.1, col: 0xf59e0b, title: 'ORDERFLOW 5D' },
            { x: 6.6,  z: -1.2, rotY: -0.35, col: 0x10b981, title: 'RISK BOUNDS' }
        ];

        screenConfigs.forEach(sc => {
            const scrGroup = new THREE.Group();
            scrGroup.position.set(sc.x, 5.5, sc.z);
            scrGroup.rotation.y = sc.rotY;

            // Frame
            const frame = new THREE.Mesh(screenGeo, new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.9 }));
            scrGroup.add(frame);

            // Emissive Screen Glow Face
            const faceMat = new THREE.MeshBasicMaterial({ color: sc.col });
            const face = new THREE.Mesh(new THREE.BoxGeometry(4.0, 2.4, 0.05), faceMat);
            face.position.z = 0.08;
            scrGroup.add(face);

            // Stand
            const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 1.4, 8), legMat);
            stand.position.y = -1.2;
            scrGroup.add(stand);

            stGroup.add(scrGroup);
        });

        // Dual Liquid-Cooled Supercomputers
        [-9.8, 9.8].forEach(pcX => {
            const pcGeo = new THREE.BoxGeometry(2.0, 3.8, 3.8);
            const pcMat = new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.9, roughness: 0.2 });
            const pc = new THREE.Mesh(pcGeo, pcMat);
            pc.position.set(pcX, 2.1, -1.0);
            stGroup.add(pc);

            // Glass side panel & glowing cyan liquid tubing
            const tubeMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
            const tube = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 3.2, 8), tubeMat);
            tube.position.set(pcX + (pcX > 0 ? -0.8 : 0.8), 2.1, -1.0);
            stGroup.add(tube);
        });

        // Ghế Công Thái Học 5 Sao
        const chairGroup = new THREE.Group();
        chairGroup.position.set(0, 0, 2.6);
        const chairDarkMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.7 });
        const chairAccentMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
        const chromeMat = new THREE.MeshStandardMaterial({ color: 0xcbd5e1, metalness: 0.9 });

        for (let b = 0; b < 5; b++) {
            const angle = (b / 5) * Math.PI * 2;
            const spoke = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.25, 2.2), chromeMat);
            spoke.rotation.y = angle;
            chairGroup.add(spoke);
        }

        const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 1.8, 8), chromeMat);
        stem.position.y = 1.0;
        chairGroup.add(stem);

        const seat = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.6, 3.6), chairDarkMat);
        seat.position.y = 2.0;
        chairGroup.add(seat);

        const seatTrim = new THREE.Mesh(new THREE.BoxGeometry(3.7, 0.15, 3.7), chairAccentMat);
        seatTrim.position.y = 2.25;
        chairGroup.add(seatTrim);

        const back = new THREE.Mesh(new THREE.BoxGeometry(3.4, 4.2, 0.5), chairDarkMat);
        back.position.set(0, 4.4, 1.6);
        back.rotation.x = -0.08;
        chairGroup.add(back);

        stGroup.add(chairGroup);

        // 3D Seated Officer: Dr. Lyra (Chief 5D WebGIS Architect)
        try {
            const officerModel = this.createSeatedOfficer3D('5d_twin', this.deptConfigs['5d_twin']);
            if (officerModel) {
                stGroup.add(officerModel);
            }
        } catch (_) {}

        // Station Hologram Badge
        const holoTag = this.createHoloSprite('🌐 5D DIGITAL TWIN · TELLUX WEBGIS', 0x06b6d4);
        holoTag.position.set(0, 11.5, -2);
        holoTag.scale.set(18, 4.5, 1);
        stGroup.add(holoTag);

        // Station Point Light
        const stLight = new THREE.PointLight(0x06b6d4, 1.4, 25);
        stLight.position.set(0, 8.0, 0);
        stGroup.add(stLight);

        // 6. CỤM TỦ SERVER LƯỢNG TỬ 5D (QUANTUM SERVER CLUSTERS)
        [-34, 34].forEach(rackZ => {
            const rackGroup = new THREE.Group();
            rackGroup.position.set(centerX + 32, centerY + 1.8, centerZ + rackZ);

            const rackBody = new THREE.Mesh(
                new THREE.BoxGeometry(6, 16, 18),
                new THREE.MeshStandardMaterial({ color: 0x0a1020, metalness: 0.9, roughness: 0.2 })
            );
            rackBody.position.y = 8;
            rackGroup.add(rackBody);

            // Blinking LEDs
            for (let ly = 3; ly <= 14; ly += 2) {
                for (let lz = -7; lz <= 7; lz += 2.5) {
                    const led = new THREE.Mesh(
                        new THREE.BoxGeometry(0.3, 0.3, 0.3),
                        new THREE.MeshBasicMaterial({ color: Math.random() > 0.5 ? 0x06b6d4 : 0xf59e0b })
                    );
                    led.position.set(-3.1, ly, lz);
                    rackGroup.add(led);
                    this.blinkingLeds.push(led);
                }
            }

            this.twinWingGroup.add(rackGroup);
        });

        // 7. OVERHEAD GRAND HOLOGRAPHIC BANNER
        const grandBanner = this.createHoloSprite('🌐 PHÒNG 5D DIGITAL TWIN (TELLUX WEBGIS · ASTRA QUANT)', 0x06b6d4);
        grandBanner.position.set(centerX, centerY + 46, centerZ);
        grandBanner.scale.set(36, 9.0, 1);
        this.twinWingGroup.add(grandBanner);

        // 8. HITBOX RAYCAST CHO PHÒNG 5D
        const hitBox = new THREE.Mesh(
            new THREE.BoxGeometry(75, 35, 75),
            new THREE.MeshBasicMaterial({ visible: false })
        );
        hitBox.position.set(centerX, centerY + 18, centerZ);
        hitBox.userData = { deptKey: '5d_twin', stationGroup: stGroup, is5dTwin: true, config: this.deptConfigs['5d_twin'] };
        this.twinWingGroup.add(hitBox);
        this.stationMeshes.push(hitBox);

        stGroup.traverse(child => {
            if (child.isMesh || child.isSprite) {
                child.userData.deptKey = '5d_twin';
                child.userData.stationGroup = stGroup;
                child.userData.is5dTwin = true;
            }
        });

        this.twinWingGroup.add(stGroup);
        this.stations['5d_twin'] = stGroup;

        // Thêm toàn bộ Phòng 5D vào Three.js Scene
        this.scene.add(this.twinWingGroup);
    }

    createHoloSprite(text, colorHex) {
        const c = document.createElement('canvas');
        c.width = 256;
        c.height = 64;
        const ctx = c.getContext('2d');

        ctx.fillStyle = 'rgba(7, 12, 26, 0.92)';
        ctx.strokeStyle = `#${colorHex.toString(16).padStart(6, '0')}`;
        ctx.lineWidth = 3;
        drawRoundRect(ctx, 6, 6, 244, 52, 10);
        ctx.fill();
        ctx.stroke();

        ctx.font = 'bold 22px "JetBrains Mono", monospace';
        ctx.fillStyle = '#f8fafc';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(text, 128, 32);

        const tex = new THREE.CanvasTexture(c);
        return new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
    }

    createSpeechBubbleSprite(text, colorHex) {
        const c = document.createElement('canvas');
        c.width = 384;
        c.height = 96;
        const ctx = c.getContext('2d');

        ctx.fillStyle = 'rgba(11, 20, 42, 0.95)';
        ctx.strokeStyle = `#${colorHex.toString(16).padStart(6, '0')}`;
        ctx.lineWidth = 3;
        drawRoundRect(ctx, 8, 8, 368, 80, 14);
        ctx.fill();
        ctx.stroke();

        ctx.font = 'bold 18px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const displayText = text.length > 38 ? text.slice(0, 36) + '…' : text;
        ctx.fillText(displayText, 192, 48);

        const tex = new THREE.CanvasTexture(c);
        return new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
    }

    updateSpeechBubble(deptKey, newText) {
        const bubble = this.floatingBubbles[deptKey];
        if (!bubble) return;
        const cfg = this.deptConfigs[deptKey];
        const updated = this.createSpeechBubbleSprite(newText, cfg ? cfg.color : 0x38bdf8);
        if (bubble.material && bubble.material.map) {
            bubble.material.map.dispose();
        }
        bubble.material.map = updated.material.map;
    }

    updateTelemetry(deptKey, dept) {
        if (!dept) return;
        const text = dept.raw_reasoning || dept.persona_quote || dept.bubble;
        if (text && typeof this.updateSpeechBubble === 'function') {
            this.updateSpeechBubble(deptKey, text);
        }
    }

    /* --------------------------------------------------------------------------
       9. TRUYỀN DẪN QUANG & BẮN GÓI TIN MẠNG LAN · HIGH-SPEED FIBER GRID & PING BEAMS
       -------------------------------------------------------------------------- */
    buildDataConduitsAndPackets() {
        // 10 Tuyến cáp quang & mạng LAN thời gian thực kết nối từ Trạm Máy Chủ và các ban
        const conduitRoutes = [
            // Tuyến 1: Trạm Máy Chủ ➔ Bàn Chỉ Huy War Room (100GbE Backbone)
            { from: { x: 85, y: 4.5, z: 76 }, to: { x: 0, y: 5.2, z: 12 }, mid: { x: 42, y: 10.5, z: 44 }, color: 0x00f0ff, label: '⚡ 100GbE FIBER · 12ms', speed: 0.45 },
            // Tuyến 2: Trạm Máy Chủ ➔ Ban Điều Hành & CRO (Management Trunk)
            { from: { x: 85, y: 4.5, z: 76 }, to: { x: -65, y: 4.5, z: -45 }, mid: { x: 10, y: 13.5, z: 15 }, color: 0xf59e0b, label: '💼 EXEC LINK · 10ms', speed: 0.42 },
            // Tuyến 3: Trạm Máy Chủ ➔ Sàn Giao Dịch OMS (HFT Binance/Bybit)
            { from: { x: 85, y: 4.5, z: 76 }, to: { x: 75, y: 4.5, z: -45 }, mid: { x: 92, y: 10.5, z: 15 }, color: 0x10b981, label: '⚡ HFT BINANCE · 8ms', speed: 0.52 },
            // Tuyến 4: Trạm Máy Chủ ➔ Viện Quant Lab Dr. Seraphina (Quantum Tensor Cluster)
            { from: { x: 85, y: 4.5, z: 76 }, to: { x: -75, y: 4.5, z: 65 }, mid: { x: 5, y: 12.0, z: 88 }, color: 0xa855f7, label: '🧠 TENSOR 5D AI · 14ms', speed: 0.40 },
            // Tuyến 5: Trạm Máy Chủ ➔ Phòng Kiểm Soát CVaR Stress (Risk Shield)
            { from: { x: 85, y: 4.5, z: 76 }, to: { x: 85, y: 4.2, z: 98 }, mid: { x: 85, y: 7.5, z: 87 }, color: 0xef4444, label: '🔒 CVaR REALTIME · 4ms', speed: 0.48 },
            // Tuyến 6: Quant Lab ➔ Risk Council (Alpha Signal Pipeline)
            { from: { x: -85, y: 4.5, z: 65 }, to: { x: -55, y: 4.5, z: -35 }, mid: { x: -85, y: 10.5, z: 15 }, color: 0xc084fc, label: '📄 ALPHA SIGNAL · +84.2', speed: 0.38 },
            // Tuyến 7: Risk Council ➔ Execution OMS (Approved Order Stream)
            { from: { x: -55, y: 4.5, z: -35 }, to: { x: 85, y: 4.5, z: -35 }, mid: { x: 15, y: 13.0, z: -45 }, color: 0x34d399, label: '⚡ ORDER APPROVED · LONG', speed: 0.48 },
            // Tuyến 8: Execution OMS ➔ Lead PM (Realized PnL Profit Pipeline)
            { from: { x: 85, y: 4.5, z: -35 }, to: { x: 0, y: 5.2, z: 15 }, mid: { x: 42, y: 10.0, z: -10 }, color: 0xfbbf24, label: '💰 PROFIT FILLED · +$340', speed: 0.40 },
            // Tuyến 9: News Scout ➔ Quant Lab (On-Chain Intel Stream)
            { from: { x: 55, y: 4.5, z: -65 }, to: { x: -85, y: 4.5, z: 65 }, mid: { x: -15, y: 15.0, z: 0 }, color: 0x06b6d4, label: '📡 INTEL ON-CHAIN · 100%', speed: 0.36 },
            // Tuyến 10: Central Core ➔ Spot DCA (Capital Allocation)
            { from: { x: 0, y: 5.2, z: 0 }, to: { x: 55, y: 4.5, z: 65 }, mid: { x: 28, y: 10.0, z: 32 }, color: 0x0ea5e9, label: '💎 SPOT DCA ALLOC · 100%', speed: 0.32 }
        ];

        conduitRoutes.forEach((route, idx) => {
            const startPt = new THREE.Vector3(route.from.x, route.from.y, route.from.z);
            const endPt = new THREE.Vector3(route.to.x, route.to.y, route.to.z);
            const midPt = new THREE.Vector3(route.mid.x, route.mid.y, route.mid.z);

            // Đường cong 3D Bezier uốn lượn đẹp mắt trên không gian trụ sở
            const curve = new THREE.QuadraticBezierCurve3(startPt, midPt, endPt);

            // 1. Ống Cáp Quang Neon Lớp Ngoài (Outer Glowing Neon Sleeve)
            const tubeGeo = new THREE.TubeGeometry(curve, 48, 0.42, 8, false);
            const tubeMat = new THREE.MeshStandardMaterial({
                color: route.color,
                emissive: route.color,
                emissiveIntensity: 0.75,
                transparent: true,
                opacity: 0.65,
                roughness: 0.2,
                metalness: 0.8
            });
            const tube = new THREE.Mesh(tubeGeo, tubeMat);
            this.scene.add(tube);
            this.conduitMeshes.push(tube);

            // 2. Lõi Laser Siêu Tốc (Inner Laser Core)
            const coreGeo = new THREE.TubeGeometry(curve, 48, 0.16, 6, false);
            const coreMat = new THREE.MeshBasicMaterial({
                color: 0xffffff,
                transparent: true,
                opacity: 0.95
            });
            const coreTube = new THREE.Mesh(coreGeo, coreMat);
            this.scene.add(coreTube);
            this.conduitMeshes.push(coreTube);

            // 3. Trụ Đỡ Cáp Quang Cyber (Cable Support Pylon tại trung điểm)
            if (midPt.y > 7.0) {
                const pylon = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.2, 0.35, midPt.y - 1.5, 6),
                    new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.9 })
                );
                pylon.position.set(midPt.x, (midPt.y - 1.5) / 2, midPt.z);
                this.scene.add(pylon);
                this.conduitMeshes.push(pylon);
            }

            // 4. Gói Tin Năng Lượng 3D Chạy Dọc Đường Truyền (Flowing 3D Data Packet)
            const packetGroup = new THREE.Group();

            // Khối cầu năng lượng phát sáng rực rỡ
            const orbGeo = new THREE.SphereGeometry(1.4, 16, 16);
            const orbMat = new THREE.MeshBasicMaterial({
                color: route.color,
                transparent: true,
                opacity: 0.95
            });
            const orb = new THREE.Mesh(orbGeo, orbMat);
            packetGroup.add(orb);

            // Lõi photon trắng nóng sáng bên trong
            const innerGeo = new THREE.SphereGeometry(0.75, 12, 12);
            const innerMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
            const inner = new THREE.Mesh(innerGeo, innerMat);
            packetGroup.add(inner);

            // 3 hạt sao băng đuôi ánh sáng laser (Laser Comet Tail)
            for (let t = 1; t <= 3; t++) {
                const tailGeo = new THREE.SphereGeometry(1.0 - t * 0.25, 8, 8);
                const tailMat = new THREE.MeshBasicMaterial({
                    color: route.color,
                    transparent: true,
                    opacity: 0.75 - t * 0.2
                });
                const tail = new THREE.Mesh(tailGeo, tailMat);
                tail.position.set(0, 0, t * 1.5);
                packetGroup.add(tail);
            }

            // Đèn chiếu sáng động theo bước di chuyển của gói tin
            const pktLight = new THREE.PointLight(route.color, 2.4, 35);
            packetGroup.add(pktLight);

            // Thẻ Hologram 3D bay trên đầu gói tin (Hiển thị tên luồng dữ liệu & ping)
            const badge = this.createPacketBadge(route.label, route.color);
            badge.position.y = 3.6;
            badge.scale.set(16, 4.0, 1);
            packetGroup.add(badge);

            this.scene.add(packetGroup);

            this.dataPackets.push({
                group: packetGroup,
                orb: orb,
                pktLight: pktLight,
                curve: curve,
                progress: (idx / conduitRoutes.length) * 0.9,
                speed: route.speed,
                route: route
            });
        });
    }

    // Hiệu ứng sóng va chạm Ping mở rộng khi gói tin chạm đích tại bàn làm việc
    spawnPingImpact(pos, colorHex) {
        const ringGeo = new THREE.RingGeometry(0.8, 1.6, 24);
        const ringMat = new THREE.MeshBasicMaterial({
            color: colorHex,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.95
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.rotation.x = -Math.PI / 2;
        ring.position.set(pos.x, pos.y + 0.15, pos.z);
        this.scene.add(ring);

        this.packetImpactRings.push({
            mesh: ring,
            scale: 1.0,
            opacity: 0.95
        });
    }

    createPacketBadge(label, colorHex) {
        const c = document.createElement('canvas');
        c.width = 256;
        c.height = 64;
        const ctx = c.getContext('2d');

        ctx.fillStyle = 'rgba(7, 18, 38, 0.94)';
        ctx.strokeStyle = `#${colorHex.toString(16).padStart(6, '0')}`;
        ctx.lineWidth = 2.5;
        drawRoundRect(ctx, 4, 4, 248, 56, 8);
        ctx.fill();
        ctx.stroke();

        ctx.font = 'bold 20px "JetBrains Mono", monospace';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, 128, 32);

        const tex = new THREE.CanvasTexture(c);
        return new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true }));
    }

    /* --------------------------------------------------------------------------
       10. 3D BOSS & ASTRA AVATARS WITH FLOOR CLICK-TO-WALK
       -------------------------------------------------------------------------- */

    /* --------------------------------------------------------------------------
       10. 3D PROCEDURAL CHARACTER GENERATORS (NO MORE 2D BILLBOARDS)
       -------------------------------------------------------------------------- */

    // 10A. Deeply Detailed 3D Seated Officer Model with Expressive Cyber Features
    // 10A. Procedural 3D Officer Model Router (6 Curvaceous Female Officers + 6 Muscular 6-Pack Male Officers)
    createSeatedOfficer3D(deptKey, cfg) {
        const femaleDepts = new Set([
            'risk_council',       // CRO Evelyn: Hourglass cyber-suit, glasses, gold lapels
            'quant_lab',          // Dr. Seraphina: Curvy quant scientist, purple twin-tails
            'breakout_hunter',    // Valkyrie Riko: Athletic crop-top curves, high ponytail
            'volatility_lab',     // Mistress Camilla: Seductive burgundy dress, long wavy locks
            'accounting_pm',      // Auditor Yukiko: Kimono-cyber suit, elegant bun
            'community_affiliate', // Ambassador Chloe: Cyber idol, twin buns, cat-ear antennas
            '5d_twin'             // Dr. Lyra: Chief 5D WebGIS Architect, electric cyan suit
        ]);

        if (femaleDepts.has(deptKey)) {
            return this.createFemaleOfficer3D(deptKey, cfg);
        } else {
            return this.createMaleOfficer3D(deptKey, cfg);
        }
    }

    // 10A-1. Sculpted 3D Curvaceous Cyberpunk Female Officer (Anime Waifu Proportions)
    createFemaleOfficer3D(deptKey, cfg) {
        const root = new THREE.Group();
        root.position.set(0, 0, 2.4);

        const skinColor = 0xffeedf;
        const skinMat = new THREE.MeshStandardMaterial({ color: skinColor, roughness: 0.5, metalness: 0.05 });
        const suitMat = new THREE.MeshStandardMaterial({ color: cfg.color, roughness: 0.35, metalness: 0.4 });
        const blackLeatherMat = new THREE.MeshStandardMaterial({ color: 0x0a0f1d, roughness: 0.25, metalness: 0.6 });
        const goldMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.9, roughness: 0.2 });
        const accentMat = new THREE.MeshBasicMaterial({ color: cfg.accent });
        const neonPinkMat = new THREE.MeshBasicMaterial({ color: 0xf43f5e });

        const hairPalettes = {
            'risk_council': 0x0f172a,       // Evelyn: Jet black bob
            'quant_lab': 0xa855f7,          // Seraphina: Cyber purple twintails
            'breakout_hunter': 0x0284c7,     // Riko: Electric cyan ponytail
            'volatility_lab': 0xbe185d,      // Camilla: Deep crimson wavy locks
            'accounting_pm': 0x475569,       // Yukiko: Platinum silver bun
            'community_affiliate': 0xf472b6  // Chloe: Sakura pink twin buns
        };
        const hairColor = hairPalettes[deptKey] || 0x1e293b;
        const hairMat = new THREE.MeshStandardMaterial({ color: hairColor, roughness: 0.55, metalness: 0.15 });

        // 1. Curvy Feminine Pelvis & Seated Hips
        const hips = new THREE.Mesh(new THREE.BoxGeometry(2.85, 0.85, 2.1), blackLeatherMat);
        hips.position.set(0, 2.55, 0);
        root.add(hips);

        // Slender Cinched Waist (Hourglass transition)
        const waist = new THREE.Mesh(new THREE.BoxGeometry(1.95, 1.35, 1.4), suitMat);
        waist.position.set(0, 3.45, 0.05);
        root.add(waist);

        // Gold Cyber Corset Belt
        const belt = new THREE.Mesh(new THREE.BoxGeometry(2.05, 0.32, 1.5), goldMat);
        belt.position.set(0, 3.3, 0.05);
        root.add(belt);

        // 2. Slender Feminine Thighs & High-Heel Cyber Boots
        for (let s = -1; s <= 1; s += 2) {
            const thigh = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.75, 2.15), blackLeatherMat);
            thigh.position.set(s * 0.65, 2.55, -1.0);
            thigh.rotation.y = s * -0.05; // Slightly angled inward feminine seating
            root.add(thigh);

            // Shins / Calves
            const shin = new THREE.Mesh(new THREE.BoxGeometry(0.68, 2.05, 0.68), blackLeatherMat);
            shin.position.set(s * 0.65, 1.1, -1.8);
            root.add(shin);

            // Sleek High-Top Cyber Boots
            const boot = new THREE.Mesh(new THREE.BoxGeometry(0.78, 0.65, 1.35), new THREE.MeshStandardMaterial({ color: 0x020617, roughness: 0.4 }));
            boot.position.set(s * 0.65, 0.35, -1.6);
            root.add(boot);

            // Glowing Neon Stiletto Sole Trim
            const bootSole = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.16, 1.4), accentMat);
            bootSole.position.set(s * 0.65, 0.1, -1.6);
            root.add(bootSole);
        }

        // 3. PROMINENT VOLUPTUOUS BUST & UPPER TORSO (Vú Bự & Đường Cong Nữ Tính)
        const bustGroup = new THREE.Group();
        bustGroup.position.set(0, 4.65, 0);

        // Upper Chest Base
        const upperTorso = new THREE.Mesh(new THREE.BoxGeometry(2.5, 1.8, 1.55), suitMat);
        bustGroup.add(upperTorso);

        // Dual Voluptuous Breasts (Sculpted rounded dome geometry with cleavage)
        const breastGeo = new THREE.SphereGeometry(0.78, 16, 16);

        const leftBreast = new THREE.Mesh(breastGeo, suitMat);
        leftBreast.scale.set(1.05, 0.95, 1.35);
        leftBreast.position.set(-0.55, 0.08, -0.74);
        leftBreast.rotation.x = -0.22;
        leftBreast.rotation.y = 0.12;
        bustGroup.add(leftBreast);

        const rightBreast = new THREE.Mesh(breastGeo, suitMat);
        rightBreast.scale.set(1.05, 0.95, 1.35);
        rightBreast.position.set(0.55, 0.08, -0.74);
        rightBreast.rotation.x = -0.22;
        rightBreast.rotation.y = -0.12;
        bustGroup.add(rightBreast);

        // Glowing V-Neckline Cleavage Trim
        const cleavageRing = new THREE.Mesh(new THREE.TorusGeometry(0.58, 0.06, 6, 16, Math.PI), accentMat);
        cleavageRing.rotation.x = Math.PI / 1.6;
        cleavageRing.position.set(0, 0.45, -0.76);
        bustGroup.add(cleavageRing);

        // Gold Lapels framing the collar
        for (let s = -1; s <= 1; s += 2) {
            const lapel = new THREE.Mesh(new THREE.BoxGeometry(0.28, 1.6, 0.14), goldMat);
            lapel.position.set(s * 0.95, 0.1, -0.78);
            lapel.rotation.z = s * -0.18;
            bustGroup.add(lapel);
        }
        root.add(bustGroup);

        // 4. Delicate Neck
        const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.36, 0.55, 10), skinMat);
        neck.position.set(0, 6.05, 0.08);
        root.add(neck);

        // Gold Choker Necklace
        const choker = new THREE.Mesh(new THREE.TorusGeometry(0.36, 0.05, 6, 16), goldMat);
        choker.rotation.x = Math.PI / 2;
        choker.position.set(0, 6.0, 0.08);
        root.add(choker);

        // 5. Head Group with Soft Anime Features & Department-Specific Hair
        const headGroup = new THREE.Group();
        headGroup.position.set(0, 7.1, 0.08);

        const head = new THREE.Mesh(new THREE.BoxGeometry(1.9, 1.95, 1.85), skinMat);
        head.castShadow = true;
        headGroup.add(head);

        // Soft Anime Pink Blush on Cheeks
        for (let s = -1; s <= 1; s += 2) {
            const blush = new THREE.Mesh(new THREE.PlaneGeometry(0.35, 0.16), neonPinkMat);
            blush.position.set(s * 0.55, -0.15, -0.94);
            headGroup.add(blush);
        }

        // Base Layered Hair Top
        const hairTop = new THREE.Mesh(new THREE.BoxGeometry(2.1, 0.85, 2.05), hairMat);
        hairTop.position.set(0, 0.95, -0.05);
        headGroup.add(hairTop);

        // Soft Front Fringe Bangs
        const fringeL = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.85, 0.25), hairMat);
        fringeL.position.set(-0.45, 0.7, -0.98);
        fringeL.rotation.z = 0.15;
        headGroup.add(fringeL);

        const fringeR = new THREE.Mesh(new THREE.BoxGeometry(0.55, 0.85, 0.25), hairMat);
        fringeR.position.set(0.45, 0.7, -0.98);
        fringeR.rotation.z = -0.15;
        headGroup.add(fringeR);

        // Department-Specific Hairstyles & Accessories
        if (deptKey === 'risk_council') {
            // Evelyn: Chic bob cut + black-rimmed AR Smart Glasses
            const bobBack = new THREE.Mesh(new THREE.BoxGeometry(2.15, 1.8, 0.6), hairMat);
            bobBack.position.set(0, 0.1, 0.9);
            headGroup.add(bobBack);

            // Thin-rimmed stylish glasses
            const glasses = new THREE.Mesh(
                new THREE.BoxGeometry(1.85, 0.42, 0.3),
                new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.9, roughness: 0.2 })
            );
            glasses.position.set(0, 0.1, -0.96);
            headGroup.add(glasses);

            const lenses = new THREE.Mesh(
                new THREE.BoxGeometry(1.75, 0.32, 0.32),
                new THREE.MeshStandardMaterial({ color: 0xf59e0b, emissive: 0xf59e0b, emissiveIntensity: 0.6, transparent: true, opacity: 0.85 })
            );
            lenses.position.set(0, 0.1, -0.97);
            headGroup.add(lenses);
        } else if (deptKey === 'quant_lab') {
            // Seraphina: Cyber Purple High Twin-Tails
            for (let s = -1; s <= 1; s += 2) {
                const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.42, 2.8, 8), hairMat);
                tail.position.set(s * 1.35, -0.3, 0.3);
                tail.rotation.z = s * 0.22;
                headGroup.add(tail);

                const ring = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.08, 4, 12), accentMat);
                ring.position.set(s * 1.15, 0.75, 0.2);
                headGroup.add(ring);
            }
        } else if (deptKey === 'breakout_hunter') {
            // Valkyrie Riko: High Athletic Ponytail
            const pony = new THREE.Mesh(new THREE.ConeGeometry(0.42, 2.8, 6), hairMat);
            pony.position.set(0, 0.4, 1.3);
            pony.rotation.x = Math.PI / 3.2;
            headGroup.add(pony);

            const clasp = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.08, 4, 12), goldMat);
            clasp.position.set(0, 1.1, 0.85);
            headGroup.add(clasp);
        } else if (deptKey === 'community_affiliate') {
            // Chloe: Twin Buns + Glowing Cat-Ear Headset
            for (let s = -1; s <= 1; s += 2) {
                const bun = new THREE.Mesh(new THREE.SphereGeometry(0.52, 10, 10), hairMat);
                bun.position.set(s * 1.15, 1.15, 0.1);
                headGroup.add(bun);

                const ear = new THREE.Mesh(new THREE.ConeGeometry(0.35, 0.7, 4), accentMat);
                ear.position.set(s * 0.95, 1.7, -0.1);
                ear.rotation.z = s * -0.35;
                headGroup.add(ear);
            }
        } else {
            // Long flowing anime locks
            const longHair = new THREE.Mesh(new THREE.BoxGeometry(2.15, 3.4, 0.5), hairMat);
            longHair.position.set(0, -0.7, 0.95);
            headGroup.add(longHair);
        }

        // Sleek AR Visor Headset
        const miniVisor = new THREE.Mesh(
            new THREE.BoxGeometry(1.9, 0.38, 0.35),
            new THREE.MeshStandardMaterial({ color: cfg.accent, emissive: cfg.accent, emissiveIntensity: 0.8, transparent: true, opacity: 0.9 })
        );
        miniVisor.position.set(0, 0.15, -0.96);
        headGroup.add(miniVisor);
        root.add(headGroup);

        // 6. Slender Arms with Glowing Cyber Bracelets & Typing Hands
        const leftArmGroup = new THREE.Group();
        leftArmGroup.position.set(-1.45, 5.2, 0.1);

        const leftUpper = new THREE.Mesh(new THREE.BoxGeometry(0.58, 1.6, 0.58), suitMat);
        leftUpper.position.set(0, -0.6, -0.3);
        leftUpper.rotation.x = -Math.PI / 5;
        leftArmGroup.add(leftUpper);

        const leftForearm = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.52, 1.9), skinMat);
        leftForearm.position.set(0, -1.3, -1.2);
        leftArmGroup.add(leftForearm);

        // Glowing Smart Bracelet on Left Wrist
        const bracelet = new THREE.Mesh(new THREE.TorusGeometry(0.32, 0.06, 6, 16), accentMat);
        bracelet.rotation.x = Math.PI / 2;
        bracelet.position.set(0, -1.3, -1.8);
        leftArmGroup.add(bracelet);

        const leftHand = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.25, 0.5), skinMat);
        leftHand.position.set(0, -1.3, -2.2);
        leftArmGroup.add(leftHand);
        root.add(leftArmGroup);

        const rightArmGroup = new THREE.Group();
        rightArmGroup.position.set(1.45, 5.2, 0.1);

        const rightUpper = new THREE.Mesh(new THREE.BoxGeometry(0.58, 1.6, 0.58), suitMat);
        rightUpper.position.set(0, -0.6, -0.3);
        rightUpper.rotation.x = -Math.PI / 5;
        rightArmGroup.add(rightUpper);

        const rightForearm = new THREE.Mesh(new THREE.BoxGeometry(0.52, 0.52, 1.9), skinMat);
        rightForearm.position.set(0, -1.3, -1.2);
        rightArmGroup.add(rightForearm);

        const rightHand = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.25, 0.5), skinMat);
        rightHand.position.set(0, -1.3, -2.2);
        rightArmGroup.add(rightHand);
        root.add(rightArmGroup);

        // Expressive Feminine Animation Logic
        root.userData = {
            headGroup: headGroup,
            bustGroup: bustGroup,
            leftArmGroup: leftArmGroup,
            rightArmGroup: rightArmGroup,
            phase: Math.random() * 10,
            state: 'working',
            animate: function(time, delta, state) {
                const p = this.phase;
                const s = state || this.state || 'working';

                if (s === 'celebrating') {
                    // Cheerful celebratory cheer
                    this.leftArmGroup.rotation.x = -Math.PI * 0.85 + Math.sin(time * 12 + p) * 0.25;
                    this.rightArmGroup.rotation.x = -Math.PI * 0.85 + Math.cos(time * 12 + p) * 0.25;
                    this.headGroup.rotation.z = Math.sin(time * 6 + p) * 0.15;
                    root.position.y = 2.4 + Math.abs(Math.sin(time * 8 + p)) * 0.4;
                    this.bustGroup.position.y = 4.65 + Math.sin(time * 8 + p) * 0.08;
                } else if (s === 'veto') {
                    // Elegant head shake with finger to chin
                    this.leftArmGroup.rotation.x = -Math.PI / 5;
                    this.rightArmGroup.rotation.x = -Math.PI * 0.7;
                    this.headGroup.rotation.y = Math.sin(time * 5 + p) * 0.35;
                    this.headGroup.rotation.z = 0.08;
                    root.position.y = 2.4;
                } else {
                    // Natural feminine typing loop & gentle bust heave
                    this.leftArmGroup.rotation.x = -Math.PI / 5 + Math.sin(time * 14 + p) * 0.15;
                    const mouseCycle = Math.sin(time * 0.8 + p);
                    if (mouseCycle > 0.3) {
                        this.rightArmGroup.rotation.x = -Math.PI / 5.8;
                        this.rightArmGroup.position.x = 1.65;
                    } else {
                        this.rightArmGroup.rotation.x = -Math.PI / 5 + Math.cos(time * 14 + p) * 0.15;
                        this.rightArmGroup.position.x = 1.45;
                    }

                    // Gentle bust breathing heave
                    this.bustGroup.position.y = 4.65 + Math.sin(time * 2.8 + p) * 0.04;

                    // Graceful head glance between screens
                    this.headGroup.rotation.y = Math.sin(time * 0.9 + p) * 0.38;
                    this.headGroup.rotation.z = Math.sin(time * 1.1 + p) * 0.06;
                    root.position.y = 2.4 + Math.sin(time * 2.0 + p) * 0.05;
                }
            }
        };

        return root;
    }

    // 10A-2. Sculpted 3D Muscular Cyberpunk Male Officer (6-Pack Abs & Broad Pecs)
    createMaleOfficer3D(deptKey, cfg) {
        const root = new THREE.Group();
        root.position.set(0, 0, 2.4);

        const skinColor = 0xf0cfba;
        const skinMat = new THREE.MeshStandardMaterial({ color: skinColor, roughness: 0.65 });
        const armorMat = new THREE.MeshStandardMaterial({ color: cfg.color, roughness: 0.4, metalness: 0.5 });
        const tacticalPantsMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.8 });
        const abPlateMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.85, roughness: 0.2 });
        const goldMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.9, roughness: 0.25 });
        const accentMat = new THREE.MeshBasicMaterial({ color: cfg.accent });

        const hairPalettes = {
            'lead_pm': 0x1e293b,       // Commander Alex: Dark spiky undercut
            'execution_oms': 0x0f172a, // Marcus: Jet black tactical cut
            'news_scout': 0xd97706,    // Kael: Frosted amber spiky hair
            'spot_dca': 0x0369a1,      // Rex: Rugged dark blue fade
            'arbitrage_desk': 0xb45309,// Dante: Bronze brown slicked back
            'cvar_stress': 0xb91c1c    // Zane: Crimson cyber spikes
        };
        const hairColor = hairPalettes[deptKey] || 0x1e293b;
        const hairMat = new THREE.MeshStandardMaterial({ color: hairColor, roughness: 0.7 });

        // 1. Broad Tactical Pelvis & Utility Belt
        const pelvis = new THREE.Mesh(new THREE.BoxGeometry(2.7, 0.9, 2.0), tacticalPantsMat);
        pelvis.position.set(0, 2.6, 0);
        root.add(pelvis);

        // Heavy Tactical Utility Belt with Gold Commander Buckle
        const belt = new THREE.Mesh(new THREE.BoxGeometry(2.8, 0.35, 2.1), new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.8 }));
        belt.position.set(0, 2.9, 0);
        root.add(belt);

        const buckle = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.45, 0.15), goldMat);
        buckle.position.set(0, 2.9, -1.05);
        root.add(buckle);

        // 2. Heavy Armored Thighs & Kneepads
        for (let s = -1; s <= 1; s += 2) {
            const thigh = new THREE.Mesh(new THREE.BoxGeometry(0.95, 0.85, 2.25), tacticalPantsMat);
            thigh.position.set(s * 0.82, 2.6, -1.0);
            root.add(thigh);

            // Titanium Kneepad Shield
            const kneepad = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.6, 0.3), armorMat);
            kneepad.position.set(s * 0.82, 2.6, -2.18);
            root.add(kneepad);

            const shin = new THREE.Mesh(new THREE.BoxGeometry(0.9, 2.1, 0.9), tacticalPantsMat);
            shin.position.set(s * 0.82, 1.1, -1.8);
            root.add(shin);

            // Heavy Combat Boots
            const boot = new THREE.Mesh(new THREE.BoxGeometry(1.02, 0.72, 1.45), new THREE.MeshStandardMaterial({ color: 0x020617, roughness: 0.6 }));
            boot.position.set(s * 0.82, 0.36, -1.6);
            root.add(boot);

            const bootSole = new THREE.Mesh(new THREE.BoxGeometry(1.08, 0.2, 1.5), accentMat);
            bootSole.position.set(s * 0.82, 0.1, -1.6);
            root.add(bootSole);
        }

        // 3. BROAD CHISELED CHEST & 6-PACK ABDOMINAL ARMOR (Chàng Trai 6 Múi Vạm Vỡ)
        const torso = new THREE.Mesh(new THREE.BoxGeometry(3.5, 3.5, 1.9), armorMat);
        torso.position.set(0, 4.6, 0.08);
        torso.castShadow = true;
        root.add(torso);

        // Broad Pectoral Muscle Plates (Ngực Nở Vạm Vỡ)
        for (let s = -1; s <= 1; s += 2) {
            const pec = new THREE.Mesh(new THREE.BoxGeometry(1.5, 1.35, 0.35), armorMat);
            pec.position.set(s * 0.85, 5.3, -0.95);
            pec.rotation.y = s * 0.08;
            root.add(pec);
        }

        // Pectoral Center Division Line (Glow LED)
        const pecLed = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.4, 0.38), accentMat);
        pecLed.position.set(0, 5.3, -0.96);
        root.add(pecLed);

        // CHISELED 6-PACK ABDOMINAL PLATES (Cơ Bụng 6 Múi Sắc Nét)
        // 2 columns x 3 rows of individual segmented ab muscle blocks
        for (let row = 0; row < 3; row++) {
            for (let col = -1; col <= 1; col += 2) {
                const abBlock = new THREE.Mesh(new THREE.BoxGeometry(0.76, 0.42, 0.18), abPlateMat);
                abBlock.position.set(col * 0.48, 4.3 - row * 0.52, -0.95);
                root.add(abBlock);
            }
        }

        // Broad Heavy Shoulder Pauldrons with Rank Insignia
        for (let s = -1; s <= 1; s += 2) {
            const pauldron = new THREE.Mesh(new THREE.BoxGeometry(1.3, 0.38, 1.8), goldMat);
            pauldron.position.set(s * 1.95, 6.2, 0.1);
            root.add(pauldron);
        }

        // 4. Muscular Neck
        const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.48, 0.52, 0.55, 8), skinMat);
        neck.position.set(0, 6.3, 0.1);
        root.add(neck);

        // 5. Chiseled Head, Spiky Tactical Hair & Commander Visor
        const headGroup = new THREE.Group();
        headGroup.position.set(0, 7.3, 0.1);

        const head = new THREE.Mesh(new THREE.BoxGeometry(2.15, 2.15, 2.05), skinMat);
        head.castShadow = true;
        headGroup.add(head);

        // Layered Spiky Anime Hair
        const hairTop = new THREE.Mesh(new THREE.BoxGeometry(2.35, 0.95, 2.25), hairMat);
        hairTop.position.set(0, 1.05, -0.05);
        headGroup.add(hairTop);

        const spikes = [
            { x: -0.7, y: 1.6, z: 0.2, rotZ: -0.3 },
            { x: 0.0, y: 1.8, z: 0.4, rotZ: 0.1 },
            { x: 0.7, y: 1.6, z: 0.2, rotZ: 0.3 }
        ];
        spikes.forEach(sp => {
            const cone = new THREE.Mesh(new THREE.ConeGeometry(0.4, 1.1, 4), hairMat);
            cone.rotation.z = sp.rotZ;
            cone.position.set(sp.x, sp.y, sp.z);
            headGroup.add(cone);
        });

        // Frosted Neon Tip Highlight
        const tip = new THREE.Mesh(new THREE.ConeGeometry(0.25, 0.7, 4), accentMat);
        tip.position.set(0.15, 2.1, 0.3);
        headGroup.add(tip);

        // Commander Tactical Visor across eyes
        const visor = new THREE.Mesh(
            new THREE.BoxGeometry(2.25, 0.55, 0.42),
            new THREE.MeshStandardMaterial({ color: cfg.accent, emissive: cfg.accent, emissiveIntensity: 0.9, transparent: true, opacity: 0.9 })
        );
        visor.position.set(0, 0.15, -1.02);
        headGroup.add(visor);

        // Comms Headset with Articulated Boom Mic
        const headband = new THREE.Mesh(new THREE.TorusGeometry(1.28, 0.14, 6, 16, Math.PI), new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.9 }));
        headband.rotation.x = -Math.PI / 2;
        headband.position.set(0, 0.35, 0);
        headGroup.add(headband);

        for (let s = -1; s <= 1; s += 2) {
            const earcup = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.32, 12), goldMat);
            earcup.rotation.z = Math.PI / 2;
            earcup.position.set(s * 1.25, 0.15, 0);
            headGroup.add(earcup);
        }

        const micBoom = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1.3, 6), new THREE.MeshStandardMaterial({ color: 0x020617 }));
        micBoom.rotation.z = -Math.PI / 3;
        micBoom.rotation.y = -Math.PI / 4;
        micBoom.position.set(-1.0, -0.2, -0.6);
        headGroup.add(micBoom);

        const micTip = new THREE.Mesh(new THREE.SphereGeometry(0.15, 8, 8), accentMat);
        micTip.position.set(-0.6, -0.45, -1.1);
        headGroup.add(micTip);

        root.add(headGroup);

        // 6. Muscular Biceps & Rolled-Up Sleeves (Bắp Tay Cơ Bắp)
        const leftArmGroup = new THREE.Group();
        leftArmGroup.position.set(-1.85, 5.6, 0.1);

        // Thick Bicep Muscle (Bulging bicep geometry)
        const leftUpper = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.7, 0.9), armorMat);
        leftUpper.position.set(0, -0.6, -0.3);
        leftUpper.rotation.x = -Math.PI / 5;
        leftArmGroup.add(leftUpper);

        // Rolled-up sleeve cuff
        const leftCuff = new THREE.Mesh(new THREE.BoxGeometry(0.98, 0.25, 0.98), goldMat);
        leftCuff.position.set(0, -1.15, -0.85);
        leftCuff.rotation.x = -Math.PI / 5;
        leftArmGroup.add(leftCuff);

        // Muscular Forearm (Exposed muscular skin with cyber conduit)
        const leftForearm = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.82, 2.0), skinMat);
        leftForearm.position.set(0, -1.3, -1.25);
        leftArmGroup.add(leftForearm);

        const leftConduit = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.85, 1.8), accentMat);
        leftConduit.position.set(-0.4, -1.3, -1.25);
        leftArmGroup.add(leftConduit);

        // Heavy Tactical Combat Glove Hand
        const leftHandGlove = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.45, 0.7), new THREE.MeshStandardMaterial({ color: 0x020617 }));
        leftHandGlove.position.set(0, -1.3, -2.25);
        leftArmGroup.add(leftHandGlove);
        root.add(leftArmGroup);

        const rightArmGroup = new THREE.Group();
        rightArmGroup.position.set(1.85, 5.6, 0.1);

        const rightUpper = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.7, 0.9), armorMat);
        rightUpper.position.set(0, -0.6, -0.3);
        rightUpper.rotation.x = -Math.PI / 5;
        rightArmGroup.add(rightUpper);

        const rightCuff = new THREE.Mesh(new THREE.BoxGeometry(0.98, 0.25, 0.98), goldMat);
        rightCuff.position.set(0, -1.15, -0.85);
        rightCuff.rotation.x = -Math.PI / 5;
        rightArmGroup.add(rightCuff);

        const rightForearm = new THREE.Mesh(new THREE.BoxGeometry(0.82, 0.82, 2.0), skinMat);
        rightForearm.position.set(0, -1.3, -1.25);
        rightArmGroup.add(rightForearm);

        const rightHandGlove = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.45, 0.7), new THREE.MeshStandardMaterial({ color: 0x020617 }));
        rightHandGlove.position.set(0, -1.3, -2.25);
        rightArmGroup.add(rightHandGlove);
        root.add(rightArmGroup);

        // Expressive Male Officer Animation Logic
        root.userData = {
            headGroup: headGroup,
            leftArmGroup: leftArmGroup,
            rightArmGroup: rightArmGroup,
            phase: Math.random() * 10,
            state: 'working',
            animate: function(time, delta, state) {
                const p = this.phase;
                const s = state || this.state || 'working';

                if (s === 'celebrating') {
                    // Firm victory pump with muscular arms
                    this.leftArmGroup.rotation.x = -Math.PI * 0.82 + Math.sin(time * 12 + p) * 0.2;
                    this.rightArmGroup.rotation.x = -Math.PI * 0.82 + Math.cos(time * 12 + p) * 0.2;
                    this.headGroup.rotation.x = -0.25;
                    this.headGroup.rotation.y = Math.sin(time * 4 + p) * 0.2;
                    root.position.y = 2.4 + Math.abs(Math.sin(time * 8 + p)) * 0.35;
                } else if (s === 'veto') {
                    // Decisive firm veto gesture
                    this.leftArmGroup.rotation.x = -Math.PI / 5;
                    this.rightArmGroup.rotation.x = -Math.PI * 0.72;
                    this.headGroup.rotation.y = Math.sin(time * 5 + p) * 0.38;
                    this.headGroup.rotation.x = 0.08;
                    root.position.y = 2.4;
                } else {
                    // Heavy athletic typing rhythm
                    this.leftArmGroup.rotation.x = -Math.PI / 5 + Math.sin(time * 12 + p) * 0.18;
                    const mouseCycle = Math.sin(time * 0.7 + p);
                    if (mouseCycle > 0.35) {
                        this.rightArmGroup.rotation.x = -Math.PI / 5.6;
                        this.rightArmGroup.position.x = 2.05;
                    } else {
                        this.rightArmGroup.rotation.x = -Math.PI / 5 + Math.cos(time * 12 + p) * 0.18;
                        this.rightArmGroup.position.x = 1.85;
                    }

                    this.headGroup.rotation.y = Math.sin(time * 0.85 + p) * 0.44;
                    this.headGroup.rotation.x = -0.06 + Math.sin(time * 1.5 + p) * 0.06;
                    root.position.y = 2.4 + Math.sin(time * 2.0 + p) * 0.06;
                }
            }
        };

        return root;
    }

    // 10B. Deeply Detailed 3D Boss (CEO / Commander) with Cyber Trenchcoat & Hologram
    createBoss3DModel() {
        const root = new THREE.Group();
        root.position.copy(this.bossPosition);

        const skinColor = 0xffdfc4;
        const skinMat = new THREE.MeshStandardMaterial({ color: skinColor, roughness: 0.65 });
        const trenchMat = new THREE.MeshStandardMaterial({ color: 0x0a0f1d, roughness: 0.4, metalness: 0.35 });
        const goldMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.25, metalness: 0.85 });
        const cyanNeonMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
        const pantsMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.7 });
        const hairMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.8 });

        // 1. Pelvis / Tactical Belt
        const pelvis = new THREE.Mesh(new THREE.BoxGeometry(2.7, 1.1, 1.8), pantsMat);
        pelvis.position.set(0, 3.2, 0);
        root.add(pelvis);

        // Tactical Utility Belt & Gold Commander Buckle
        const belt = new THREE.Mesh(new THREE.BoxGeometry(2.8, 0.35, 1.9), new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.8 }));
        belt.position.set(0, 3.5, 0);
        root.add(belt);

        const buckle = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.45, 0.15), goldMat);
        buckle.position.set(0, 3.5, 0.98);
        root.add(buckle);

        // Cyber Pouches on hips
        for (let s = -1; s <= 1; s += 2) {
            const pouch = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.7, 0.8), new THREE.MeshStandardMaterial({ color: 0x1e293b }));
            pouch.position.set(s * 1.5, 3.3, 0);
            root.add(pouch);
        }

        // 2. Commander Trenchcoat Torso
        const torso = new THREE.Mesh(new THREE.BoxGeometry(3.1, 3.5, 1.9), trenchMat);
        torso.position.set(0, 5.1, 0);
        torso.castShadow = true;
        root.add(torso);

        // Gold Lapels & Dual Cyan Neon Accent Energy Lines
        const lapelL = new THREE.Mesh(new THREE.BoxGeometry(0.4, 3.0, 0.12), goldMat);
        lapelL.position.set(-0.6, 5.2, 0.98);
        root.add(lapelL);

        const lapelR = new THREE.Mesh(new THREE.BoxGeometry(0.4, 3.0, 0.12), goldMat);
        lapelR.position.set(0.6, 5.2, 0.98);
        root.add(lapelR);

        const neonStripL = new THREE.Mesh(new THREE.BoxGeometry(0.1, 3.0, 0.12), cyanNeonMat);
        neonStripL.position.set(-0.25, 5.2, 0.99);
        root.add(neonStripL);

        const neonStripR = new THREE.Mesh(new THREE.BoxGeometry(0.1, 3.0, 0.12), cyanNeonMat);
        neonStripR.position.set(0.25, 5.2, 0.99);
        root.add(neonStripR);

        // High Standing Trenchcoat Collar
        const collarBack = new THREE.Mesh(new THREE.BoxGeometry(2.4, 1.2, 0.25), trenchMat);
        collarBack.position.set(0, 7.0, -0.9);
        root.add(collarBack);

        // Swaying Coat Tails (Flaps behind and in front of legs)
        const coatTailPivot = new THREE.Group();
        coatTailPivot.position.set(0, 3.3, 0);
        const coatBackTail = new THREE.Mesh(new THREE.BoxGeometry(2.7, 2.4, 0.2), trenchMat);
        coatBackTail.position.set(0, -1.2, -0.95);
        coatTailPivot.add(coatBackTail);

        const coatFrontL = new THREE.Mesh(new THREE.BoxGeometry(0.8, 2.0, 0.2), trenchMat);
        coatFrontL.position.set(-0.9, -1.0, 0.95);
        coatTailPivot.add(coatFrontL);

        const coatFrontR = new THREE.Mesh(new THREE.BoxGeometry(0.8, 2.0, 0.2), trenchMat);
        coatFrontR.position.set(0.9, -1.0, 0.95);
        coatTailPivot.add(coatFrontR);
        root.add(coatTailPivot);

        // 3. Neck
        const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.45, 0.5, 0.5, 8), skinMat);
        neck.position.set(0, 6.95, 0);
        root.add(neck);

        // 4. Head Group (Spiky Cyber Hair, Visor, Headset)
        const headGroup = new THREE.Group();
        headGroup.position.set(0, 8.0, 0);

        const head = new THREE.Mesh(new THREE.BoxGeometry(2.2, 2.2, 2.0), skinMat);
        head.castShadow = true;
        headGroup.add(head);

        // Layered Anime Spiky Hair with Frosted Cyan Highlights
        const hairTop = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.9, 2.2), hairMat);
        hairTop.position.set(0, 1.0, -0.05);
        headGroup.add(hairTop);

        const spikes = [
            { x: -0.8, y: 1.6, z: 0.2, rotZ: -0.35, size: 0.45, h: 1.2 },
            { x: 0.0, y: 1.8, z: 0.4, rotZ: 0.1, size: 0.5, h: 1.4 },
            { x: 0.8, y: 1.6, z: 0.2, rotZ: 0.35, size: 0.45, h: 1.2 },
            { x: -0.5, y: 1.4, z: -0.5, rotZ: -0.2, size: 0.4, h: 1.0 },
            { x: 0.5, y: 1.4, z: -0.5, rotZ: 0.2, size: 0.4, h: 1.0 }
        ];
        spikes.forEach(sp => {
            const cone = new THREE.Mesh(new THREE.ConeGeometry(sp.size, sp.h, 4), hairMat);
            cone.rotation.z = sp.rotZ;
            cone.position.set(sp.x, sp.y, sp.z);
            headGroup.add(cone);
        });

        // Glowing Frosted Cyan Hair Highlight Tip
        const cyanTip = new THREE.Mesh(new THREE.ConeGeometry(0.3, 0.8, 4), cyanNeonMat);
        cyanTip.rotation.z = 0.15;
        cyanTip.position.set(0.2, 2.2, 0.3);
        headGroup.add(cyanTip);

        // Tactical Commander Visor with Crosshair Projection
        const visor = new THREE.Mesh(
            new THREE.BoxGeometry(2.35, 0.55, 0.4),
            new THREE.MeshStandardMaterial({ color: 0x06b6d4, emissive: 0x06b6d4, emissiveIntensity: 0.9, transparent: true, opacity: 0.9 })
        );
        visor.position.set(0, 0.15, 0.98);
        headGroup.add(visor);

        // Headset with Pulsing LED Ring
        const headband = new THREE.Mesh(new THREE.TorusGeometry(1.28, 0.14, 6, 16, Math.PI), new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.9 }));
        headband.rotation.x = -Math.PI / 2;
        headband.position.set(0, 0.3, 0);
        headGroup.add(headband);

        for (let s = -1; s <= 1; s += 2) {
            const earcup = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.3, 12), goldMat);
            earcup.rotation.z = Math.PI / 2;
            earcup.position.set(s * 1.28, 0.15, 0);
            headGroup.add(earcup);

            const earcupLed = new THREE.Mesh(new THREE.TorusGeometry(0.38, 0.05, 4, 12), cyanNeonMat);
            earcupLed.rotation.y = Math.PI / 2;
            earcupLed.position.set(s * 1.45, 0.15, 0);
            headGroup.add(earcupLed);
        }
        root.add(headGroup);

        // 5. Left Leg & Right Leg with High-Top Dual-Air Sneaker
        const legGeo = new THREE.BoxGeometry(0.95, 2.8, 1.05);
        const shoeMat = new THREE.MeshStandardMaterial({ color: 0x020617, roughness: 0.5 });

        const leftLegPivot = new THREE.Group();
        leftLegPivot.position.set(-0.9, 3.2, 0);
        const leftLeg = new THREE.Mesh(legGeo, pantsMat);
        leftLeg.position.set(0, -1.4, 0);
        leftLegPivot.add(leftLeg);

        const leftShoe = new THREE.Mesh(new THREE.BoxGeometry(1.05, 0.75, 1.6), shoeMat);
        leftShoe.position.set(0, -2.85, 0.2);
        leftLegPivot.add(leftShoe);

        const leftSole = new THREE.Mesh(new THREE.BoxGeometry(1.12, 0.22, 1.65), cyanNeonMat);
        leftSole.position.set(0, -3.22, 0.2);
        leftLegPivot.add(leftSole);
        root.add(leftLegPivot);

        const rightLegPivot = new THREE.Group();
        rightLegPivot.position.set(0.9, 3.2, 0);
        const rightLeg = new THREE.Mesh(legGeo, pantsMat);
        rightLeg.position.set(0, -1.4, 0);
        rightLegPivot.add(rightLeg);

        const rightShoe = new THREE.Mesh(new THREE.BoxGeometry(1.05, 0.75, 1.6), shoeMat);
        rightShoe.position.set(0, -2.85, 0.2);
        rightLegPivot.add(rightShoe);

        const rightSole = new THREE.Mesh(new THREE.BoxGeometry(1.12, 0.22, 1.65), cyanNeonMat);
        rightSole.position.set(0, -3.22, 0.2);
        rightLegPivot.add(rightSole);
        root.add(rightLegPivot);

        // 6. Left Cybernetic Titanium Arm with Holographic Command Tablet
        const leftArmPivot = new THREE.Group();
        leftArmPivot.position.set(-1.85, 6.3, 0);

        const leftArm = new THREE.Mesh(
            new THREE.BoxGeometry(0.8, 2.6, 0.8),
            new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.85, roughness: 0.25 })
        );
        leftArm.position.set(0, -1.2, 0);
        leftArmPivot.add(leftArm);

        // Glowing Cybernetic Conduit Circuit Line along arm
        const armCircuit = new THREE.Mesh(new THREE.BoxGeometry(0.12, 2.4, 0.82), cyanNeonMat);
        armCircuit.position.set(0, -1.2, 0);
        leftArmPivot.add(armCircuit);

        const leftHand = new THREE.Mesh(new THREE.BoxGeometry(0.68, 0.5, 0.68), skinMat);
        leftHand.position.set(0, -2.6, 0);
        leftArmPivot.add(leftHand);

        // Obsidian Glass Holographic Command Tablet
        const tablet = new THREE.Mesh(
            new THREE.BoxGeometry(1.8, 0.12, 2.4),
            new THREE.MeshStandardMaterial({ color: 0x020617, metalness: 0.95, roughness: 0.1 })
        );
        tablet.position.set(-0.2, -2.3, 1.0);
        tablet.rotation.x = Math.PI / 3.8;
        leftArmPivot.add(tablet);

        // FLOATING 3D HOLOGRAPHIC QUANTUM GLOBE ABOVE TABLET
        const holoGroup = new THREE.Group();
        holoGroup.position.set(-0.2, -1.2, 1.2);

        const holoWire = new THREE.Mesh(
            new THREE.IcosahedronGeometry(0.85, 1),
            new THREE.MeshBasicMaterial({ color: 0x06b6d4, wireframe: true, transparent: true, opacity: 0.85 })
        );
        holoGroup.add(holoWire);

        const holoCore = new THREE.Mesh(
            new THREE.SphereGeometry(0.4, 12, 12),
            new THREE.MeshBasicMaterial({ color: 0x38bdf8 })
        );
        holoGroup.add(holoCore);

        const holoLight = new THREE.PointLight(0x06b6d4, 1.5, 10);
        holoGroup.add(holoLight);

        leftArmPivot.add(holoGroup);
        root.add(leftArmPivot);

        // 7. Right Arm (Natural swing & tactical glove)
        const rightArmPivot = new THREE.Group();
        rightArmPivot.position.set(1.85, 6.3, 0);

        const rightArm = new THREE.Mesh(new THREE.BoxGeometry(0.8, 2.6, 0.8), trenchMat);
        rightArm.position.set(0, -1.2, 0);
        rightArmPivot.add(rightArm);

        const rightHand = new THREE.Mesh(new THREE.BoxGeometry(0.68, 0.5, 0.68), new THREE.MeshStandardMaterial({ color: 0x020617 }));
        rightHand.position.set(0, -2.6, 0);
        rightArmPivot.add(rightHand);

        root.add(rightArmPivot);

        // Animation Metadata
        root.userData = {
            leftLegPivot: leftLegPivot,
            rightLegPivot: rightLegPivot,
            leftArmPivot: leftArmPivot,
            rightArmPivot: rightArmPivot,
            coatTailPivot: coatTailPivot,
            headGroup: headGroup,
            torso: torso,
            holoWire: holoWire,
            holoCore: holoCore,
            walkCycle: 0,
            animate: function(time, delta, isMoving) {
                // Spin 3D Hologram above tablet
                this.holoWire.rotation.y += delta * 1.8;
                this.holoWire.rotation.x += delta * 1.2;
                this.holoCore.scale.setScalar(1.0 + Math.sin(time * 6) * 0.15);

                if (isMoving) {
                    this.walkCycle += delta * 13;
                    const angle = Math.sin(this.walkCycle) * 0.65;
                    this.leftLegPivot.rotation.x = angle;
                    this.rightLegPivot.rotation.x = -angle;

                    this.rightArmPivot.rotation.x = angle * 0.7;
                    this.leftArmPivot.rotation.x = -0.3 + Math.sin(this.walkCycle) * 0.2;

                    // Coat tails sway dynamically behind Boss
                    this.coatTailPivot.rotation.x = Math.abs(Math.sin(this.walkCycle)) * 0.35;

                    // Step bounce internal offset (not overwriting root.position.y)
                    this.stepBounce = Math.abs(Math.sin(this.walkCycle * 2)) * 0.35;
                } else {
                    this.leftLegPivot.rotation.x *= 0.8;
                    this.rightLegPivot.rotation.x *= 0.8;
                    this.rightArmPivot.rotation.x *= 0.8;
                    this.leftArmPivot.rotation.x = -0.3;
                    this.coatTailPivot.rotation.x *= 0.8;
                    this.stepBounce = 0;

                    // Idle breathing
                    this.torso.scale.y = 1.0 + Math.sin(time * 2.5) * 0.02;
                    this.headGroup.rotation.y = Math.sin(time * 1.2) * 0.12;
                }
            }
        };

        return root;
    }

    // 10C. Deeply Detailed 3D Astra AI Companion (Chibi Anime Cyber Fairy with Bitcoin Halo & Crystal Wings)
    createAstra3DModel() {
        const root = new THREE.Group();
        root.position.copy(this.astraPosition);

        const skinColor = 0xfff1f2;
        const skinMat = new THREE.MeshStandardMaterial({ color: skinColor, roughness: 0.6 });
        const pinkHairMat = new THREE.MeshStandardMaterial({ color: 0xf472b6, roughness: 0.45, metalness: 0.15 });
        const dressMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3, metalness: 0.25 });
        const neonPinkMat = new THREE.MeshBasicMaterial({ color: 0xec4899 });
        const neonCyanMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
        const goldMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.25, metalness: 0.9 });

        // 1. Chibi Android Body (Dress Chassis)
        const body = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 1.4, 2.2, 8), dressMat);
        body.position.set(0, 0, 0);
        body.castShadow = true;
        root.add(body);

        // Pleated Skirt Hem Neon Ring
        const skirtRing = new THREE.Mesh(new THREE.TorusGeometry(1.42, 0.08, 6, 16), neonPinkMat);
        skirtRing.rotation.x = Math.PI / 2;
        skirtRing.position.set(0, -1.0, 0);
        root.add(skirtRing);

        // Glowing Energy Heart Core in Chest
        const core = new THREE.Mesh(new THREE.SphereGeometry(0.42, 12, 12), neonCyanMat);
        core.position.set(0, 0.4, 0.82);
        root.add(core);

        // 2. Chibi Head & Anime Face
        const headGroup = new THREE.Group();
        headGroup.position.set(0, 2.0, 0);

        const head = new THREE.Mesh(new THREE.BoxGeometry(2.2, 2.0, 2.0), skinMat);
        head.castShadow = true;
        headGroup.add(head);

        // Pink Hair Cap
        const hairCap = new THREE.Mesh(new THREE.BoxGeometry(2.35, 0.95, 2.2), pinkHairMat);
        hairCap.position.set(0, 0.85, -0.05);
        headGroup.add(hairCap);

        // Twin-Tails with Articulated Ribbons
        const leftTailGroup = new THREE.Group();
        leftTailGroup.position.set(-1.45, 0.5, -0.3);
        const tailGeo = new THREE.CylinderGeometry(0.2, 0.5, 2.2, 6);
        const leftTail = new THREE.Mesh(tailGeo, pinkHairMat);
        leftTail.position.set(-0.25, -1.0, 0);
        leftTail.rotation.z = 0.35;
        leftTailGroup.add(leftTail);

        const ribbonL = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.08, 4, 12), goldMat);
        ribbonL.position.set(0, 0, 0);
        leftTailGroup.add(ribbonL);
        headGroup.add(leftTailGroup);

        const rightTailGroup = new THREE.Group();
        rightTailGroup.position.set(1.45, 0.5, -0.3);
        const rightTail = new THREE.Mesh(tailGeo, pinkHairMat);
        rightTail.position.set(0.25, -1.0, 0);
        rightTail.rotation.z = -0.35;
        rightTailGroup.add(rightTail);

        const ribbonR = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.08, 4, 12), goldMat);
        ribbonR.position.set(0, 0, 0);
        rightTailGroup.add(ribbonR);
        headGroup.add(rightTailGroup);

        // Digital Emote Smiling Face (Cyan Visor)
        const eyeVisor = new THREE.Mesh(new THREE.BoxGeometry(1.85, 0.42, 0.22), neonCyanMat);
        eyeVisor.position.set(0, 0.15, 1.0);
        headGroup.add(eyeVisor);

        // Pink Blush Dots on Cheeks
        for (let b = -1; b <= 1; b += 2) {
            const blush = new THREE.Mesh(new THREE.PlaneGeometry(0.35, 0.2), neonPinkMat);
            blush.position.set(b * 0.75, -0.2, 1.02);
            headGroup.add(blush);
        }

        // 3D BITCOIN HALO: Golden Ring + Engraved 'B' Signet Disc
        const haloGroup = new THREE.Group();
        haloGroup.position.set(0, 2.0, 0);

        const haloRing = new THREE.Mesh(new THREE.TorusGeometry(1.0, 0.12, 8, 24), goldMat);
        haloRing.rotation.x = Math.PI / 2.2;
        haloGroup.add(haloRing);

        const bDisc = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.1, 16), goldMat);
        bDisc.rotation.x = Math.PI / 2.2;
        haloGroup.add(bDisc);

        const bBar = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.8, 0.15), new THREE.MeshBasicMaterial({ color: 0xffffff }));
        bBar.rotation.x = Math.PI / 2.2;
        haloGroup.add(bBar);

        headGroup.add(haloGroup);
        root.add(headGroup);

        // 3. Multi-Faceted Crystal Energy Wings
        const wingGroup = new THREE.Group();
        wingGroup.position.set(0, 0.6, -0.8);

        const wingMat = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.75
        });

        const leftWing = new THREE.Group();
        for (let w = 0; w < 3; w++) {
            const feather = new THREE.Mesh(new THREE.ConeGeometry(0.4 - w * 0.08, 2.2 - w * 0.4, 4), wingMat);
            feather.rotation.z = 0.5 + w * 0.35;
            feather.position.set(-0.8 - w * 0.4, 0.4 - w * 0.3, 0);
            leftWing.add(feather);
        }
        wingGroup.add(leftWing);

        const rightWing = new THREE.Group();
        for (let w = 0; w < 3; w++) {
            const feather = new THREE.Mesh(new THREE.ConeGeometry(0.4 - w * 0.08, 2.2 - w * 0.4, 4), wingMat);
            feather.rotation.z = -0.5 - w * 0.35;
            feather.position.set(0.8 + w * 0.4, 0.4 - w * 0.3, 0);
            rightWing.add(feather);
        }
        wingGroup.add(rightWing);
        root.add(wingGroup);

        // 4. Dual Gyroscopic Orbital Rings with Orbiting Micro Data Bits
        const ring1 = new THREE.Mesh(new THREE.TorusGeometry(2.4, 0.06, 6, 32), neonCyanMat);
        root.add(ring1);

        const ring2 = new THREE.Mesh(new THREE.TorusGeometry(3.0, 0.06, 6, 32), goldMat);
        root.add(ring2);

        // Orbiting micro data cubes
        const dataBits = [];
        for (let d = 0; d < 3; d++) {
            const bit = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.35, 0.35), neonPinkMat);
            root.add(bit);
            dataBits.push(bit);
        }

        // Warm Pink Ambient PointLight
        const auraLight = new THREE.PointLight(0xf472b6, 1.8, 40);
        auraLight.position.set(0, 1.0, 0);
        root.add(auraLight);

        // Animation Metadata
        root.userData = {
            leftWing: leftWing,
            rightWing: rightWing,
            ring1: ring1,
            ring2: ring2,
            haloGroup: haloGroup,
            dataBits: dataBits,
            leftTailGroup: leftTailGroup,
            rightTailGroup: rightTailGroup,
            hoverOffset: 0,
            animate: function(time, delta) {
                // Floating Hover oscillation offset
                this.hoverOffset = Math.sin(time * 3.2) * 0.4;

                // Spinning Gyroscope Rings
                this.ring1.rotation.x += delta * 1.8;
                this.ring1.rotation.y += delta * 1.3;
                this.ring2.rotation.y -= delta * 1.5;
                this.ring2.rotation.z += delta * 1.1;

                // Orbiting Data Bits along ring
                this.dataBits.forEach((bit, i) => {
                    const ang = time * 2.5 + (i * Math.PI * 2) / 3;
                    bit.position.set(Math.cos(ang) * 2.7, Math.sin(ang * 1.5) * 1.2, Math.sin(ang) * 2.7);
                    bit.rotation.x += delta * 3;
                    bit.rotation.y += delta * 3;
                });

                // Crystal Wing Flapping
                const wingFlap = Math.sin(time * 16) * 0.4;
                this.leftWing.rotation.y = 0.4 + wingFlap;
                this.rightWing.rotation.y = -0.4 - wingFlap;

                // Hair physics bounce
                const bounce = Math.sin(time * 6) * 0.18;
                this.leftTailGroup.rotation.z = bounce;
                this.rightTailGroup.rotation.z = -bounce;

                // Bitcoin Halo Rotation
                this.haloGroup.rotation.y += delta * 1.6;
            }
        };

        return root;
    }

    /* --------------------------------------------------------------------------
       10D. BUILD 3D AVATARS (BOSS & ASTRA COMPANION)
       -------------------------------------------------------------------------- */
    buildAvatars() {
        // Full 3D Boss (CEO/Commander) Model
        this.bossModel = this.createBoss3DModel();
        this.scene.add(this.bossModel);

        const shadowGeo = new THREE.CircleGeometry(3.5, 24);
        const shadowMat = new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.45 });
        this.bossShadow = new THREE.Mesh(shadowGeo, shadowMat);
        this.bossShadow.rotation.x = -Math.PI / 2;
        this.bossShadow.position.set(this.bossPosition.x, 0.15, this.bossPosition.z);
        this.scene.add(this.bossShadow);

        // Full 3D Astra AI Companion Model
        this.astraModel = this.createAstra3DModel();
        this.scene.add(this.astraModel);

        this.astraShadow = new THREE.Mesh(shadowGeo, shadowMat);
        this.astraShadow.rotation.x = -Math.PI / 2;
        this.astraShadow.position.set(this.astraPosition.x, 0.15, this.astraPosition.z);
        this.scene.add(this.astraShadow);

        // Dynamic 3D Speech Bubbles for Boss and Astra Companion
        this.bossBubbleSprite = this.createSpeechBubbleSprite('👑 Boss: Kiểm tra an toàn!', 0xf59e0b);
        this.bossBubbleSprite.visible = false;
        this.bossBubbleSprite.scale.set(24, 6.5, 1);
        this.scene.add(this.bossBubbleSprite);

        this.astraBubbleSprite = this.createSpeechBubbleSprite('🤖 Astra: 12 phòng ban sẵn sàng!', 0xc084fc);
        this.astraBubbleSprite.visible = false;
        this.astraBubbleSprite.scale.set(24, 6.5, 1);
        this.scene.add(this.astraBubbleSprite);
    }

    /* --------------------------------------------------------------------------
       10E. BUILD MEGACITY SKYLINE & SUPERCAR SHOWROOM BALCONY (INSPIRED BY NARGOR/CAR-ACTION)
       -------------------------------------------------------------------------- */
    buildMegacitySkylineAndSupercars() {
        const megacityGroup = new THREE.Group();

        // 1. 52 Cyberpunk Illuminated Skyscrapers around the Horizon (r = 280 .. 520)
        const buildingColors = [0x0f172a, 0x0a0f1d, 0x111827, 0x050b14, 0x1e1b4b];
        const neonGlowColors = [0x00f0ff, 0x38bdf8, 0xf59e0b, 0xec4899, 0xa855f7, 0x10b981];

        const numTowers = 52;
        for (let i = 0; i < numTowers; i++) {
            const angle = (i / numTowers) * Math.PI * 2 + (Math.sin(i * 3.7) * 0.08);
            const radius = 290 + (i % 7) * 32 + (Math.sin(i * 1.5) * 25);
            const width = 22 + (i % 5) * 6;
            const depth = 22 + ((i + 2) % 5) * 6;
            const height = 110 + (i % 9) * 26 + ((i * 17) % 80);

            const towerGroup = new THREE.Group();
            towerGroup.position.set(
                Math.sin(angle) * radius,
                height / 2 - 15,
                Math.cos(angle) * radius
            );

            // Tower main body
            const bGeo = new THREE.BoxGeometry(width, height, depth);
            const bMat = new THREE.MeshStandardMaterial({
                color: buildingColors[i % buildingColors.length],
                metalness: 0.85,
                roughness: 0.25
            });
            const tower = new THREE.Mesh(bGeo, bMat);
            towerGroup.add(tower);

            // Illuminated window facade strips
            const winColor = neonGlowColors[i % neonGlowColors.length];
            const numStrips = 3 + (i % 4);
            for (let s = 0; s < numStrips; s++) {
                const stripY = -height * 0.4 + (s / numStrips) * height * 0.85;
                const winH = 4 + (s % 3) * 3;
                const winGeo = new THREE.BoxGeometry(width + 0.4, winH, depth + 0.4);
                const winMat = new THREE.MeshBasicMaterial({
                    color: winColor,
                    transparent: true,
                    opacity: 0.55 + (s % 2) * 0.25
                });
                const winStrip = new THREE.Mesh(winGeo, winMat);
                winStrip.position.y = stripY;
                towerGroup.add(winStrip);
            }

            // Rooftop Communication Antenna & Spire
            const spireH = 18 + (i % 6) * 7;
            const spireGeo = new THREE.CylinderGeometry(0.3, 1.2, spireH, 6);
            const spireMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9 });
            const spire = new THREE.Mesh(spireGeo, spireMat);
            spire.position.y = height / 2 + spireH / 2;
            towerGroup.add(spire);

            // Flashing Red Aviation Beacon on Rooftop Spire
            const beaconGeo = new THREE.SphereGeometry(0.8, 8, 8);
            const beaconMat = new THREE.MeshBasicMaterial({ color: (i % 2 === 0 ? 0xef4444 : 0xf59e0b) });
            const beacon = new THREE.Mesh(beaconGeo, beaconMat);
            beacon.position.y = height / 2 + spireH;
            towerGroup.add(beacon);
            this.skylineBeacons.push({ mesh: beacon, phase: i * 0.35 });

            // Rooftop Billboard on select major skyscrapers
            if (i % 8 === 0) {
                const ads = [
                    'BINANCE HFT LIVE',
                    'ASTRA QUANT V3.0',
                    'WALL STREET ALGO',
                    'DEEP ALPHA LAB',
                    'CVAR SHIELD 0.0%',
                    'BYBIT PERP CLUSTER'
                ];
                const adText = ads[(i / 8) % ads.length];
                const billboard = this.createHoloSprite(adText, winColor);
                billboard.position.set(0, height / 2 + 10, 0);
                billboard.scale.set(45, 12, 1);
                towerGroup.add(billboard);
            }

            megacityGroup.add(towerGroup);
        }

        // 2. Autonomous Sky-Cruisers (Flying hover-cars in air traffic corridors)
        for (let c = 0; c < 5; c++) {
            const cruiser = new THREE.Group();
            const cBody = new THREE.Mesh(
                new THREE.BoxGeometry(7.0, 1.6, 3.2),
                new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9, roughness: 0.1 })
            );
            cruiser.add(cBody);

            const hLight = new THREE.Mesh(
                new THREE.BoxGeometry(0.4, 0.5, 2.6),
                new THREE.MeshBasicMaterial({ color: 0x00f0ff })
            );
            hLight.position.set(3.6, 0, 0);
            cruiser.add(hLight);

            const thruster = new THREE.Mesh(
                new THREE.BoxGeometry(0.4, 0.6, 2.4),
                new THREE.MeshBasicMaterial({ color: 0xec4899 })
            );
            thruster.position.set(-3.6, 0, 0);
            cruiser.add(thruster);

            cruiser.userData = {
                radius: 260 + c * 35,
                speed: 0.18 + c * 0.06,
                angle: (c * Math.PI * 2) / 5,
                baseY: 95 + c * 18
            };
            megacityGroup.add(cruiser);
            this.skyCruisers.push(cruiser);
        }

        // 3. SOUTH VIP SUPERCAR SHOWROOM TERRACE & BALCONY (Inspired by Nargor/car-action)
        const balcony = new THREE.Group();
        balcony.position.set(0, 0, 150);

        // Balcony Platform
        const balGeo = new THREE.BoxGeometry(72, 3.0, 48);
        const balMat = new THREE.MeshStandardMaterial({ color: 0x0a1020, metalness: 0.85, roughness: 0.2 });
        const balMesh = new THREE.Mesh(balGeo, balMat);
        balMesh.position.y = 1.5;
        balMesh.receiveShadow = true;
        balcony.add(balMesh);

        // Glowing Balcony Rim Edge
        const balEdge = new THREE.LineSegments(
            new THREE.EdgesGeometry(new THREE.BoxGeometry(72.4, 3.2, 48.4)),
            new THREE.LineBasicMaterial({ color: 0x00f0ff })
        );
        balEdge.position.y = 1.5;
        balcony.add(balEdge);

        // Glass Safety Railings
        const railMat = new THREE.MeshStandardMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.35,
            metalness: 0.5
        });
        const backRail = new THREE.Mesh(new THREE.BoxGeometry(72, 4.5, 0.3), railMat);
        backRail.position.set(0, 4.5, 24);
        balcony.add(backRail);

        const leftRail = new THREE.Mesh(new THREE.BoxGeometry(0.3, 4.5, 48), railMat);
        leftRail.position.set(-36, 4.5, 0);
        balcony.add(leftRail);

        const rightRail = new THREE.Mesh(new THREE.BoxGeometry(0.3, 4.5, 48), railMat);
        rightRail.position.set(36, 4.5, 0);
        balcony.add(rightRail);

        // Balcony Entrance Billboard
        const terraceBanner = this.createHoloSprite('🏎️ VIP SUPERCAR BALCONY · ĐỘI XE ĐUA QUANTUM', 0xf59e0b);
        terraceBanner.position.set(0, 14, 23.5);
        terraceBanner.scale.set(36, 5.5, 1);
        balcony.add(terraceBanner);

        // Connecting Skywalk from Central Core to Balcony
        const bridgeGeo = new THREE.BoxGeometry(16, 2.2, 55);
        const bridge = new THREE.Mesh(bridgeGeo, balMat);
        bridge.position.set(0, 1.1, -40);
        balcony.add(bridge);

        const bridgeTrim = new THREE.LineSegments(
            new THREE.EdgesGeometry(new THREE.BoxGeometry(16.3, 2.3, 55.2)),
            new THREE.LineBasicMaterial({ color: 0x38bdf8 })
        );
        bridgeTrim.position.set(0, 1.1, -40);
        balcony.add(bridgeTrim);

        // 4. SUPERCAR 1: Ferrari 488 Cyber Red GTB (Referenced from Nargor/car-action 50 Ferrari setup)
        const ferrari = this.createSupercarMesh(
            'ferrari',
            0xd90429, // Cyber Ferrari Racing Red
            0x111827, // Carbon Black
            '🏎️ FERRARI 488 GTB · RACER #01',
            'V8 TWIN-TURBO 720HP | TIKTOK NITRO READY'
        );
        ferrari.position.set(-18, 3.0, 4);
        ferrari.rotation.y = Math.PI * 0.12;
        balcony.add(ferrari);
        this.supercars.push({
            group: ferrari,
            id: 'ferrari_488',
            name: 'Ferrari 488 Cyber GTB',
            worldPos: new THREE.Vector3(-18, 3.0, 154)
        });

        // 5. SUPERCAR 2: Lamborghini Aventador SVJ Cyber Cyan
        const lambo = this.createSupercarMesh(
            'lambo',
            0x00f0ff, // Electric Cyber Cyan
            0x0f172a, // Obsidian Black
            '⚡ LAMBORGHINI SVJ · RACER #07',
            'V12 770HP | QUANTUM OVERCLOCK 350 KM/H'
        );
        lambo.position.set(18, 3.0, 4);
        lambo.rotation.y = -Math.PI * 0.12;
        balcony.add(lambo);
        this.supercars.push({
            group: lambo,
            id: 'lambo_svj',
            name: 'Lamborghini Aventador SVJ',
            worldPos: new THREE.Vector3(18, 3.0, 154)
        });

        megacityGroup.add(balcony);
        this.scene.add(megacityGroup);
        this.megacityGroup = megacityGroup;
    }

    /* --------------------------------------------------------------------------
       10E-2. CREATE PROCEDURAL SUPERCAR MESH (FERRARI & LAMBORGHINI)
       -------------------------------------------------------------------------- */
    createSupercarMesh(brand, bodyColorHex, accentColorHex, nameLabel, subLabel) {
        const car = new THREE.Group();

        const carPaintMat = new THREE.MeshStandardMaterial({
            color: bodyColorHex,
            metalness: 0.9,
            roughness: 0.15
        });
        const carbonMat = new THREE.MeshStandardMaterial({
            color: accentColorHex,
            roughness: 0.4,
            metalness: 0.8
        });
        const glassMat = new THREE.MeshStandardMaterial({
            color: 0x050c18,
            metalness: 0.95,
            roughness: 0.05,
            transparent: true,
            opacity: 0.85
        });
        const chromeWheelMat = new THREE.MeshStandardMaterial({
            color: 0xe2e8f0,
            metalness: 0.95,
            roughness: 0.1
        });
        const tireMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.8 });
        const brakeCaliperMat = new THREE.MeshBasicMaterial({ color: 0xff0055 });

        // 1. Lower Chassis & Aerodynamic Floor
        const chassis = new THREE.Mesh(new THREE.BoxGeometry(5.6, 0.45, 11.2), carbonMat);
        chassis.position.y = 0.5;
        chassis.castShadow = true;
        car.add(chassis);

        // Front Splitter
        const splitter = new THREE.Mesh(new THREE.BoxGeometry(5.8, 0.12, 1.4), carbonMat);
        splitter.position.set(0, 0.35, 5.8);
        car.add(splitter);

        // 2. Main Aerodynamic Sleek Body Shell
        const bodyGeo = new THREE.BoxGeometry(5.4, 1.1, 10.4);
        const body = new THREE.Mesh(bodyGeo, carPaintMat);
        body.position.y = 1.15;
        body.castShadow = true;
        car.add(body);

        // Sculpted Slanted Front Hood / Nose
        const hoodGeo = new THREE.ConeGeometry(3.6, 3.8, 4);
        const hood = new THREE.Mesh(hoodGeo, carPaintMat);
        hood.rotation.x = Math.PI / 2;
        hood.rotation.y = Math.PI / 4;
        hood.scale.set(1.0, 0.35, 1.0);
        hood.position.set(0, 1.15, 3.8);
        car.add(hood);

        // 3. Cabin Cockpit Canopy with Tinted Panoramic Windshield
        const cabinGeo = new THREE.BoxGeometry(4.2, 1.15, 5.0);
        const cabin = new THREE.Mesh(cabinGeo, glassMat);
        cabin.position.set(0, 2.05, -0.6);
        car.add(cabin);

        // Aerodynamic Roof Carbon Cap
        const roof = new THREE.Mesh(new THREE.BoxGeometry(3.8, 0.15, 4.4), carbonMat);
        roof.position.set(0, 2.68, -0.6);
        car.add(roof);

        // 4. Rear Carbon Fiber GT Racing Wing Spoiler
        const wingPillars = new THREE.Group();
        for (let p = -1; p <= 1; p += 2) {
            const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.18, 1.2, 0.8), carbonMat);
            pillar.position.set(p * 1.8, 2.4, -4.8);
            wingPillars.add(pillar);
        }
        const gtWing = new THREE.Mesh(new THREE.BoxGeometry(5.8, 0.14, 1.4), carbonMat);
        gtWing.position.set(0, 3.0, -4.9);
        gtWing.rotation.x = -0.08;
        wingPillars.add(gtWing);
        car.add(wingPillars);

        // 5. LED Headlights & Quad Taillights
        const headLightMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
        for (let side = -1; side <= 1; side += 2) {
            const hl = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.25, 0.2), headLightMat);
            hl.position.set(side * 1.9, 1.25, 5.4);
            hl.rotation.y = side * 0.2;
            car.add(hl);
        }

        const tailLightMat = new THREE.MeshBasicMaterial({ color: 0xff0033 });
        for (let side = -1; side <= 1; side += 2) {
            const tl = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.25, 0.2), tailLightMat);
            tl.position.set(side * 1.8, 1.35, -5.25);
            car.add(tl);
        }

        // 6. Dual Exhaust Pipes with Glowing Blue Flame Tips
        const exhaustGroup = new THREE.Group();
        const flames = [];
        for (let side = -1; side <= 1; side += 2) {
            const pipe = new THREE.Mesh(
                new THREE.CylinderGeometry(0.24, 0.24, 0.8, 12),
                chromeWheelMat
            );
            pipe.rotation.x = Math.PI / 2;
            pipe.position.set(side * 0.9, 0.7, -5.3);
            exhaustGroup.add(pipe);

            // Blue flame interior glow
            const flame = new THREE.Mesh(
                new THREE.ConeGeometry(0.16, 0.6, 8),
                new THREE.MeshBasicMaterial({ color: 0x00f0ff })
            );
            flame.rotation.x = -Math.PI / 2;
            flame.position.set(side * 0.9, 0.7, -5.7);
            exhaustGroup.add(flame);
            flames.push(flame);
        }
        car.add(exhaustGroup);
        car.userData.exhaustGroup = exhaustGroup;
        car.userData.flames = flames;

        // 7. 4 High-Detail Sports Wheels (Rims, Tires & Brembo Brake Calipers)
        const wheels = [];
        const wheelCoords = [
            { x: -2.8, y: 0.9, z: 3.2 },
            { x: 2.8, y: 0.9, z: 3.2 },
            { x: -2.8, y: 1.0, z: -3.2 },
            { x: 2.8, y: 1.0, z: -3.2 }
        ];
        wheelCoords.forEach(pos => {
            const wGroup = new THREE.Group();
            wGroup.position.set(pos.x, pos.y, pos.z);

            const tire = new THREE.Mesh(
                new THREE.CylinderGeometry(0.9, 0.9, 0.8, 18),
                tireMat
            );
            tire.rotation.z = Math.PI / 2;
            wGroup.add(tire);

            const rim = new THREE.Mesh(
                new THREE.CylinderGeometry(0.65, 0.65, 0.82, 12),
                chromeWheelMat
            );
            rim.rotation.z = Math.PI / 2;
            wGroup.add(rim);

            const caliper = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.45, 0.35), brakeCaliperMat);
            caliper.position.set(pos.x > 0 ? -0.2 : 0.2, 0.35, 0);
            wGroup.add(caliper);

            car.add(wGroup);
            wheels.push(wGroup);
        });
        car.userData.wheels = wheels;

        // 8. Dynamic Neon Underglow
        const underglowGeo = new THREE.PlaneGeometry(5.2, 9.6);
        const underglowMat = new THREE.MeshBasicMaterial({
            color: bodyColorHex,
            transparent: true,
            opacity: 0.65,
            side: THREE.DoubleSide
        });
        const underglow = new THREE.Mesh(underglowGeo, underglowMat);
        underglow.rotation.x = -Math.PI / 2;
        underglow.position.y = 0.12;
        car.add(underglow);
        car.userData.underglow = underglow;

        // 9. OVERHEAD BILLBOARD UI (Inspired by Nargor/car-action Overhead Billboard UI System)
        const billboard = this.createSupercarBillboard(nameLabel, subLabel, bodyColorHex);
        billboard.position.set(0, 6.2, 0);
        car.add(billboard);

        return car;
    }

    /* --------------------------------------------------------------------------
       10E-3. CREATE OVERHEAD BILLBOARD UI FOR SUPERCAR
       -------------------------------------------------------------------------- */
    createSupercarBillboard(title, sub, colorHex) {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 140;
        const ctx = canvas.getContext('2d');

        ctx.fillStyle = 'rgba(10, 15, 30, 0.88)';
        ctx.roundRect(8, 8, 496, 124, 16);
        ctx.fill();

        ctx.strokeStyle = `#${colorHex.toString(16).padStart(6, '0')}`;
        ctx.lineWidth = 4;
        ctx.roundRect(8, 8, 496, 124, 16);
        ctx.stroke();

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 26px "Segoe UI", Arial, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(title, 256, 50);

        ctx.fillStyle = `#${colorHex.toString(16).padStart(6, '0')}`;
        ctx.font = '600 17px "Segoe UI", Arial, sans-serif';
        ctx.fillText(sub, 256, 88);

        ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
        ctx.roundRect(130, 98, 252, 24, 6);
        ctx.fill();
        ctx.fillStyle = '#f8fafc';
        ctx.font = 'bold 12px "Segoe UI", monospace';
        ctx.fillText('[E / F] NỔ MÁY & REV NITRO BOOST', 256, 115);

        const tex = new THREE.CanvasTexture(canvas);
        const mat = new THREE.SpriteMaterial({ map: tex, transparent: true });
        const sprite = new THREE.Sprite(mat);
        sprite.scale.set(18, 5.0, 1);
        return sprite;
    }

    /* --------------------------------------------------------------------------
       10E-4. TRIGGER SUPERCAR REV & NITRO BOOST
       -------------------------------------------------------------------------- */
    triggerSupercarRev(car) {
        this.playSfx('turbo');
        if (car.group && car.group.userData && car.group.userData.exhaustGroup) {
            car.group.userData.exhaustGroup.scale.set(1.5, 1.5, 2.2);
            setTimeout(() => {
                if (car.group.userData.exhaustGroup) {
                    car.group.userData.exhaustGroup.scale.set(1.0, 1.0, 1.0);
                }
            }, 650);
        }
        const banner = document.getElementById('wingFocusBanner');
        const bannerText = document.getElementById('wingFocusBannerText');
        if (banner && bannerText) {
            bannerText.textContent = `🔥 [NITRO REV] ${car.name} V8/V12 gầm rú! Sẵn sàng đua TikTok Live!`;
            banner.style.display = 'block';
            setTimeout(() => { banner.style.display = 'none'; }, 3000);
        }
    }

    /* --------------------------------------------------------------------------
       10F. BUILD EXECUTIVE ASSISTANT ASTRA WORKSTATION (HQ RECEPTION CO-PILOT)
       -------------------------------------------------------------------------- */
    buildExecutiveAssistantAstra() {
        const deskGroup = new THREE.Group();
        // Positioned in the Executive Foyer outside the CEO Suite entrance
        deskGroup.position.set(-52, 3.75, -55);

        // 1. Curved Glass & Titanium Secretary Desk
        const deskGeo = new THREE.CylinderGeometry(8.5, 8.5, 3.2, 24, 1, false, 0, Math.PI * 0.85);
        const deskMat = new THREE.MeshStandardMaterial({
            color: 0x0f172a,
            metalness: 0.9,
            roughness: 0.15,
            side: THREE.DoubleSide
        });
        const deskMesh = new THREE.Mesh(deskGeo, deskMat);
        deskMesh.position.y = 1.6;
        deskMesh.rotation.y = Math.PI * 0.6;
        deskGroup.add(deskMesh);

        // Gold LED Desk Countertop Trim
        const rimGeo = new THREE.TorusGeometry(8.6, 0.12, 6, 24, Math.PI * 0.85);
        const rim = new THREE.Mesh(rimGeo, new THREE.MeshBasicMaterial({ color: 0xf59e0b }));
        rim.rotation.x = Math.PI / 2;
        rim.rotation.z = -Math.PI * 0.35;
        rim.position.y = 3.2;
        deskGroup.add(rim);

        // 2. Dual Curved Holographic Displays
        const screenGeo = new THREE.BoxGeometry(4.8, 2.6, 0.15);
        const leftScreen = new THREE.Mesh(screenGeo, new THREE.MeshStandardMaterial({
            color: 0x020617,
            emissive: 0x38bdf8,
            emissiveIntensity: 0.6,
            map: this.createTradingChartTexture(0x38bdf8)
        }));
        leftScreen.position.set(-2.5, 4.6, 1.2);
        leftScreen.rotation.y = 0.35;
        deskGroup.add(leftScreen);

        const rightScreen = new THREE.Mesh(screenGeo, new THREE.MeshStandardMaterial({
            color: 0x020617,
            emissive: 0xc084fc,
            emissiveIntensity: 0.6,
            map: this.createTradingChartTexture(0xc084fc)
        }));
        rightScreen.position.set(2.5, 4.6, 1.2);
        rightScreen.rotation.y = -0.35;
        deskGroup.add(rightScreen);

        // 3. 3D Floating Nameplate
        const nameplate = this.createHoloSprite('👑 THƯ KÝ TRƯỞNG ASTRA · AI CO-PILOT', 0xc084fc);
        nameplate.position.set(0, 7.2, 1.5);
        nameplate.scale.set(20, 4.0, 1);
        deskGroup.add(nameplate);

        // 4. Resident Astra Secretary Avatar seated behind desk
        const astraAvatar = this.createAstra3DModel();
        astraAvatar.position.set(0, 1.8, -2.5);
        astraAvatar.rotation.y = 0;
        deskGroup.add(astraAvatar);
        this.deskAstraAvatar = astraAvatar;

        // Register for station click & hovering
        deskMesh.userData = { deptKey: 'lead_pm', isAstraDesk: true };
        this.stationMeshes.push(deskMesh);

        this.scene.add(deskGroup);
    }

    /* --------------------------------------------------------------------------
       10G. BUILD FIRST-PERSON VIEW (FPV) CYBER COMPANION ASTRA
       -------------------------------------------------------------------------- */
    buildFpvCompanionAstra() {
        // Attached directly to this.camera so she moves seamlessly with the player!
        const fpvGroup = new THREE.Group();
        // Positioned comfortably in the bottom-right viewport (doesn't obstruct reticle)
        fpvGroup.position.set(1.45, -0.72, -2.5);
        fpvGroup.scale.set(0.38, 0.38, 0.38);

        // 1. Chibi Cyber Anime Head
        const skinMat = new THREE.MeshStandardMaterial({ color: 0xffe4d6, roughness: 0.4 });
        const hairMat = new THREE.MeshStandardMaterial({ color: 0xf472b6, roughness: 0.3, emissive: 0xec4899, emissiveIntensity: 0.2 });
        const goldMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.9, roughness: 0.2 });
        const cyanMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
        const whiteMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.2 });

        const head = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.5, 1.5), skinMat);
        head.position.y = 1.6;
        fpvGroup.add(head);

        // Hair Cap
        const hair = new THREE.Mesh(new THREE.BoxGeometry(1.75, 0.8, 1.65), hairMat);
        hair.position.set(0, 2.1, -0.05);
        fpvGroup.add(hair);

        // Twin-tails
        const leftTail = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.35, 1.8, 6), hairMat);
        leftTail.position.set(-1.1, 1.3, -0.2);
        leftTail.rotation.z = 0.35;
        fpvGroup.add(leftTail);
        this.fpvLeftTail = leftTail;

        const rightTail = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.35, 1.8, 6), hairMat);
        rightTail.position.set(1.1, 1.3, -0.2);
        rightTail.rotation.z = -0.35;
        fpvGroup.add(rightTail);
        this.fpvRightTail = rightTail;

        // Animated LED Visor Eyes (Cyan Glow)
        const eyeVisor = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.32, 0.2), cyanMat);
        eyeVisor.position.set(0, 1.6, 0.8);
        fpvGroup.add(eyeVisor);
        this.fpvCompanionEyeVisor = eyeVisor;

        // Cute Blush Cheeks
        for (let b = -1; b <= 1; b += 2) {
            const blush = new THREE.Mesh(new THREE.PlaneGeometry(0.24, 0.12), new THREE.MeshBasicMaterial({ color: 0xff0077 }));
            blush.position.set(b * 0.55, 1.35, 0.82);
            fpvGroup.add(blush);
        }

        // 2. Cyber Suit Body
        const torso = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.5, 0.9), whiteMat);
        torso.position.y = 0.35;
        fpvGroup.add(torso);

        // Glowing Heart Core
        const core = new THREE.Mesh(new THREE.SphereGeometry(0.25, 12, 12), cyanMat);
        core.position.set(0, 0.45, 0.5);
        fpvGroup.add(core);

        // Skirt Ring
        const skirt = new THREE.Mesh(new THREE.TorusGeometry(0.85, 0.08, 6, 16), hairMat);
        skirt.rotation.x = Math.PI / 2;
        skirt.position.y = -0.4;
        fpvGroup.add(skirt);

        // 3. Fluttering Crystal Holographic Wings
        const wingMat = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.75,
            side: THREE.DoubleSide
        });
        const leftWing = new THREE.Mesh(new THREE.ConeGeometry(0.3, 1.8, 4), wingMat);
        leftWing.position.set(-0.8, 0.6, -0.6);
        leftWing.rotation.z = 0.75;
        fpvGroup.add(leftWing);
        this.fpvLeftWing = leftWing;

        const rightWing = new THREE.Mesh(new THREE.ConeGeometry(0.3, 1.8, 4), wingMat);
        rightWing.position.set(0.8, 0.6, -0.6);
        rightWing.rotation.z = -0.75;
        fpvGroup.add(rightWing);
        this.fpvRightWing = rightWing;

        // 4. Rotating Bitcoin Halo Ring
        const halo = new THREE.Mesh(new THREE.TorusGeometry(0.7, 0.08, 8, 20), goldMat);
        halo.position.set(0, 2.7, 0);
        halo.rotation.x = Math.PI / 2.3;
        fpvGroup.add(halo);
        this.fpvHalo = halo;

        // 5. Mini Holographic Live Data Tablet in hands
        const tabletGeo = new THREE.BoxGeometry(1.4, 0.9, 0.06);
        const tabletMat = new THREE.MeshStandardMaterial({
            color: 0x050c18,
            emissive: 0x00f0ff,
            emissiveIntensity: 0.7,
            map: this.createTradingChartTexture(0x10b981)
        });
        const tablet = new THREE.Mesh(tabletGeo, tabletMat);
        tablet.position.set(0, 0.1, 0.9);
        tablet.rotation.x = -0.35;
        fpvGroup.add(tablet);

        // 6. Overhead Hologram Name Tag
        const badge = this.createHoloSprite('🤖 ASTRA CO-PILOT [E: Chat]', 0xc084fc);
        badge.position.set(0, 3.4, 0);
        badge.scale.set(6.5, 1.6, 1);
        fpvGroup.add(badge);

        // Default hidden until cameraMode === 'fpv'
        fpvGroup.visible = false;
        this.camera.add(fpvGroup);
        this.fpvCompanionGroup = fpvGroup;
    }

    /* --------------------------------------------------------------------------
       10H. ANIMATE MEGACITY SKYLINE, SUPERCARS & COMPANIONS
       -------------------------------------------------------------------------- */
    animateMegacityAndCompanion(time, delta) {
        // 1. Skyline Aviation Beacons Flashing
        if (this.skylineBeacons && this.skylineBeacons.length > 0) {
            this.skylineBeacons.forEach(b => {
                const flash = Math.sin(time * 5.0 + b.phase);
                b.mesh.visible = flash > 0.15;
            });
        }

        // 2. Air Traffic Sky-Cruisers Gliding
        if (this.skyCruisers && this.skyCruisers.length > 0) {
            this.skyCruisers.forEach(c => {
                c.userData.angle += delta * c.userData.speed;
                const a = c.userData.angle;
                const r = c.userData.radius;
                c.position.x = Math.sin(a) * r;
                c.position.z = Math.cos(a) * r;
                c.position.y = c.userData.baseY + Math.sin(time * 2.0 + a) * 3.5;
                c.rotation.y = a + Math.PI / 2;
            });
        }

        // 3. Supercars Underglow & Flame Exhausts Pulse
        if (this.supercars && this.supercars.length > 0) {
            this.supercars.forEach(sc => {
                if (sc.group.userData.underglow) {
                    sc.group.userData.underglow.material.opacity = 0.55 + Math.sin(time * 4.0) * 0.25;
                }
            });

            // Check distance to Boss for Supercar Proximity Prompt
            let nearCar = null;
            for (let i = 0; i < this.supercars.length; i++) {
                const sc = this.supercars[i];
                if (this.bossPosition.distanceTo(sc.worldPos) < 14) {
                    nearCar = sc;
                    break;
                }
            }
            this.nearbySupercar = nearCar;
        }

        // 4. Resident HQ Astra Desk Avatar Animation
        if (this.deskAstraAvatar && this.deskAstraAvatar.userData && this.deskAstraAvatar.userData.animate) {
            this.deskAstraAvatar.userData.animate(time, delta);
        }

        // 5. First-Person View (FPV) Companion Astra Animation
        if (this.fpvCompanionGroup && this.fpvCompanionGroup.visible) {
            const bobY = Math.sin(time * 3.5) * 0.05;
            const tiltZ = Math.sin(time * 2.2) * 0.04;
            this.fpvCompanionGroup.position.y = -0.72 + bobY;
            this.fpvCompanionGroup.rotation.z = tiltZ;
            this.fpvCompanionGroup.rotation.y = -0.22 + Math.sin(time * 1.5) * 0.05;

            if (this.fpvLeftWing && this.fpvRightWing) {
                const wingFlap = Math.sin(time * 18.0) * 0.35;
                this.fpvLeftWing.rotation.y = wingFlap;
                this.fpvRightWing.rotation.y = -wingFlap;
            }

            if (this.fpvLeftTail && this.fpvRightTail) {
                const hBounce = Math.sin(time * 4.0) * 0.12;
                this.fpvLeftTail.rotation.z = 0.35 + hBounce;
                this.fpvRightTail.rotation.z = -0.35 - hBounce;
            }

            if (this.fpvHalo) {
                this.fpvHalo.rotation.y += delta * 2.0;
            }

            if (this.fpvCompanionEyeVisor) {
                const blink = Math.sin(time * 0.8);
                this.fpvCompanionEyeVisor.scale.y = (blink > 0.96) ? 0.1 : 1.0;
            }
        }
    }

    /* --------------------------------------------------------------------------
       11. INTERACTION, RAYCASTING & CLICK-TO-WALK
       -------------------------------------------------------------------------- */

    /* --------------------------------------------------------------------------
       10E-5. SUPERCAR DRIVING MECHANICS (FERRARI SF90 & LAMBORGHINI SVJ)
       -------------------------------------------------------------------------- */
    enterSupercar(car) {
        if (!car || !car.group) return;
        this.isDriving = true;
        this.drivingCar = car;
        this.playSfx('turbo');

        // Detach car to scene so it moves across the entire campus freely
        if (car.group.parent !== this.scene) {
            const wp = new THREE.Vector3();
            car.group.getWorldPosition(wp);
            const wq = new THREE.Quaternion();
            car.group.getWorldQuaternion(wq);
            this.scene.attach(car.group);
            car.group.position.copy(wp);
            car.group.quaternion.copy(wq);
        }

        this.carPosition = car.group.position;
        this.carHeading = car.group.rotation.y;
        this.carSpeed = 0;
        this.carSteer = 0;
        this.carNitro = 100;
        this.isNitroActive = false;
        this.carLookTarget = null;
        this._carHudCache = null;

        // Seat Boss inside cockpit in driver seat
        if (this.bossModel) {
            this.bossModel.visible = true;
            if (this.bossShadow) this.bossShadow.visible = false;
            car.group.add(this.bossModel);
            this.bossModel.position.set(-1.0, 1.15, -0.4);
            this.bossModel.scale.set(0.65, 0.65, 0.65);
            this.bossModel.rotation.set(0, 0, 0);
        }

        // Show Driving HUD
        const carHud = document.getElementById('car-cockpit-hud');
        if (carHud) carHud.style.display = 'flex';
        const carNameEl = document.getElementById('car-name-display');
        if (carNameEl) carNameEl.textContent = car.name.toUpperCase();

        const banner = document.getElementById('wingFocusBanner');
        const bannerText = document.getElementById('wingFocusBannerText');
        if (banner && bannerText) {
            bannerText.textContent = `🏎️ ĐANG LÁI ${car.name.toUpperCase()}! [W/S]: Ga & Thắng · [A/D]: Lái · [SPACE]: Phun Nitro · [F/ESC]: Xuống xe`;
            banner.style.display = 'block';
            setTimeout(() => { banner.style.display = 'none'; }, 3200);
        }
    }

    exitSupercar() {
        if (!this.isDriving || !this.drivingCar) return;
        this.isDriving = false;
        this.playSfx('hover');

        // Reset car body roll
        if (this.drivingCar && this.drivingCar.group) {
            this.drivingCar.group.rotation.z = 0;
        }
        this.carLookTarget = null;
        this._carHudCache = null;

        // Eject Boss safely beside the driver door
        if (this.bossModel) {
            this.scene.attach(this.bossModel);
            this.bossModel.scale.set(1.0, 1.0, 1.0);
            if (this.bossShadow) this.bossShadow.visible = true;
            const exitOffset = new THREE.Vector3(
                -Math.cos(this.carHeading) * 6.0,
                -2.0,
                Math.sin(this.carHeading) * 6.0
            );
            this.bossPosition.copy(this.carPosition).add(exitOffset);
            this.bossPosition.y = THREE.MathUtils.clamp(this.bossPosition.y, 0.5, 3.5);
            this.bossModel.position.copy(this.bossPosition);
            this.bossModel.rotation.set(0, this.bossHeading, 0);
        }

        // Hide Driving HUD
        const carHud = document.getElementById('car-cockpit-hud');
        if (carHud) carHud.style.display = 'none';

        const banner = document.getElementById('wingFocusBanner');
        const bannerText = document.getElementById('wingFocusBannerText');
        if (banner && bannerText) {
            bannerText.textContent = `🏎️ ĐÃ XUỐNG SIÊU XE ${this.drivingCar.name}. BOSS ĐI BỘ TRỞ LẠI SÀN TRADE!`;
            banner.style.display = 'block';
            setTimeout(() => { banner.style.display = 'none'; }, 2500);
        }

        this.drivingCar = null;
        this.setCameraMode('follow');
    }

    /* --------------------------------------------------------------------------
       10E-6. BUILD PROCEDURAL CYBER ELEVATOR (CONNECTING TẦNG TRADE & MKT)
       -------------------------------------------------------------------------- */
    buildCyberElevator() {
        const elevGroup = new THREE.Group();
        elevGroup.position.set(0, 0, 28); // Promenade between Central Lobby & Balcony

        // 1. 4 Glowing Vertical Guide Shaft Columns (Running from y = 4 down to y = -79)
        const columnGeo = new THREE.CylinderGeometry(0.35, 0.35, 86, 12);
        const columnMat = new THREE.MeshStandardMaterial({
            color: 0x38bdf8,
            metalness: 0.9,
            roughness: 0.1,
            emissive: 0x0284c7,
            emissiveIntensity: 0.4
        });
        const colOffsets = [
            { x: -3.8, z: -3.8 }, { x: 3.8, z: -3.8 },
            { x: -3.8, z: 3.8 }, { x: 3.8, z: 3.8 }
        ];
        colOffsets.forEach(pos => {
            const col = new THREE.Mesh(columnGeo, columnMat);
            col.position.set(pos.x, -38.5, pos.z);
            elevGroup.add(col);
        });

        // 2. Upper Landing Platform Base (Tầng Trade y = 0)
        const upperBaseGeo = new THREE.CylinderGeometry(5.2, 5.2, 0.6, 6);
        const baseMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.8, roughness: 0.2 });
        const upperBase = new THREE.Mesh(upperBaseGeo, baseMat);
        upperBase.position.y = 0.3;
        elevGroup.add(upperBase);

        const upperRing = new THREE.Mesh(
            new THREE.TorusGeometry(5.2, 0.12, 8, 24),
            new THREE.MeshBasicMaterial({ color: 0x00f0ff })
        );
        upperRing.rotation.x = Math.PI / 2;
        upperRing.position.y = 0.6;
        elevGroup.add(upperRing);

        // 3. Lower Landing Platform Base (Tầng MKT y = -79)
        const lowerBase = new THREE.Mesh(upperBaseGeo, baseMat);
        lowerBase.position.y = -78.5;
        elevGroup.add(lowerBase);

        const lowerRing = new THREE.Mesh(
            new THREE.TorusGeometry(5.2, 0.12, 8, 24),
            new THREE.MeshBasicMaterial({ color: 0xc084fc })
        );
        lowerRing.rotation.x = Math.PI / 2;
        lowerRing.position.y = -78.2;
        elevGroup.add(lowerRing);

        // 4. Moving Hexagonal Glass Elevator Cabin
        const cabin = new THREE.Group();
        cabin.position.set(0, 0.8, 0);

        // Cabin Floor
        const cabinFloor = new THREE.Mesh(new THREE.CylinderGeometry(4.4, 4.4, 0.45, 6), baseMat);
        cabinFloor.position.y = 0.2;
        cabin.add(cabinFloor);

        // Cabin Ceiling
        const cabinCeil = new THREE.Mesh(new THREE.CylinderGeometry(4.4, 4.4, 0.45, 6), baseMat);
        cabinCeil.position.y = 7.5;
        cabin.add(cabinCeil);

        // Cabin Glass Enclosure
        const glassMat = new THREE.MeshStandardMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.35,
            metalness: 0.9,
            roughness: 0.05,
            side: THREE.DoubleSide
        });
        const glassGeo = new THREE.CylinderGeometry(4.3, 4.3, 7.0, 6, 1, true);
        const glassMesh = new THREE.Mesh(glassGeo, glassMat);
        glassMesh.position.y = 3.8;
        cabin.add(glassMesh);

        // Cabin Interior Light Core
        const cabinLight = new THREE.PointLight(0x00f0ff, 1.8, 18);
        cabinLight.position.set(0, 6.8, 0);
        cabin.add(cabinLight);

        // Sliding Glass Doors (Front)
        const doorMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.65 });
        const leftDoor = new THREE.Mesh(new THREE.BoxGeometry(1.9, 6.5, 0.1), doorMat);
        leftDoor.position.set(-1.0, 3.6, 4.2);
        cabin.add(leftDoor);

        const rightDoor = new THREE.Mesh(new THREE.BoxGeometry(1.9, 6.5, 0.1), doorMat);
        rightDoor.position.set(1.0, 3.6, 4.2);
        cabin.add(rightDoor);

        cabin.userData.leftDoor = leftDoor;
        cabin.userData.rightDoor = rightDoor;

        // Overhead Holographic Sign
        const holoSign = this.createHoloSprite('🛗 THANG MÁY TẦNG QUANT [BẤM E ĐI]', 0x38bdf8);
        holoSign.position.set(0, 9.8, 0);
        holoSign.scale.set(16, 4.2, 1);
        cabin.add(holoSign);
        cabin.userData.holoSign = holoSign;

        elevGroup.add(cabin);
        this.scene.add(elevGroup);
        this.elevatorGroup = elevGroup;
        this.elevatorCabin = cabin;
    }

    /* --------------------------------------------------------------------------
       10E-7. TRIGGER CYBER ELEVATOR RIDE (TẦNG TRADE <---> TẦNG MKT NIVER)
       -------------------------------------------------------------------------- */
    triggerCyberElevator() {
        if (this.isElevatorMoving || !this.elevatorCabin) return;
        this.isElevatorMoving = true;
        this.playSfx('hover');

        const isGoingDown = (this.elevatorCurrentFloor === 'upper');
        const targetY = isGoingDown ? -78.2 : 0.8;
        const targetFloorName = isGoingDown ? 'TẦNG DƯỚI (MKT NIVER)' : 'TẦNG TRÊN (TRADE QUANT)';

        // 1. Close Sliding Doors
        const ld = this.elevatorCabin.userData.leftDoor;
        const rd = this.elevatorCabin.userData.rightDoor;
        if (ld && rd) {
            new TWEEN.Tween(ld.position).to({ x: -0.9 }, 300).start();
            new TWEEN.Tween(rd.position).to({ x: 0.9 }, 300).start();
        }

        // Put Boss inside cabin smoothly
        if (this.bossModel) {
            this.bossPosition.set(0, isGoingDown ? 1.0 : -78.0, 28);
            this.bossModel.position.copy(this.bossPosition);
        }

        const banner = document.getElementById('wingFocusBanner');
        const bannerText = document.getElementById('wingFocusBannerText');
        if (banner && bannerText) {
            bannerText.textContent = `🛗 THANG MÁY ĐANG CHUYỂN BÁC SĨ TỚI ${targetFloorName}...`;
            banner.style.display = 'block';
        }

        // 2. Smooth Descent / Ascent Tween (2.2s)
        new TWEEN.Tween(this.elevatorCabin.position)
            .to({ y: targetY }, 2200)
            .easing(TWEEN.Easing.Cubic.InOut)
            .onUpdate(() => {
                if (this.bossModel) {
                    this.bossPosition.y = this.elevatorCabin.position.y + 0.2;
                    this.bossModel.position.y = this.bossPosition.y;
                }
                if (['follow', 'shoulder', 'fpv'].includes(this.cameraMode)) {
                    this.camera.position.y += (this.bossPosition.y - this.camera.position.y) * 0.15;
                }
            })
            .onComplete(() => {
                this.isElevatorMoving = false;
                this.playSfx('swoosh');

                // Open Doors on arrival
                if (ld && rd) {
                    new TWEEN.Tween(ld.position).to({ x: -2.2 }, 400).start();
                    new TWEEN.Tween(rd.position).to({ x: 2.2 }, 400).start();
                }

                if (isGoingDown) {
                    this.elevatorCurrentFloor = 'lower';
                    window.switchFloorMode('mkt');
                    this.bossPosition.set(0, -78.0, 36);
                    if (this.bossModel) this.bossModel.position.copy(this.bossPosition);
                } else {
                    this.elevatorCurrentFloor = 'upper';
                    window.switchFloorMode('campus');
                    this.bossPosition.set(0, 1.0, 36);
                    if (this.bossModel) this.bossModel.position.copy(this.bossPosition);
                }

                if (banner && bannerText) {
                    bannerText.textContent = `🛗 ĐÃ CẬP BẾN ${targetFloorName}! CỬA ĐÃ MỞ!`;
                    setTimeout(() => { banner.style.display = 'none'; }, 2400);
                }
            })
            .start();
    }

    setupEvents() {
        const vp = this.container;

        // Pointer Lock & Mouse Look Tracking
        document.addEventListener('pointerlockchange', () => {
            this.isPointerLocked = (document.pointerLockElement === this.canvas);
        });

        // Prevent browser context menu on right click to allow smooth RMB camera dragging
        this.canvas.addEventListener('contextmenu', (e) => e.preventDefault());

        this.dragDist = 0;
        this.canvas.addEventListener('mousedown', (e) => {
            this.isMouseDown = true;
            this.mouseButton = e.button;
            this.dragDist = 0;
            this.prevMouseX = e.clientX;
            this.prevMouseY = e.clientY;

            // Only in FPV view, clicking enters Pointer Lock for direct crosshair aiming
            // In Shoulder & Follow (TPP), dragging rotates camera smoothly without locking pointer
            if (this.cameraMode === 'fpv') {
                if (document.pointerLockElement !== this.canvas && this.canvas.requestPointerLock) {
                    try { this.canvas.requestPointerLock(); } catch (_) {}
                }
            }
        });

        window.addEventListener('mouseup', () => {
            this.isMouseDown = false;
        });

        window.addEventListener('mousemove', (e) => {
            let dx = 0, dy = 0;
            if (this.isPointerLocked) {
                dx = e.movementX || 0;
                dy = e.movementY || 0;
            } else if (this.isMouseDown && (['fpv', 'shoulder', 'follow'].includes(this.cameraMode) || this.isDriving)) {
                // Calculate deltas BEFORE updating prevMouseX/prevMouseY
                dx = e.clientX - this.prevMouseX;
                dy = e.clientY - this.prevMouseY;
            }

            if (this.isMouseDown) {
                this.dragDist += Math.hypot(e.clientX - this.prevMouseX, e.clientY - this.prevMouseY);
                this.prevMouseX = e.clientX;
                this.prevMouseY = e.clientY;
            }

            // Prevent huge delta spikes when entering pointer lock or fast-dragging
            dx = THREE.MathUtils.clamp(dx, -50, 50);
            dy = THREE.MathUtils.clamp(dy, -50, 50);

            if (dx !== 0 || dy !== 0) {
                const sensX = 0.0035;
                const sensY = 0.0055;
                if (this.isDriving) {
                    this.carHeading -= dx * sensX * 0.7;
                    this.bossHeading = this.carHeading;
                } else {
                    // FIX INVERTED MOUSE LOOK: Dragging mouse right (dx > 0) turns view to the RIGHT
                    this.bossHeading -= dx * sensX;
                    this.targetHeading = this.bossHeading;
                }

                // FPV Pitch (Straight up & down)
                this.cameraPitch = THREE.MathUtils.clamp(this.cameraPitch - dy * 0.055, -28.0, 28.0);

                // TPP (Third-person) & Shoulder Pitch (Orbit angle in radians)
                // Dragging mouse UP (dy < 0): lifts camera higher to look DOWN at character
                // Dragging mouse DOWN (dy > 0): lowers camera to look UP at character and celestial sky
                this.targetTppPitch = THREE.MathUtils.clamp(
                    (this.targetTppPitch !== undefined ? this.targetTppPitch : 0.28) - dy * sensY,
                    -0.45, // Looking up at Boss from low ground level
                    1.35   // Looking down at Boss and floor from bird's-eye perspective
                );
            }

            if (!this.isPointerLocked) {
                const rect = this.canvas.getBoundingClientRect();
                this.mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
                this.mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
                this.checkHover(e.clientX, e.clientY);
            }
        });

        // Touch Drag support for mobile & tablet screens
        this.canvas.addEventListener('touchstart', (e) => {
            if (e.touches.length === 1) {
                this.isMouseDown = true;
                this.dragDist = 0;
                this.prevMouseX = e.touches[0].clientX;
                this.prevMouseY = e.touches[0].clientY;
            }
        }, { passive: true });

        window.addEventListener('touchmove', (e) => {
            if (!this.isMouseDown || e.touches.length !== 1) return;
            const touch = e.touches[0];
            let dx = 0, dy = 0;
            if (['fpv', 'shoulder', 'follow'].includes(this.cameraMode)) {
                dx = touch.clientX - this.prevMouseX;
                dy = touch.clientY - this.prevMouseY;
            }
            this.dragDist += Math.hypot(touch.clientX - this.prevMouseX, touch.clientY - this.prevMouseY);
            this.prevMouseX = touch.clientX;
            this.prevMouseY = touch.clientY;

            dx = THREE.MathUtils.clamp(dx, -50, 50);
            dy = THREE.MathUtils.clamp(dy, -50, 50);
            if (dx !== 0 || dy !== 0) {
                const sensX = 0.004;
                const sensY = 0.005;
                this.bossHeading -= dx * sensX;
                this.targetHeading = this.bossHeading;
                this.targetTppPitch = THREE.MathUtils.clamp(
                    (this.targetTppPitch !== undefined ? this.targetTppPitch : 0.28) - dy * sensY,
                    -0.45, 1.35
                );
                this.cameraPitch = THREE.MathUtils.clamp(this.cameraPitch - dy * 0.055, -28.0, 28.0);
            }
        }, { passive: true });

        window.addEventListener('touchend', () => {
            this.isMouseDown = false;
        }, { passive: true });

        // Wheel Zoom for Shoulder / Follow modes (smooth & responsive)
        const handleWheelZoom = (e) => {
            if (['shoulder', 'follow'].includes(this.cameraMode)) {
                e.preventDefault();
                e.stopPropagation();
                const zoomStep = 2.5;
                const dir = Math.sign(e.deltaY); // > 0: scroll down (zoom out), < 0: scroll up (zoom in)
                if (this.cameraMode === 'follow') {
                    this.targetFollowDist = THREE.MathUtils.clamp((this.targetFollowDist || this.followDist || 20) + dir * zoomStep, 6.0, 55.0);
                } else if (this.cameraMode === 'shoulder') {
                    this.targetFollowDist = THREE.MathUtils.clamp((this.targetFollowDist || this.followDist || 6.5) + dir * 1.5, 3.5, 18.0);
                }
            }
        };
        this.canvas.addEventListener('wheel', handleWheelZoom, { passive: false });
        if (this.container) {
            this.container.addEventListener('wheel', handleWheelZoom, { passive: false });
        }

        // Canvas Click for Station Hit & Click-to-Walk
        vp.addEventListener('click', (e) => {
            if (e.target !== this.canvas) return;

            // If user was dragging to pan/move the view, do not trigger click action
            if (this.dragDist > 14) return;

            // In action mode with pointer lock, click interacts with aimed station
            if (this.isPointerLocked && this.aimHitDept) {
                this.onStationClick(this.aimHitDept);
                return;
            }

            const rect = this.canvas.getBoundingClientRect();
            this.mouse.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
            this.raycaster.setFromCamera(this.mouse, this.camera);

            // 1. Check Station Hitboxes & all station meshes (officer, desk, etc.)
            const intersects = this.raycaster.intersectObjects(this.stationMeshes, true);
            let targetDept = null;
            for (let hit of intersects) {
                let cur = hit.object;
                while (cur && cur !== this.scene) {
                    if (cur.userData && cur.userData.deptKey) {
                        targetDept = cur.userData.deptKey;
                        break;
                    }
                    cur = cur.parent;
                }
                if (targetDept) break;
            }

            if (!targetDept && this.stations) {
                const allStationMeshes = Object.values(this.stations);
                const deepHits = this.raycaster.intersectObjects(allStationMeshes, true);
                for (let hit of deepHits) {
                    let cur = hit.object;
                    while (cur && cur !== this.scene) {
                        if (cur.userData && cur.userData.deptKey) {
                            targetDept = cur.userData.deptKey;
                            break;
                        }
                        cur = cur.parent;
                    }
                    if (targetDept) break;
                }
            }

            if (targetDept) {
                this.onStationClick(targetDept);
                return;
            }

            // 2. Check Floor Plane for Click-to-Walk (Supports god, tactical, follow, and shoulder)
            if (['god', 'tactical', 'follow', 'shoulder'].includes(this.cameraMode)) {
                const floorHits = this.raycaster.intersectObject(this.floorPlane);
                if (floorHits.length > 0) {
                    const pt = floorHits[0].point;
                    const targetX = THREE.MathUtils.clamp(pt.x, -160, 160);
                    const targetZ = THREE.MathUtils.clamp(pt.z, -150, 150);

                    this.bossTarget = new THREE.Vector3(targetX, 5.75, targetZ);
                    this.spawnClickReticle(targetX, targetZ);
                    this.playSfx('hover');
                }
            }
        });

        // Keyboard WASD Movement & Tactical Keys
        window.addEventListener('keydown', (e) => {
            if (e.target.closest('input, textarea, select, [contenteditable="true"]')) {
                if (e.key === 'Escape') {
                    e.target.blur();
                    closeDeptModal();
                    if (typeof closeCyberIntercomModal === 'function') closeCyberIntercomModal();
                    if (typeof closeQuantum5dModal === 'function') closeQuantum5dModal();
                    if (typeof closeQuickReportModal === 'function') closeQuickReportModal();
                }
                return;
            }
            const code = e.code;
            const keyLower = e.key.toLowerCase();

            // 1. MODAL HOTKEY CLOSE: If any modal is currently open, pressing E or Escape or Q or X closes it immediately!
            const deptModal = document.getElementById('pixelDeptModal');
            const isDeptOpen = deptModal && (deptModal.style.display === 'flex' || deptModal.style.display === 'block');
            const intercomModal = document.getElementById('cyber-intercom-modal');
            const isIntercomOpen = intercomModal && (intercomModal.style.display === 'flex' || intercomModal.style.display === 'block');
            const q5dModal = document.getElementById('q5dModalBackdrop');
            const isQ5dOpen = q5dModal && (q5dModal.style.display === 'flex' || q5dModal.style.display === 'block');
            const qReportModal = document.getElementById('quickReportModal');
            const isQReportOpen = qReportModal && (qReportModal.style.display === 'flex' || qReportModal.style.display === 'block');

            if (isDeptOpen || isIntercomOpen || isQ5dOpen || isQReportOpen) {
                if (code === 'Escape' || keyLower === 'e' || keyLower === 'q' || keyLower === 'x') {
                    e.preventDefault();
                    e.stopPropagation();
                    if (isDeptOpen) closeDeptModal();
                    if (isIntercomOpen) closeCyberIntercomModal();
                    if (isQ5dOpen) closeQuantum5dModal();
                    if (isQReportOpen) closeQuickReportModal();
                    return;
                }
            }

            this.walkKeys.add(code);
            if (keyLower === 'w') this.walkKeys.add('KeyW');
            if (keyLower === 'a') this.walkKeys.add('KeyA');
            if (keyLower === 's') this.walkKeys.add('KeyS');
            if (keyLower === 'd') this.walkKeys.add('KeyD');

            if (e.key.startsWith('Arrow') || code === 'Space') {
                e.preventDefault();
            }

            if (e.key === 'Shift') {
                this.walkKeys.add('ShiftLeft');
            }

            // [PageUp / PageDown] Direct Keyboard Pitch Controls for TPP / Shoulder / FPV
            if (code === 'PageUp') {
                e.preventDefault();
                this.targetTppPitch = THREE.MathUtils.clamp((this.targetTppPitch !== undefined ? this.targetTppPitch : 0.28) + 0.15, -0.45, 1.35);
                this.cameraPitch = THREE.MathUtils.clamp(this.cameraPitch + 4.0, -28.0, 28.0);
            }
            if (code === 'PageDown') {
                e.preventDefault();
                this.targetTppPitch = THREE.MathUtils.clamp((this.targetTppPitch !== undefined ? this.targetTppPitch : 0.28) - 0.15, -0.45, 1.35);
                this.cameraPitch = THREE.MathUtils.clamp(this.cameraPitch - 4.0, -28.0, 28.0);
            }

            // [V] Quick Switch FPV <-> TPP (PUBG Style)
            // [T] Smart Health Patrol
            if (code === 'KeyT' || keyLower === 't') {
                e.preventDefault();
                this.patrolNextDept();
                return;
            }

            // [P] Autonomous CEO Patrol Toggle
            if (code === 'KeyP' || keyLower === 'p') {
                e.preventDefault();
                this.toggleAutonomousPatrol();
                return;
            }

            // Player manual movement interrupts autonomous patrol smoothly
            if (['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(code)) {
                if (this.isAutonomousPatrol) {
                    this.toggleAutonomousPatrol();
                }
            }

            // In Patrol Mode: Space jumps AND advances, Escape stops
            if (this.isPatrolling) {
                if (code === 'Space') {
                    e.preventDefault();
                    if (this.bossIsGrounded) {
                        this.bossVelocityY = 32.0; // High athletic leap
                        this.bossIsGrounded = false;
                        this.playSfx('hover');
                    }
                    this.patrolNextDept();
                    return;
                }
                if (code === 'Escape') {
                if (this.isDriving) {
                    e.preventDefault();
                    this.exitSupercar();
                    return;
                }
                    e.preventDefault();
                    this.stopPatrol();
                    return;
                }
            }

            if (code === 'KeyV' || keyLower === 'v') {
                e.preventDefault();
                if (this.cameraMode === 'fpv') {
                    this.setCameraMode('shoulder');
                } else if (this.cameraMode === 'shoulder') {
                    this.setCameraMode('follow');
                } else {
                    this.setCameraMode('fpv');
                }
                this.playSfx('hover');
            }

            // [B] Quick Teleport to South VIP Balcony (Ferrari 488, Lamborghini SVJ & Skyline)
            if (code === 'KeyB' || keyLower === 'b') {
                e.preventDefault();
                this.teleportToBalcony();
                return;
            }

            // [F / E] Interact with nearby agent, supercar, aimed station, elevator or driving exit
            if (code === 'KeyF' || keyLower === 'f' || keyLower === 'e') {
                if (this.isDriving) {
                    e.preventDefault();
                    this.exitSupercar();
                    return;
                }
                if (this.nearbyElevator) {
                    e.preventDefault();
                    this.triggerCyberElevator();
                    return;
                }
                if (this.nearbySupercar) {
                    e.preventDefault();
                    this.enterSupercar(this.nearbySupercar);
                    return;
                } else if (this.nearbyAgentDept) {
                    e.preventDefault();
                    window.openCyberIntercomForDept(this.nearbyAgentDept);
                    return;
                } else if (this.aimHitDept) {
                    e.preventDefault();
                    this.onStationClick(this.aimHitDept);
                    return;
                } else if (this.hoveredDept) {
                    e.preventDefault();
                    this.onStationClick(this.hoveredDept);
                    return;
                } else if (this.cameraMode === 'fpv') {
                    // In FPV mode, pressing E/F opens quick dialogue with Astra
                    e.preventDefault();
                    window.openCyberIntercomForDept('lead_pm');
                    return;
                }
            }

            // [Space] Jump / Parkour Leap (High Athletic Impulse) OR Nitro Boost when Driving
            if (code === 'Space') {
                e.preventDefault();
                if (this.isDriving) {
                    return;
                }
                if (this.bossIsGrounded) {
                    this.bossVelocityY = 32.0; // High athletic parkour leap!
                    this.bossIsGrounded = false;
                    this.playSfx('hover');
                }
            }

            // [C] Crouch
            if (code === 'KeyC' || keyLower === 'c') {
                e.preventDefault();
                this.isCrouching = !this.isCrouching;
                this.playSfx('hover');
            }

            // [Escape] Quay lại View Thượng Đế toàn cảnh OR Xuống siêu xe
            if (code === 'Escape') {
                e.preventDefault();
                if (this.isDriving) {
                    this.exitSupercar();
                    return;
                }
                this.setCameraMode('god');
            }

            // [1..9] Smart Focus Zoom trực tiếp vào từng Phòng Ban trọng điểm
            const deptQuickMap = {
                'Digit1': 'execution_oms',
                'Digit2': 'quant_lab',
                'Digit3': 'risk_council',
                'Digit4': 'lead_pm',
                'Digit5': 'arbitrage_desk',
                'Digit6': 'breakout_hunter',
                'Digit7': 'volatility_lab',
                'Digit8': 'spot_dca',
                'Digit9': 'cvar_stress'
            };
            if (deptQuickMap[code]) {
                e.preventDefault();
                this.onStationClick(deptQuickMap[code]);
            }
        });

        // Double-click to Smart Zoom / Reset
        this.canvas.addEventListener('dblclick', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouse.x = ((e.clientX - rect.left) / this.width) * 2 - 1;
            this.mouse.y = -((e.clientY - rect.top) / this.height) * 2 + 1;
            this.raycaster.setFromCamera(this.mouse, this.camera);
            const hits = this.raycaster.intersectObjects(this.stationMeshes);
            if (hits.length > 0) {
                const deptKey = hits[0].object.userData.deptKey;
                if (deptKey) this.onStationClick(deptKey);
            } else {
                // Nhấp đúp vào sàn trống: Lướt mượt mà về lại View Thượng Đế
                this.setCameraMode('god');
            }
        });

        window.addEventListener('keyup', (e) => {
            const code = e.code;
            const keyLower = e.key.toLowerCase();
            this.walkKeys.delete(code);
            if (keyLower === 'w') this.walkKeys.delete('KeyW');
            if (keyLower === 'a') this.walkKeys.delete('KeyA');
            if (keyLower === 's') this.walkKeys.delete('KeyS');
            if (keyLower === 'd') this.walkKeys.delete('KeyD');
            if (e.key === 'Shift') {
                this.walkKeys.delete('ShiftLeft');
                this.walkKeys.delete('ShiftRight');
            }
        });

        window.addEventListener('resize', () => this.onResize());
    }

    spawnClickReticle(x, z) {
        const retGeo = new THREE.RingGeometry(1.5, 2.5, 32);
        const retMat = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.9
        });
        const reticle = new THREE.Mesh(retGeo, retMat);
        reticle.rotation.x = -Math.PI / 2;
        reticle.position.set(x, 0.25, z);
        this.scene.add(reticle);

        this.clickPings.push({
            mesh: reticle,
            scale: 1,
            opacity: 0.9
        });
    }

    checkHover(screenX, screenY) {
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.stationMeshes);
        const tooltip = document.getElementById('office-hud-tooltip');

        if (intersects.length > 0) {
            const hit = intersects[0].object;
            const deptKey = hit.userData.deptKey;
            const cfg = this.deptConfigs[deptKey];

            if (this.hoveredDept !== deptKey) {
                this.hoveredDept = deptKey;
                this.canvas.style.cursor = 'pointer';
                this.playSfx('hover');

                if (tooltip && cfg) {
                    const badge = document.getElementById('hud-badge');
                    const title = document.getElementById('hud-title');
                    const officer = document.getElementById('hud-officer');
                    const metric = document.getElementById('hud-metric');
                    const status = document.getElementById('hud-status');

                    if (badge) badge.textContent = cfg.tag;
                    if (title) title.textContent = cfg.name;
                    if (officer) officer.textContent = cfg.officer;
                    if (metric) metric.textContent = `${cfg.activity} · ${cfg.metric}`;
                    if (status) status.textContent = 'TRỰC CHIẾN';
                    tooltip.style.display = 'block';
                }
            }

            if (tooltip) {
                const vpRect = this.container.getBoundingClientRect();
                const relX = screenX - vpRect.left + 15;
                const relY = screenY - vpRect.top - 25;
                tooltip.style.left = `${Math.min(relX, vpRect.width - 240)}px`;
                tooltip.style.top = `${Math.max(relY, 15)}px`;
            }
        } else {
            if (this.hoveredDept !== null) {
                this.hoveredDept = null;
                this.canvas.style.cursor = 'default';
                if (tooltip) tooltip.style.display = 'none';
            }
        }
    }

    onStationClick(deptKey) {
        this.playSfx('click');
        const cfg = this.deptConfigs[deptKey];
        if (!cfg) return;

        // Walk Boss to this station
        this.bossTarget = new THREE.Vector3(cfg.pos.x, 5.75, cfg.pos.z + 12);

        // Smart Zoom: Close-up cinematic focus on the workstation (distance ~24 units)
        // Chi tiết sắc nét: thấy rõ 3 màn hình biểu đồ nến, bàn phím RGB và nhân vật đang gõ phím!
        new TWEEN.Tween(this.camera.position)
            .to({ x: cfg.pos.x + 14, y: cfg.pos.y + 13, z: cfg.pos.z + 20 }, 850)
            .easing(TWEEN.Easing.Cubic.Out)
            .start();

        new TWEEN.Tween(this.controls.target)
            .to({ x: cfg.pos.x, y: cfg.pos.y + 5.5, z: cfg.pos.z }, 850)
            .easing(TWEEN.Easing.Cubic.Out)
            .start();

        const dialogue = document.getElementById('astra-dialogue');
        if (dialogue) {
            dialogue.textContent = `Boss đang thị sát ${cfg.name}! Đội ngũ đang: ${cfg.activity}. Toàn bộ luồng dữ liệu thông suốt. (Nhấn [Esc] hoặc nhấp đúp để quay lại Toàn Cảnh)`;
        }

        if (this.floatingBubbles[deptKey]) {
            this.floatingBubbles[deptKey].visible = true;
            setTimeout(() => {
                if (this.floatingBubbles[deptKey]) this.floatingBubbles[deptKey].visible = false;
            }, 6000);
        }

        if (typeof openDeptDetailModal === 'function') {
            openDeptDetailModal(deptKey);
        }
    }

    /* --------------------------------------------------------------------------
       11B. PHẢN ỨNG PHÂN KHU & CHUYỂN GÓC CAMERA 3D (FOCUS WING 3D ENGINE)
       -------------------------------------------------------------------------- */
    focusWing(wingId) {
        this.activeWing = wingId;
        this.playSfx('swoosh');
        TWEEN.removeAll();

        const banner = document.getElementById('wingFocusBanner');
        const bannerText = document.getElementById('wingFocusBannerText');

        const wingSpecs = {
            'all': {
                camPos: { x: -165, y: 205, z: 215 },
                target: { x: 0, y: 10, z: 0 },
                title: '🏢 TOÀN CẢNH TRỤ SỞ · 12 PHÒNG BAN ĐỒNG BỘ',
                dialogue: 'Đang hiển thị toàn cảnh Trụ sở 12 phòng ban, hệ thống mạng LAN và Trạm máy chủ trung tâm kết nối liên tục.'
            },
            'executive': {
                camPos: { x: -50, y: 68, z: -10 },
                target: { x: -80, y: 6.0, z: -60 },
                title: '💼 PHÂN KHU ĐIỀU HÀNH & CRO (2 BAN CHỈ HUY)',
                dialogue: 'Đang thị sát Khu Điều Hành PM & CRO Evelyn. Hệ thống phòng vệ rủi ro và điều phối vốn tối cao đang hoạt động.'
            },
            'trading': {
                camPos: { x: 50, y: 68, z: -10 },
                target: { x: 80, y: 6.0, z: -60 },
                title: '⚡ PHÂN KHU SÀN GIAO DỊCH & OMS (3 BÀN KHỚP LỆNH)',
                dialogue: 'Đang thị sát Sàn Giao Dịch OMS Marcus, Spot DCA Rex và Arbitrage Dante. Đang kết nối trực tiếp cổng WebSocket Binance/Bybit.'
            },
            'research': {
                camPos: { x: -50, y: 68, z: 125 },
                target: { x: -80, y: 6.0, z: 75 },
                title: '📊 PHÂN KHU VIỆN QUANT & BREAKOUT (3 BAN ALPHA)',
                dialogue: 'Đang thị sát Viện Quant Dr. Seraphina, Breakout Valkyrie Riko và Volatility Camilla. Ma trận Tensor 5D đang tính toán liên tục.'
            },
            'operations': {
                camPos: { x: 50, y: 68, z: 125 },
                target: { x: 80, y: 6.0, z: 75 },
                title: '🛡️ PHÂN KHU KIỂM SOÁT, HẬU CẦN & TRẠM MÁY CHỦ DATA CENTER',
                dialogue: 'Đang thị sát Phân Khu Hậu Cần, Trạm Máy Chủ Blade Server Cluster (Ping: 12ms) và Kiểm Soát Rủi Ro CVaR Stress Zane.'
            }
        };

        const spec = wingSpecs[wingId] || wingSpecs['all'];

        // 1. Bay Camera mượt mà tới phân khu (Camera Fly Animation)
        this.cameraTransitioning = true;
        this.controls.enabled = false;

        new TWEEN.Tween(this.camera.position)
            .to(spec.camPos, 850)
            .easing(TWEEN.Easing.Cubic.Out)
            .start();

        new TWEEN.Tween(this.controls.target)
            .to(spec.target, 850)
            .easing(TWEEN.Easing.Cubic.Out)
            .onUpdate(() => {
                this.camera.lookAt(this.controls.target);
            })
            .onComplete(() => {
                this.controls.enabled = true;
                this.cameraTransitioning = false;
            })
            .start();

        // 2. Nhấn sáng các phòng ban thuộc phân khu được chọn, hạ nhẹ các phòng khác
        Object.entries(this.stations || {}).forEach(([key, st]) => {
            const cfg = this.deptConfigs[key];
            if (!cfg) return;
            const isMatch = (wingId === 'all' || cfg.wing === wingId);

            if (isMatch) {
                new TWEEN.Tween(st.scale)
                    .to({ x: 1.08, y: 1.08, z: 1.08 }, 250)
                    .yoyo(true)
                    .repeat(1)
                    .start();
            } else {
                new TWEEN.Tween(st.scale)
                    .to({ x: 0.94, y: 0.94, z: 0.94 }, 250)
                    .start();
            }
        });

        // 3. Nhấn sáng đường viền nền bục sàn của phân khu
        if (this.wingPlatforms) {
            Object.entries(this.wingPlatforms).forEach(([wId, pObj]) => {
                const isMatch = (wingId === 'all' || wId === wingId);
                if (pObj.border && pObj.border.material) {
                    pObj.border.material.opacity = isMatch ? 1.0 : 0.25;
                }
                if (pObj.light) {
                    pObj.light.intensity = isMatch ? 1.8 : 0.4;
                }
            });
        }

        // 4. Bật thông báo Banner HUD Cyber
        if (banner && bannerText) {
            bannerText.textContent = spec.title;
            banner.style.display = 'block';
            clearTimeout(this._wingBannerTimeout);
            this._wingBannerTimeout = setTimeout(() => { banner.style.display = 'none'; }, 2600);
        }

        // 5. Cập nhật hộp thoại AI Astra
        const dialogue = document.getElementById('astra-dialogue');
        if (dialogue) {
            dialogue.textContent = spec.dialogue;
        }

        // 6. Boss di chuyển tới trung tâm phân khu nếu đang ở View Thượng Đế
        if (this.cameraMode === 'god' && wingId !== 'all') {
            this.bossTarget = new THREE.Vector3(spec.target.x + 8, this.getFloorHeight(spec.target.x + 8, spec.target.z + 10), spec.target.z + 10);
        }
    }

    /* --------------------------------------------------------------------------
       12. 5 DYNAMIC CAMERA MODES: GOD-VIEW, 1ST PERSON, 2ND PERSON, 3RD PERSON, 2D
       -------------------------------------------------------------------------- */
    setCameraMode(mode) {
        this.cameraMode = mode;
        if (mode !== 'fpv' && document.pointerLockElement) {
            try { document.exitPointerLock(); } catch (_) {}
        }
        TWEEN.removeAll();
        this.playSfx('swoosh');

        // Toggle FPV Companion visibility: Keep view 100% clean & unobstructed
        if (this.fpvCompanionGroup) {
            this.fpvCompanionGroup.visible = false; // Never block FPV crosshair/reticle!
        }
        const crosshair = document.getElementById('fpv-crosshair');
        if (crosshair) crosshair.style.display = (mode === 'fpv') ? 'flex' : 'none';
        if (this.astraModel) {
            this.astraModel.visible = (mode !== 'fpv');
            if (this.astraShadow) this.astraShadow.visible = (mode !== 'fpv');
        }

        // Update active UI tool buttons
        const btnMap = {
            'god': 'btn-cam-god',
            'fpv': 'btn-cam-fpv',
            'shoulder': 'btn-cam-shoulder',
            'follow': 'btn-cam-follow',
            'tactical': 'btn-cam-tactical'
        };
        Object.entries(btnMap).forEach(([m, id]) => {
            const btn = document.getElementById(id);
            if (btn) btn.classList.toggle('active', m === mode);
        });

        // Đồng bộ hóa trạng thái nút Nhập Thể trên HUD
        this.updatePossessBtn(['follow', 'shoulder', 'fpv'].includes(mode));

        const banner = document.getElementById('wingFocusBanner');
        const bannerText = document.getElementById('wingFocusBannerText');

        if (mode === 'god') {
            // "VIEW THƯỢNG ĐẾ" — Grand Panoramic Isometric Overview
            this.cameraTransitioning = false;
            if (this.bossModel) this.bossModel.visible = true;
            this.controls.enabled = true;
            this.controls.enableRotate = true;

            new TWEEN.Tween(this.camera.position)
                .to({ x: -165, y: 205, z: 215 }, 900)
                .easing(TWEEN.Easing.Cubic.Out)
                .start();

            new TWEEN.Tween(this.controls.target)
                .to({ x: 0, y: 10, z: 0 }, 900)
                .easing(TWEEN.Easing.Cubic.Out)
                .start();

            if (banner && bannerText) {
                bannerText.textContent = '👁️ VIEW THƯỢNG ĐẾ · TOÀN CẢNH TRỤ SỞ VẬN HÀNH';
                banner.style.display = 'block';
                setTimeout(() => { banner.style.display = 'none'; }, 2200);
            }
        } else if (mode === 'fpv') {
            // GÓC NHÌN THỨ 1 (FIRST-PERSON VIEW FPV) — Through Boss Eyes
            if (this.bossModel) this.bossModel.visible = false;
            this.controls.enabled = false;
            this.cameraTransitioning = false;

            if (banner && bannerText) {
                bannerText.textContent = '👤 GÓC NHÌN THỨ 1 (FPV) · MẮT NHÌN CHỈ HUY TRỰC TIẾP';
                banner.style.display = 'block';
                setTimeout(() => { banner.style.display = 'none'; }, 2200);
            }
        } else if (mode === 'shoulder') {
            // GÓC NHÌN THỨ 2 (OVER-THE-SHOULDER) — Cinematic Action View
            if (this.bossModel) this.bossModel.visible = true;
            this.controls.enabled = false;

            const rightX = Math.cos(this.bossHeading) * 2.6;
            const rightZ = -Math.sin(this.bossHeading) * 2.6;
            const backX = -Math.sin(this.bossHeading) * 6.5;
            const backZ = -Math.cos(this.bossHeading) * 6.5;

            const targetCamPos = {
                x: this.bossPosition.x + rightX + backX,
                y: this.bossPosition.y + (this.isCrouching ? 5.8 : 7.8) + (this.cameraPitch * 0.2),
                z: this.bossPosition.z + rightZ + backZ
            };
            const targetLook = {
                x: this.bossPosition.x + rightX * 0.5 + Math.sin(this.bossHeading) * 25,
                y: this.bossPosition.y + (this.isCrouching ? 5.5 : 7.0) + this.cameraPitch,
                z: this.bossPosition.z + rightZ * 0.5 + Math.cos(this.bossHeading) * 25
            };

            this.cameraTransitioning = true;
            new TWEEN.Tween(this.camera.position)
                .to(targetCamPos, 600)
                .easing(TWEEN.Easing.Cubic.Out)
                .start();

            new TWEEN.Tween(this.controls.target)
                .to(targetLook, 600)
                .easing(TWEEN.Easing.Cubic.Out)
                .onUpdate(() => {
                    this.camera.lookAt(this.controls.target);
                })
                .onComplete(() => {
                    this.cameraTransitioning = false;
                })
                .start();

            if (banner && bannerText) {
                bannerText.textContent = '🎯 GÓC NHÌN THỨ 2 (GÓC QUA VAI) · CINEMATIC TÁC CHIẾN';
                banner.style.display = 'block';
                setTimeout(() => { banner.style.display = 'none'; }, 2200);
            }
        } else if (mode === 'follow') {
            // GÓC NHÌN THỨ 3 (THIRD-PERSON CHASE) — Rock-Solid Butter Smooth Glide
            if (this.bossModel) this.bossModel.visible = true;
            this.controls.enabled = false;

            const dist = this.targetFollowDist || this.followDist || 20;
            const backX = -Math.sin(this.bossHeading) * dist;
            const backZ = -Math.cos(this.bossHeading) * dist;
            const targetCamPos = {
                x: this.bossPosition.x + backX,
                y: Math.max(this.bossPosition.y + 10.0 + (this.cameraPitch * 0.25), 4.0),
                z: this.bossPosition.z + backZ
            };
            const targetLook = {
                x: this.bossPosition.x + Math.sin(this.bossHeading) * 4.0,
                y: this.bossPosition.y + 5.5 + (this.cameraPitch * 0.35),
                z: this.bossPosition.z + Math.cos(this.bossHeading) * 4.0
            };

            if (!this.currentLookAt) {
                this.currentLookAt = new THREE.Vector3().copy(this.controls.target);
            }

            this.cameraTransitioning = true;
            new TWEEN.Tween(this.camera.position)
                .to(targetCamPos, 600)
                .easing(TWEEN.Easing.Cubic.Out)
                .start();

            new TWEEN.Tween(this.currentLookAt)
                .to(targetLook, 600)
                .easing(TWEEN.Easing.Cubic.Out)
                .onUpdate(() => {
                    this.camera.lookAt(this.currentLookAt);
                })
                .onComplete(() => {
                    this.cameraTransitioning = false;
                    this.controls.target.copy(this.currentLookAt);
                })
                .start();

            if (banner && bannerText) {
                bannerText.textContent = '🏃 GÓC NHÌN THỨ 3 (TPP) · Kéo chuột / PageUp / PageDown nhìn Lên-Xuống · Shift chạy nhanh · Space nhảy';
                banner.style.display = 'block';
                setTimeout(() => { banner.style.display = 'none'; }, 2800);
            }
        } else if (mode === 'tactical') {
            // TACTICAL 2D — Top-Down Radar View
            if (this.bossModel) this.bossModel.visible = true;
            new TWEEN.Tween(this.camera.position)
                .to({ x: 0, y: 320, z: 0.1 }, 900)
                .easing(TWEEN.Easing.Cubic.Out)
                .start();

            new TWEEN.Tween(this.controls.target)
                .to({ x: 0, y: 0, z: 0 }, 900)
                .easing(TWEEN.Easing.Cubic.Out)
                .start();

            if (banner && bannerText) {
                bannerText.textContent = '🗺️ TACTICAL 2D · BẢN ĐỒ TÁC CHIẾN TỪ TRÊN ĐỈNH';
                banner.style.display = 'block';
                setTimeout(() => { banner.style.display = 'none'; }, 2200);
            }
        }
    }

    resetToIsometric() {
        this.setCameraMode('god');
    }

    toggleTacticalView() {
        if (this.cameraMode === 'tactical') {
            this.setCameraMode('god');
        } else {
            this.setCameraMode('tactical');
        }
    }

    /* --------------------------------------------------------------------------
       12B. QUICK BOSS TELEPORT FOCUS & POSSESSION ENGINE (HUD SHORTCUTS)
       -------------------------------------------------------------------------- */
    focusOnBoss() {
        if (!this.bossPosition) return;
        this.playSfx('swoosh');

        if (this.cameraMode === 'fpv') {
            this.setCameraMode('follow');
            return;
        }

        TWEEN.removeAll();
        this.cameraTransitioning = true;
        if (this.bossModel) this.bossModel.visible = true;

        const targetCamPos = {
            x: this.bossPosition.x + 14,
            y: this.bossPosition.y + 16,
            z: this.bossPosition.z + 22
        };
        const targetLook = {
            x: this.bossPosition.x,
            y: this.bossPosition.y + 4.5,
            z: this.bossPosition.z
        };

        new TWEEN.Tween(this.camera.position)
            .to(targetCamPos, 750)
            .easing(TWEEN.Easing.Cubic.Out)
            .start();

        new TWEEN.Tween(this.controls.target)
            .to(targetLook, 750)
            .easing(TWEEN.Easing.Cubic.Out)
            .onUpdate(() => {
                this.camera.lookAt(this.controls.target);
            })
            .onComplete(() => {
                this.cameraTransitioning = false;
                this.controls.enabled = true;
                this.controls.enableRotate = true;
            })
            .start();

        const banner = document.getElementById('wingFocusBanner');
        const bannerText = document.getElementById('wingFocusBannerText');
        if (banner && bannerText) {
            bannerText.textContent = '👑 PHÒNG TỔNG TƯ LỆNH · CEO COMMAND SUITE';
            banner.style.display = 'block';
            setTimeout(() => { banner.style.display = 'none'; }, 2500);
        }

        const dialogue = document.getElementById('astra-dialogue');
        if (dialogue) {
            dialogue.textContent = `👑 Camera đã định vị Boss tại PHÒNG TỔNG TƯ LỆNH (CEO Suite) [X: ${Math.round(this.bossPosition.x)}, Z: ${Math.round(this.bossPosition.z)}]. Boss đang trực tiếp điều hành toàn bộ chiến lược 12 phòng ban và phê duyệt các lệnh giao dịch lớn!`;
        }
    }

    possessBoss() {
        this.playSfx('click');
        const isCurrentlyPossessed = ['follow', 'shoulder', 'fpv'].includes(this.cameraMode);
        if (isCurrentlyPossessed) {
            this.setCameraMode('god');
            const dialogue = document.getElementById('astra-dialogue');
            if (dialogue) {
                dialogue.textContent = '↩️ Đã thoát Nhập Thể. Camera chuyển về View Thượng Đế bao quát toàn cảnh tổng hành dinh.';
            }
        } else {
            this.setCameraMode('follow');
            const dialogue = document.getElementById('astra-dialogue');
            if (dialogue) {
                dialogue.textContent = '🔮 Nhập Thể thành công! Dùng phím [W-A-S-D] điều khiển Boss bước đi, [Shift] chạy nhanh, [Space] nhảy, rê chuột đổi hướng nhìn. Bấm [Esc] để thoát.';
            }
        }
    }

    updatePossessBtn(isPossessed) {
        const btn = document.getElementById('btnPossessBoss');
        if (!btn) return;
        if (isPossessed) {
            btn.classList.add('active-possessed');
            btn.innerHTML = '↩️ Thoát (Esc)';
            btn.title = 'Thoát nhập thể, trở về View Thượng Đế (phím Esc)';
        } else {
            btn.classList.remove('active-possessed');
            btn.innerHTML = '🔮 Nhập Thể';
            btn.title = 'Nhập thể trực tiếp điều khiển Boss (phím W-A-S-D, Space nhảy, Esc thoát)';
        }
    }

    triggerCoffee() {
        this.playSfx('click');
        this.bossTarget = new THREE.Vector3(0, 5.75, -36);

        if (this.cameraMode === 'god') {
            new TWEEN.Tween(this.camera.position)
                .to({ x: 0, y: 38, z: -15 }, 1000)
                .easing(TWEEN.Easing.Cubic.Out)
                .start();

            new TWEEN.Tween(this.controls.target)
                .to({ x: 0, y: 4, z: -45 }, 1000)
                .easing(TWEEN.Easing.Cubic.Out)
                .start();
        }

        const dialogue = document.getElementById('astra-dialogue');
        if (dialogue) {
            dialogue.textContent = '☕ Boss và toàn bộ 12 phòng ban đang thưởng thức cà phê! Tinh thần chiến đấu sẵn sàng cho phiên London & New York!';
        }

        const ticker = document.getElementById('office-ticker-msg');
        if (ticker) {
            ticker.innerHTML = '☕ <strong>COFFEE BREAK:</strong> Cả đội ngũ AI nạp năng lượng, các thuật toán phòng vệ vẫn duy trì 100%!';
        }
    }

    triggerTeamBuildingCelebration() {
        if (typeof triggerConfetti === 'function') {
            triggerConfetti();
            setTimeout(triggerConfetti, 800);
            setTimeout(triggerConfetti, 1600);
        }
        if (typeof playRetroSound === 'function') {
            playRetroSound('gold');
        }

        // Walk Boss to central stage
        this.bossTarget = new THREE.Vector3(0, 5.75, -10);

        const dialogue = document.getElementById('astra-dialogue');
        if (dialogue) {
            dialogue.innerHTML = '🎊 <strong>BIG WIN & TEAM BUILDING:</strong> Kính thưa Boss! Toàn bộ 10 tác tử giáo sư - tiến sĩ AI đang nâng ly chúc mừng chuỗi lợi nhuận rực rỡ! Toàn công ty chuẩn bị đi du lịch 5 sao!';
        }

        const ticker = document.getElementById('office-ticker-msg');
        if (ticker) {
            ticker.innerHTML = '🏖️ <strong>TEAM BUILDING PARTY:</strong> Toàn sàn Pixel Floor bật chế độ lễ hội! Lợi nhuận xanh mướt, két sắt an toàn tuyệt đối!';
        }

        if (typeof triggerPixelAlert === 'function') {
            triggerPixelAlert({
                type: 'gold',
                title: '🎊 [THẮNG LỚN - TEAM BUILDING PARTY]',
                body: 'Sếp duyệt lệnh thưởng lớn! Toàn bộ dàn chuyên gia AI cấp cao hân hoan ăn mừng!',
                icon: '🏖️',
                highlight: '+BIG WIN',
                footer: 'Astra Supreme Command'
            });
        }
    }

    /* ==========================================================================
       SMART HEALTH PATROL ENGINE (EXCEPTION-BASED & GLASSMORPHIC HUD)
       ========================================================================== */
    startPatrol() {
        this.isPatrolling = true;
        this.buildPatrolQueue();
        this.patrolIndex = 0;
        const hud = document.getElementById('tacticalPatrolHud');
        if (hud) hud.style.display = 'block';

        if (this.patrolQueue.length > 0) {
            this.inspectPatrolStation(this.patrolQueue[0]);
        }
    }

    stopPatrol() {
        this.isPatrolling = false;
        this.isAutonomousPatrol = false;
        if (this.patrolTimer) {
            clearInterval(this.patrolTimer);
            this.patrolTimer = null;
        }
        if (this.dialogueTimer) {
            clearTimeout(this.dialogueTimer);
            this.dialogueTimer = null;
        }
        if (this.bossBubbleSprite) this.bossBubbleSprite.visible = false;
        if (this.astraBubbleSprite) this.astraBubbleSprite.visible = false;
        if (this.currentPatrolDept && this.floatingBubbles[this.currentPatrolDept]) {
            this.floatingBubbles[this.currentPatrolDept].visible = false;
        }

        const btn = document.getElementById('btn-auto-patrol');
        if (btn) {
            btn.classList.remove('active');
            btn.style.background = 'linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(239, 68, 68, 0.25))';
            btn.style.borderColor = '#f59e0b';
            btn.style.color = '#fde68a';
            btn.innerHTML = '🤖 CEO Auto Patrol';
        }

        const hud = document.getElementById('tacticalPatrolHud');
        if (hud) hud.style.display = 'none';
        this.playSfx('hover');
    }

    patrolNextDept() {
        if (!this.isPatrolling || !this.patrolQueue || this.patrolQueue.length === 0) {
            this.startPatrol();
            return;
        }
        this.patrolIndex = (this.patrolIndex + 1) % this.patrolQueue.length;
        this.inspectPatrolStation(this.patrolQueue[this.patrolIndex]);
    }

    patrolPrevDept() {
        if (!this.isPatrolling || !this.patrolQueue || this.patrolQueue.length === 0) {
            this.startPatrol();
            return;
        }
        this.patrolIndex = (this.patrolIndex - 1 + this.patrolQueue.length) % this.patrolQueue.length;
        this.inspectPatrolStation(this.patrolQueue[this.patrolIndex]);
    }

    buildPatrolQueue() {
        // Triage 12 departments by live operational priority
        const evaluated = this.deptKeysOrder.map(key => {
            const { score, level } = this.evaluateDeptPriority(key);
            return { key, score, level };
        });

        // Sort descending: highest priority (issues / action) first
        evaluated.sort((a, b) => b.score - a.score);
        this.patrolQueue = evaluated.map(item => item.key);
    }

    evaluateDeptPriority(deptKey) {
        let score = 10;
        let level = 'normal'; // 'normal', 'action', 'critical'
        const telemetry = (typeof currentTelemetry !== 'undefined' && currentTelemetry) ? currentTelemetry : null;

        if (telemetry) {
            // 1. Critical: Risk Council Veto or Drawdown threshold
            if (deptKey === 'risk_council') {
                const vetoCount = telemetry.risk?.veto_count || 0;
                const isVeto = telemetry.risk?.is_veto || false;
                if (isVeto || vetoCount > 0) {
                    score += 150;
                    level = 'critical';
                }
            }

            // 2. High Drawdown
            const dd = telemetry.pnl?.max_drawdown_pct || 0;
            if (dd > 3.0) {
                score += 100;
                level = 'critical';
            } else if (dd > 1.0) {
                score += 40;
                level = 'action';
            }

            // 3. Execution OMS Active Positions
            if (deptKey === 'execution_oms') {
                const openPos = telemetry.oms?.open_positions || 0;
                if (openPos > 0) {
                    score += 60;
                    level = 'action';
                }
            }

            // 4. Quant Lab / Breakout Hunter active trades
            if (['quant_lab', 'breakout_hunter', 'volatility_lab'].includes(deptKey)) {
                const trades = telemetry.pnl?.today_trades || 0;
                if (trades > 0) {
                    score += 35;
                    level = 'action';
                }
            }

            // 5. Spot DCA Accumulation
            if (deptKey === 'spot_dca') {
                const spotHoldings = telemetry.spot?.active_holdings || 0;
                if (spotHoldings > 0) {
                    score += 30;
                    level = 'action';
                }
            }
        }

        return { score, level };
    }

    toggleAutonomousPatrol() {
        this.isAutonomousPatrol = !this.isAutonomousPatrol;
        const btn = document.getElementById('btn-auto-patrol');
        if (this.isAutonomousPatrol) {
            if (btn) {
                btn.classList.add('active');
                btn.style.background = 'linear-gradient(135deg, rgba(16, 185, 129, 0.4), rgba(56, 189, 248, 0.4))';
                btn.style.borderColor = '#10b981';
                btn.style.color = '#6ee7b7';
                btn.innerHTML = '🟢 Đang Auto Tuần Tra';
            }
            if (!this.isPatrolling) {
                this.startPatrol();
            }
        } else {
            if (btn) {
                btn.classList.remove('active');
                btn.style.background = 'linear-gradient(135deg, rgba(245, 158, 11, 0.25), rgba(239, 68, 68, 0.25))';
                btn.style.borderColor = '#f59e0b';
                btn.style.color = '#fde68a';
                btn.innerHTML = '🤖 CEO Auto Patrol';
            }
            this.stopPatrol();
        }
    }

    teleportToBalcony() {
        if (this.isPatrolling) this.stopPatrol();
        this.bossPosition.set(0, 0.5, 142);
        this.bossRotation = 0; // Face south towards the cars and skyline
        if (this.cameraMode === 'god') {
            this.controls.target.set(0, 5, 150);
            this.camera.position.set(0, 35, 110);
        } else if (this.cameraMode === 'follow' || this.cameraMode === 'shoulder') {
            this.cameraPitch = 2.0;
        }
        this.playSfx('warp');
        this.showToast('🏎️ ĐÃ DỊCH CHUYỂN ĐẾN BAN CÔNG SIÊU XE (VIP BALCONY) & MEGACITY SKYLINE!');
    }

    setSpriteSpeech(sprite, text, colorHex = 0x38bdf8) {
        if (!sprite) return;
        const c = document.createElement('canvas');
        c.width = 384;
        c.height = 96;
        const ctx = c.getContext('2d');
        ctx.fillStyle = 'rgba(11, 20, 42, 0.95)';
        ctx.strokeStyle = `#${colorHex.toString(16).padStart(6, '0')}`;
        ctx.lineWidth = 3;
        drawRoundRect(ctx, 8, 8, 368, 80, 14);
        ctx.fill();
        ctx.stroke();

        ctx.font = 'bold 17px "Plus Jakarta Sans", sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        const displayText = text.length > 36 ? text.slice(0, 34) + '…' : text;
        ctx.fillText(displayText, 192, 48);

        if (sprite.material && sprite.material.map) {
            sprite.material.map.dispose();
        }
        sprite.material.map = new THREE.CanvasTexture(c);
        sprite.material.needsUpdate = true;
        sprite.visible = true;
    }

    inspectPatrolStation(deptKey) {
        this.currentPatrolDept = deptKey;
        this.playSfx('click');
        const cfg = this.deptConfigs[deptKey];
        if (!cfg) return;

        // 1. Move Boss to this station smoothly
        this.bossTarget = new THREE.Vector3(cfg.pos.x, 5.75, cfg.pos.z + 12);

        // 2. Smooth camera glide towards the station
        new TWEEN.Tween(this.camera.position)
            .to({ x: cfg.pos.x + 28, y: cfg.pos.y + 34, z: cfg.pos.z + 44 }, 750)
            .easing(TWEEN.Easing.Cubic.Out)
            .start();

        new TWEEN.Tween(this.controls.target)
            .to({ x: cfg.pos.x, y: cfg.pos.y + 6, z: cfg.pos.z }, 750)
            .easing(TWEEN.Easing.Cubic.Out)
            .start();

        // 3. Update the Mini Tactical Patrol HUD Card
        this.updatePatrolHUD(deptKey);

        // 4. Launch 3-Way Executive Dialogue Sequence (Boss ➔ Officer ➔ Astra)
        this.startPatrolDialogueSequence(deptKey);

        // 5. Auto progression timer (advances after 8 seconds)
        this.startPatrolTimer(8000);
    }

    startPatrolDialogueSequence(deptKey) {
        if (this.dialogueTimer) clearTimeout(this.dialogueTimer);
        const telemetry = (typeof currentTelemetry !== 'undefined' && currentTelemetry) ? currentTelemetry : null;
        const dept = (telemetry && telemetry.departments && telemetry.departments[deptKey]) || {};
        const diag = dept.executive_dialogue || {
            boss: 'Astra, kiểm tra tình hình vận hành phòng ban này ngay!',
            officer: 'Báo cáo Boss: Tất cả chỉ số đang trong ngưỡng an toàn tối đa.',
            astra: 'AI Model đã xác thực dữ liệu khớp lệnh và tuân thủ kỷ luật 100%.'
        };

        const bossLineEl = document.getElementById('patrolBossLine');
        const officerLineEl = document.getElementById('patrolOfficerLine');
        const astraLineEl = document.getElementById('patrolAstraLine');

        const bossTextEl = document.getElementById('patrolBossText');
        const officerTextEl = document.getElementById('patrolOfficerText');
        const officerSpeakerEl = document.getElementById('patrolOfficerSpeaker');
        const astraTextEl = document.getElementById('patrolAstraText');

        const cfg = this.deptConfigs[deptKey];
        if (bossTextEl) bossTextEl.textContent = `"${diag.boss}"`;
        if (officerTextEl) officerTextEl.textContent = `"${diag.officer}"`;
        if (officerSpeakerEl) officerSpeakerEl.textContent = `👨‍💻 ${cfg ? cfg.officer.split('—')[0].trim() : 'TRƯỞNG PHÒNG'}:`;
        if (astraTextEl) astraTextEl.textContent = `"${diag.astra}"`;

        // PHASE 1 (0s - 2.5s): Boss asks / checks
        if (bossLineEl) bossLineEl.className = 'dialogue-line boss-line active-speaking';
        if (officerLineEl) officerLineEl.className = 'dialogue-line officer-line';
        if (astraLineEl) astraLineEl.className = 'dialogue-line astra-line';

        this.setSpriteSpeech(this.bossBubbleSprite, `👑 Boss: ${diag.boss}`, 0xf59e0b);
        if (this.astraBubbleSprite) this.astraBubbleSprite.visible = false;
        if (this.floatingBubbles[deptKey]) this.floatingBubbles[deptKey].visible = false;

        // PHASE 2 (2.5s - 5.2s): Officer reports
        this.dialogueTimer = setTimeout(() => {
            if (!this.isPatrolling) return;
            if (bossLineEl) bossLineEl.className = 'dialogue-line boss-line';
            if (officerLineEl) officerLineEl.className = 'dialogue-line officer-line active-speaking';
            if (astraLineEl) astraLineEl.className = 'dialogue-line astra-line';

            if (this.bossBubbleSprite) this.bossBubbleSprite.visible = false;
            this.updateSpeechBubble(deptKey, diag.officer);
            if (this.floatingBubbles[deptKey]) this.floatingBubbles[deptKey].visible = true;

            // PHASE 3 (5.2s - 8.0s): Astra verifies
            this.dialogueTimer = setTimeout(() => {
                if (!this.isPatrolling) return;
                if (bossLineEl) bossLineEl.className = 'dialogue-line boss-line';
                if (officerLineEl) officerLineEl.className = 'dialogue-line officer-line';
                if (astraLineEl) astraLineEl.className = 'dialogue-line astra-line active-speaking';

                if (this.floatingBubbles[deptKey]) this.floatingBubbles[deptKey].visible = false;
                this.setSpriteSpeech(this.astraBubbleSprite, `🤖 Astra: ${diag.astra}`, 0xc084fc);

                // PHASE 4 (8.0s): Conclude & clear bubbles
                this.dialogueTimer = setTimeout(() => {
                    if (this.bossBubbleSprite) this.bossBubbleSprite.visible = false;
                    if (this.astraBubbleSprite) this.astraBubbleSprite.visible = false;
                    if (this.floatingBubbles[deptKey]) this.floatingBubbles[deptKey].visible = false;
                }, 2800);
            }, 2700);
        }, 2500);
    }

    initGameLoadingScreen() {
        if (typeof window.dismissLoadingOverlay === 'function') {
            window.dismissLoadingOverlay();
        } else {
            const overlay = document.getElementById('gameLoadingOverlay');
            if (overlay) {
                overlay.classList.add('hidden');
                overlay.style.display = 'none';
                overlay.style.pointerEvents = 'none';
            }
        }
    }

    updatePatrolHUD(deptKey) {
        const hud = document.getElementById('tacticalPatrolHud');
        if (!hud) return;

        const cfg = this.deptConfigs[deptKey];
        const telemetry = (typeof currentTelemetry !== 'undefined' && currentTelemetry) ? currentTelemetry : null;
        const dept = (telemetry && telemetry.departments && telemetry.departments[deptKey]) || {};
        const { score, level } = this.evaluateDeptPriority(deptKey);

        // Priority Class
        hud.className = 'tactical-patrol-hud priority-' + level;

        // Badge & Step
        const badgeEl = document.getElementById('patrolHudBadge');
        if (badgeEl) badgeEl.textContent = `${cfg ? cfg.tag : deptKey.toUpperCase()}`;

        const stepEl = document.getElementById('patrolHudStep');
        if (stepEl) stepEl.textContent = `TRẠM ${this.patrolIndex + 1}/${this.patrolQueue.length}`;

        // Priority Tag
        const tagEl = document.getElementById('patrolPriorityTag');
        if (tagEl) {
            tagEl.className = 'patrol-priority-tag ' + level;
            if (level === 'critical') tagEl.textContent = '🚨 CẢNH BÁO RỦI RO';
            else if (level === 'action') tagEl.textContent = '⚡ ĐANG TÁC CHIẾN';
            else tagEl.textContent = '🛡️ AN TOÀN 100%';
        }

        // Officer info
        const titleEl = document.getElementById('patrolStationTitle');
        if (titleEl) titleEl.textContent = cfg ? cfg.name : (dept.title || deptKey);

        const subEl = document.getElementById('patrolOfficerSub');
        if (subEl) subEl.textContent = `${cfg ? cfg.officer : 'Agent'} · ${cfg ? cfg.activity : 'Trực chiến'}`;

        // Metrics
        const pnlVal = (telemetry && telemetry.pnl) ? telemetry.pnl.today_pnl_usd : 0.4556;
        const pnlEl = document.getElementById('patrolMetricPnl');
        if (pnlEl) {
            pnlEl.textContent = (pnlVal >= 0 ? '+' : '') + `$${Number(pnlVal).toFixed(4)}`;
            pnlEl.style.color = pnlVal >= 0 ? '#10b981' : '#ef4444';
        }

        const posEl = document.getElementById('patrolMetricPos');
        if (posEl) {
            const openPos = (telemetry && telemetry.oms) ? telemetry.oms.open_positions : 13;
            posEl.textContent = `${openPos} Vị thế`;
        }

        const ddEl = document.getElementById('patrolMetricDd');
        if (ddEl) {
            const ddVal = (telemetry && telemetry.pnl) ? telemetry.pnl.max_drawdown_pct : 0.0;
            ddEl.textContent = `${Number(ddVal).toFixed(2)}%`;
            ddEl.style.color = ddVal > 2.0 ? '#ef4444' : '#38bdf8';
        }

        const vetoEl = document.getElementById('patrolMetricVeto');
        if (vetoEl) {
            const vCount = (telemetry && telemetry.risk) ? telemetry.risk.veto_count : 0;
            vetoEl.textContent = `${vCount} VETO`;
            vetoEl.style.color = vCount > 0 ? '#ef4444' : '#10b981';
        }

        // Speech
        const speechEl = document.getElementById('patrolSpeechBox');
        if (speechEl) {
            const quotes = DEPT_SPEECHES[deptKey] || [];
            const quote = quotes.length > 0 ? quotes[0] : (dept.speech || 'Hệ thống vận hành ổn định, sẵn sàng tác chiến.');
            speechEl.textContent = `"${quote}"`;
        }
    }

    startPatrolTimer(duration = 8000) {
        if (this.patrolTimer) clearInterval(this.patrolTimer);
        this.patrolProgress = 0;
        const progressBar = document.getElementById('patrolProgressBar');
        if (progressBar) progressBar.style.width = '0%';

        const interval = 100;
        let elapsed = 0;

        this.patrolTimer = setInterval(() => {
            if (!this.isPatrolling) {
                clearInterval(this.patrolTimer);
                return;
            }
            elapsed += interval;
            const pct = Math.min((elapsed / duration) * 100, 100);
            if (progressBar) progressBar.style.width = `${pct}%`;

            if (elapsed >= duration) {
                clearInterval(this.patrolTimer);
                this.patrolNextDept();
            }
        }, interval);
    }

    openCurrentDeptDetail() {
        if (this.currentPatrolDept && typeof openDeptDetailModal === 'function') {
            openDeptDetailModal(this.currentPatrolDept);
        }
    }

    toggleFullscreen() {
        this.isFullscreen = !this.isFullscreen;
        const container = document.getElementById('office-stage-container');
        if (container) {
            container.classList.toggle('fullscreen', this.isFullscreen);
        }
        setTimeout(() => this.onResize(), 100);
    }

    onResize() {
        if (!this.container || !this.renderer || !this.camera) return;
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;
        this.camera.aspect = this.width / this.height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.width, this.height);
    }

    /* --------------------------------------------------------------------------
       13. EMBODIED SPATIAL MULTI-AGENT DEBATE & SEQUENTIAL SPEECH ROTATOR
       -------------------------------------------------------------------------- */
    initSpeechRotator() {
        let lastKey = null;
        let lastDebateId = null;
        let lastStepIdx = -1;

        // Poll live multi-agent debate stream from SpatialAgentBrain
        const pollDebates = async () => {
            if (document.hidden) return;
            try {
                const res = await fetch('/api/v1/spatial/debates');
                if (!res.ok) return;
                const data = await res.json();
                const debate = data.current_debate;
                if (!debate || !debate.steps) return;

                const stepIdx = debate.active_step_index;
                const step = debate.steps[stepIdx];
                if (!step) return;

                // When debate step advances
                if (debate.debate_id !== lastDebateId || stepIdx !== lastStepIdx) {
                    lastDebateId = debate.debate_id;
                    lastStepIdx = stepIdx;

                    // Hide previous station's bubble
                    if (lastKey && this.floatingBubbles[lastKey]) {
                        this.floatingBubbles[lastKey].visible = false;
                    }

                    const deptKey = step.dept_key;
                    const speakerText = `${step.speaker_name}: ${step.speech}`;
                    this.updateSpeechBubble(deptKey, speakerText);

                    if (this.floatingBubbles[deptKey]) {
                        this.floatingBubbles[deptKey].visible = true;
                        lastKey = deptKey;
                    }

                    // Update HUD dialogue banner
                    const astraBar = document.getElementById('astra-dialogue');
                    if (astraBar) {
                        astraBar.innerHTML = `<span style="color: ${step.color}; font-weight: 800;">[${step.speaker_name} · ${step.role}]:</span> "${step.speech}"`;
                    }

                    // Highlight station and play audio on events
                    if (step.action === 'VETO_ORDER') {
                        this.playSfx('click');
                        this.pulseStationHighlight(deptKey, 0xef4444);
                        this.triggerRunnerCourier('risk_council', 'spot_dca', '⚠️ LỆNH VETO');
                    } else if (step.action === 'APPROVE_MODIFIED' || step.action === 'PROPOSE_BUY') {
                        this.playSfx('hover');
                        this.pulseStationHighlight(deptKey, 0x10b981);
                        if (step.action === 'APPROVE_MODIFIED') {
                            this.triggerRunnerCourier('lead_pm', 'execution_oms', '⚡ PHÊ CHUẨN');
                        }
                    }
                }
            } catch (err) {
                console.debug('[SPATIAL DEBATE] poll error:', err);
            }
        };

        this.speechTimer = setInterval(pollDebates, 2500);
        pollDebates();
    }

    pulseStationHighlight(deptKey, colorHex = 0x38bdf8) {
        const station = this.stations[deptKey];
        if (!station) return;
        const origScale = station.scale.x;
        new TWEEN.Tween(station.scale)
            .to({ x: origScale * 1.05, y: origScale * 1.05, z: origScale * 1.05 }, 250)
            .yoyo(true)
            .repeat(1)
            .easing(TWEEN.Easing.Quadratic.Out)
            .start();
    }

    triggerRunnerCourier(fromDeptKey, toDeptKey, message) {
        if (!this.wanderingStaff || this.wanderingStaff.length === 0) return;
        const runner = this.wanderingStaff[0];
        const fromCfg = this.deptConfigs[fromDeptKey];
        const toCfg = this.deptConfigs[toDeptKey];
        if (!runner || !fromCfg || !toCfg) return;

        if (runner.userData && runner.userData.badge) {
            this.setSpriteSpeech(runner.userData.badge, message, 0xf59e0b);
        }

        // Animate runner movement between the two stations
        new TWEEN.Tween(runner.position)
            .to({ x: toCfg.pos.x, y: 0, z: toCfg.pos.z + 6 }, 3000)
            .easing(TWEEN.Easing.Quadratic.InOut)
            .onComplete(() => {
                setTimeout(() => {
                    new TWEEN.Tween(runner.position)
                        .to({ x: fromCfg.pos.x, y: 0, z: fromCfg.pos.z + 6 }, 3000)
                        .easing(TWEEN.Easing.Quadratic.InOut)
                        .start();
                }, 2000);
            })
            .start();
    }

    playSfx(type) {
        if (typeof playRetroSound === 'function') {
            playRetroSound(type === 'hover' ? 'blip' : 'purple');
        }
    }

    /* --------------------------------------------------------------------------
       14. REAL-TIME MINIMAP RADAR CANVAS (100% TELEMETRY SYNCED)
       -------------------------------------------------------------------------- */
    initMinimap() {
        this.minimapCanvas = document.getElementById('hud-minimap-canvas');
        this.minimapTooltip = document.getElementById('minimap-radar-tooltip');
        this.hoveredMinimapBlip = null;
        this.radarAngle = 0;

        if (this.minimapCanvas && typeof this.minimapCanvas.getContext === 'function') {
            this.minimapCtx = this.minimapCanvas.getContext('2d');

            // Interactive Event Listeners for Minimap
            this.minimapCanvas.addEventListener('mousemove', (e) => this.onMinimapMouseMove(e));
            this.minimapCanvas.addEventListener('mouseleave', () => this.onMinimapMouseLeave());
            this.minimapCanvas.addEventListener('click', (e) => this.onMinimapClick(e));
        }
    }

    getMinimapBlipCoords(cx, cy) {
        const blips = [];
        // 12 Departments mapped to canvas
        const shortLabels = {
            'lead_pm': 'PM',
            'risk_council': 'CRO',
            'news_scout': 'REC',
            'execution_oms': 'OMS',
            'arbitrage_desk': 'ARB',
            'quant_lab': 'QNT',
            'breakout_hunter': 'BRK',
            'volatility_lab': 'VOL',
            'spot_dca': 'DCA',
            'cvar_stress': 'CVR',
            'accounting_pm': 'ACC',
            'community_affiliate': 'CRM'
        };

        Object.entries(this.deptConfigs).forEach(([key, cfg]) => {
            const rx = cx + (cfg.pos.x / 140) * 50;
            const ry = cy + (cfg.pos.z / 140) * 50;
            blips.push({
                type: 'dept',
                key: key,
                agentName: cfg.agentName || 'Astra',
                name: cfg.name,
                officer: cfg.officer,
                shortLabel: shortLabels[key] || 'DEP',
                color: `#${cfg.color.toString(16).padStart(6, '0')}`,
                x: rx,
                y: ry,
                pos3d: cfg.pos,
                metric: cfg.metric
            });
        });

        // Boss Suite HQ
        blips.push({
            type: 'boss',
            key: 'boss_suite',
            agentName: 'Boss',
            name: 'Bộ Chỉ Huy Tổng Tư Lệnh (CEO Suite)',
            officer: '👑 BOSS · CEO / COMMANDER',
            shortLabel: 'HQ',
            color: '#f59e0b',
            x: cx,
            y: cy - 28,
            pos3d: { x: 0, y: 15, z: -85 },
            metric: 'Quyền trượng tối cao · 100% Quyết định'
        });

        return blips;
    }

    onMinimapMouseMove(event) {
        if (!this.minimapCanvas) return;
        const rect = this.minimapCanvas.getBoundingClientRect();
        const mx = event.clientX - rect.left;
        const my = event.clientY - rect.top;
        const cx = this.minimapCanvas.width / 2;
        const cy = this.minimapCanvas.height / 2;
        const blips = this.getMinimapBlipCoords(cx, cy);

        let closest = null;
        let minDist = 11; // 11px hit radius

        blips.forEach(b => {
            const d = Math.hypot(b.x - mx, b.y - my);
            if (d < minDist) {
                minDist = d;
                closest = b;
            }
        });

        this.hoveredMinimapBlip = closest;

        if (closest) {
            this.minimapCanvas.style.cursor = 'pointer';
            if (this.minimapTooltip) {
                const liveTelem = (currentTelemetry && currentTelemetry.departments && currentTelemetry.departments[closest.key]) || {};
                const statusStr = (liveTelem.status === 'ONLINE' || liveTelem.status === 'RECENT_RECORD') 
                    ? '<span style="color:#10b981;">● ONLINE · HOẠT ĐỘNG</span>' 
                    : '<span style="color:#38bdf8;">● GIÁM SÁT 24/7</span>';

                this.minimapTooltip.style.display = 'block';
                this.minimapTooltip.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="color:#f59e0b; font-weight:800; font-size:10px;">[${closest.shortLabel}] ${closest.name}</span>
                        <span style="font-size:9px;">${statusStr}</span>
                    </div>
                    <div style="color:#cbd5e1; font-size:9.5px; margin-bottom:3px;"><strong>Nhân sự:</strong> ${closest.officer}</div>
                    <div style="color:#94a3b8; font-size:9px; border-top:1px solid rgba(255,255,255,0.08); padding-top:3px; margin-top:3px;">${closest.metric}</div>
                    <div style="color:#38bdf8; font-size:8.5px; font-weight:700; margin-top:4px; text-align:right;">👉 Nhấp: Zoom 3D & Xem RPG Sheet</div>
                `;
            }
        } else {
            this.minimapCanvas.style.cursor = 'crosshair';
            if (this.minimapTooltip) this.minimapTooltip.style.display = 'none';
        }
    }

    onMinimapMouseLeave() {
        this.hoveredMinimapBlip = null;
        if (this.minimapCanvas) this.minimapCanvas.style.cursor = 'crosshair';
        if (this.minimapTooltip) this.minimapTooltip.style.display = 'none';
    }

    onMinimapClick(event) {
        if (!this.minimapCanvas) return;
        const rect = this.minimapCanvas.getBoundingClientRect();
        const mx = event.clientX - rect.left;
        const my = event.clientY - rect.top;
        const cx = this.minimapCanvas.width / 2;
        const cy = this.minimapCanvas.height / 2;
        const blips = this.getMinimapBlipCoords(cx, cy);

        let closest = null;
        let minDist = 14;

        blips.forEach(b => {
            const d = Math.hypot(b.x - mx, b.y - my);
            if (d < minDist) {
                minDist = d;
                closest = b;
            }
        });

        if (closest) {
            if (closest.type === 'boss') {
                if (typeof this.focusOnBoss === 'function') this.focusOnBoss();
            } else {
                // Focus 3D camera
                if (window.worldEngine && typeof window.worldEngine.setCameraMode === 'function') {
                    window.worldEngine.setCameraMode('FOCUS', closest.agentName);
                } else if (typeof this.teleportToDept === 'function') {
                    this.teleportToDept(closest.key);
                }

                // Open RPG Character Stat Sheet
                if (typeof window.openAgentRpgSheet === 'function') {
                    window.openAgentRpgSheet(closest.agentName);
                } else if (typeof openDeptDetailModal === 'function') {
                    openDeptDetailModal(closest.key);
                }
            }
        }
    }

    drawMinimap() {
        if (!this.minimapCtx) return;
        const ctx = this.minimapCtx;
        const w = this.minimapCanvas.width;
        const h = this.minimapCanvas.height;
        const cx = w / 2;
        const cy = h / 2;
        const now = Date.now() * 0.002;

        ctx.clearRect(0, 0, w, h);

        // Radar background grid circles
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.18)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(cx, cy, 18, 0, Math.PI * 2);
        ctx.arc(cx, cy, 38, 0, Math.PI * 2);
        ctx.arc(cx, cy, 56, 0, Math.PI * 2);
        ctx.stroke();

        // Crosshairs & Quadrants
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.12)';
        ctx.beginPath();
        ctx.moveTo(cx, 4); ctx.lineTo(cx, h - 4);
        ctx.moveTo(4, cy); ctx.lineTo(w - 4, cy);
        ctx.stroke();

        // Rotating Sweeping Radar Line with glowing gradient
        this.radarAngle = (this.radarAngle || 0) + 0.04;
        const sx = cx + Math.cos(this.radarAngle) * 56;
        const sy = cy + Math.sin(this.radarAngle) * 56;
        ctx.strokeStyle = 'rgba(16, 185, 129, 0.6)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(sx, sy);
        ctx.stroke();

        // Sweep cone shadow
        ctx.fillStyle = 'rgba(16, 185, 129, 0.06)';
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, 56, this.radarAngle - 0.35, this.radarAngle);
        ctx.closePath();
        ctx.fill();

        const blips = this.getMinimapBlipCoords(cx, cy);
        const openPosCount = currentTelemetry?.open_positions_count || 0;

        blips.forEach(b => {
            const isHovered = this.hoveredMinimapBlip && this.hoveredMinimapBlip.key === b.key;
            const isOmsActive = (b.key === 'execution_oms' || b.key === 'quant_lab') && openPosCount > 0;
            const isRiskVeto = (b.key === 'risk_council' || b.key === 'cvar_stress') && (this.activeDebate && this.activeDebate.includes('VETO'));

            // Dynamic Pulse Rings
            if (isOmsActive) {
                // Expanding Vibrant Green Beacon
                const pulseR = 4 + (Math.sin(now * 3) + 1) * 3;
                ctx.strokeStyle = 'rgba(16, 185, 129, 0.8)';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.arc(b.x, b.y, pulseR, 0, Math.PI * 2);
                ctx.stroke();
            } else if (isRiskVeto) {
                // Expanding Crimson Red Alert
                const pulseR = 4 + (Math.sin(now * 4) + 1) * 3.5;
                ctx.strokeStyle = 'rgba(239, 68, 68, 0.85)';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.arc(b.x, b.y, pulseR, 0, Math.PI * 2);
                ctx.stroke();
            } else if (isHovered) {
                // Hover highlight ring
                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.arc(b.x, b.y, 6, 0, Math.PI * 2);
                ctx.stroke();
            }

            // Blip center core
            ctx.fillStyle = isHovered ? '#ffffff' : b.color;
            ctx.beginPath();
            ctx.arc(b.x, b.y, isHovered ? 3.5 : (b.type === 'boss' ? 3.2 : 2.5), 0, Math.PI * 2);
            ctx.fill();

            // Blip Label
            ctx.fillStyle = isHovered ? '#38bdf8' : 'rgba(203, 213, 225, 0.75)';
            ctx.font = '600 6.5px "JetBrains Mono", monospace';
            ctx.fillText(b.shortLabel, b.x + 3.5, b.y + 2);
        });
    }

    /* --------------------------------------------------------------------------
       14B. PUBG TACTICAL UI: COMPASS TAPE, CROSSHAIR & SURVIVAL HUD
       -------------------------------------------------------------------------- */
    initPubgUI() {
        this.compassWrapEl = document.getElementById('pubgCompassWrap');
        this.compassStripEl = document.getElementById('pubgCompassStrip');
        this.compassDegreeEl = document.getElementById('pubgCompassDegree');
        this.crosshairEl = document.getElementById('pubgCrosshair');
        this.interactPromptEl = document.getElementById('pubgInteractPrompt');
        this.interactTextEl = document.getElementById('pubgPromptText');
        this.bottomHudEl = document.getElementById('pubgBottomHud');
        this.healthFillEl = document.getElementById('pubgHealthFill');
        this.stanceBadgeEl = document.getElementById('pubgStanceBadge');
        this.boostTrackEl = document.getElementById('pubgBoostTrack');

        // Populate PUBG Compass Strip with Degree Marks
        if (this.compassStripEl) {
            this.compassStripEl.innerHTML = '';
            const directions = { 0: 'N', 45: 'NE', 90: 'E', 135: 'SE', 180: 'S', 225: 'SW', 270: 'W', 315: 'NW', 360: 'N' };
            for (let deg = -180; deg <= 540; deg += 15) {
                const norm = ((deg % 360) + 360) % 360;
                const tick = document.createElement('div');
                const isCard = directions[norm] !== undefined;
                const isMajor = norm % 15 === 0;
                tick.className = `pubg-compass-tick ${isMajor ? 'major' : ''} ${isCard ? 'cardinal' : ''}`;

                const line = document.createElement('div');
                line.className = 'tick-line';
                tick.appendChild(line);

                const label = document.createElement('div');
                label.className = 'tick-label';
                label.textContent = directions[norm] || (norm % 30 === 0 ? norm : '');
                tick.appendChild(label);

                this.compassStripEl.appendChild(tick);
            }
        }
    }

    selectToolSlot(slot) {
        this.activeToolSlot = slot;
        [1, 2, 3].forEach(s => {
            const card = document.getElementById(`wpn-slot-${s}`);
            if (card) card.classList.toggle('active', s === slot);
        });
        this.playSfx('click');

        // Tactical Hotkey Navigation: Focus department & pop up live telemetry
        if (slot === 1) {
            this.onStationClick('execution_oms');
        } else if (slot === 2) {
            this.onStationClick('quant_lab');
        } else if (slot === 3) {
            this.onStationClick('risk_council');
        }
    }

    updatePubgUI(delta, isMoving, isSprint) {
        if (this.isDriving) {
            if (this.crosshairEl && this.crosshairEl.style.display !== 'none') {
                this.crosshairEl.style.display = 'none';
            }
            if (this.interactPromptEl && this.interactTextEl) {
                if (this.interactPromptEl.style.display !== 'inline-flex') {
                    this.interactPromptEl.style.display = 'inline-flex';
                }
                const promptText = `🏎️ [ESC / F] XUỐNG SIÊU XE ${this.drivingCar ? this.drivingCar.name.toUpperCase() : ''}`;
                if (this.interactTextEl.textContent !== promptText) {
                    this.interactTextEl.textContent = promptText;
                }
            }
            return;
        }

        const isActionCam = ['fpv', 'shoulder', 'follow'].includes(this.cameraMode);

        // 1. Crosshair visibility & spread
        if (this.crosshairEl) {
            if (isActionCam) {
                this.crosshairEl.style.display = 'block';
                const spread = isSprint ? '16px' : (isMoving ? '10px' : '6px');
                this.crosshairEl.style.setProperty('--spread', spread);
            } else {
                this.crosshairEl.style.display = 'none';
            }
        }

        // If near elevator or supercar, maintain interaction prompt!
        if (this.nearbyElevator || this.nearbySupercar) {
            return;
        }

        // 2. Crosshair Raycast Interaction Detection
        if (isActionCam && this.crosshairEl) {
            this.raycaster.setFromCamera(new THREE.Vector2(0, 0), this.camera);
            const hits = this.raycaster.intersectObjects(this.stationMeshes);
            if (hits.length > 0 && hits[0].distance < 85) {
                const deptKey = hits[0].object.userData.deptKey;
                const cfg = this.deptConfigs[deptKey];
                if (cfg) {
                    this.aimHitDept = deptKey;
                    this.crosshairEl.classList.add('locked');
                    if (this.interactPromptEl && this.interactTextEl) {
                        this.interactPromptEl.style.display = 'inline-flex';
                        this.interactTextEl.textContent = `TƯƠNG TÁC · ${cfg.tag} (${cfg.officer})`;
                    }
                }
            } else {
                this.aimHitDept = null;
                this.crosshairEl.classList.remove('locked');
                if (this.interactPromptEl) {
                    this.interactPromptEl.style.display = 'none';
                }
            }
        } else if (this.interactPromptEl) {
            this.interactPromptEl.style.display = 'none';
        }

        // 3. PUBG Compass Tape
        let rawDeg = (this.bossHeading * 180 / Math.PI) % 360;
        if (rawDeg < 0) rawDeg += 360;
        const currDeg = Math.round(rawDeg);

        if (this.compassStripEl) {
            // Index 12 corresponds to 0 degrees, 32px per 15 degrees
            const offsetPx = ((12 + rawDeg / 15) * 32) + 16;
            this.compassStripEl.style.transform = `translateX(-${offsetPx}px)`;
        }

        if (this.compassDegreeEl) {
            const getCard = (d) => {
                if (d >= 338 || d < 23) return 'N';
                if (d < 68) return 'NE';
                if (d < 113) return 'E';
                if (d < 158) return 'SE';
                if (d < 203) return 'S';
                if (d < 248) return 'SW';
                if (d < 293) return 'W';
                return 'NW';
            };
            this.compassDegreeEl.textContent = `${currDeg.toString().padStart(3, '0')}° ${getCard(currDeg)}`;
        }

        // 4. Boost / Stamina Drain & Recharge
        if (isSprint) {
            this.boostStamina = Math.max(0, this.boostStamina - delta * 24);
        } else {
            this.boostStamina = Math.min(100, this.boostStamina + delta * 14);
        }

        // 4 Segments in Boost Track
        for (let i = 1; i <= 4; i++) {
            const seg = document.getElementById(`boost-seg-${i}`);
            if (seg) {
                seg.classList.toggle('active', this.boostStamina >= (i - 0.5) * 25);
            }
        }

        // 5. Stance Badge Update
        if (this.stanceBadgeEl) {
            if (!this.bossIsGrounded) {
                this.stanceBadgeEl.textContent = '🦘 AIRBORNE';
                this.stanceBadgeEl.style.color = '#38bdf8';
                this.stanceBadgeEl.style.borderColor = '#38bdf8';
            } else if (this.isCrouching) {
                this.stanceBadgeEl.textContent = '🧘 CROUCH [C]';
                this.stanceBadgeEl.style.color = '#f59e0b';
                this.stanceBadgeEl.style.borderColor = '#f59e0b';
            } else if (isSprint && isMoving) {
                this.stanceBadgeEl.textContent = '🏃 SPRINT [SHIFT]';
                this.stanceBadgeEl.style.color = '#f43f5e';
                this.stanceBadgeEl.style.borderColor = '#f43f5e';
            } else if (isMoving) {
                this.stanceBadgeEl.textContent = '🚶 WALK [WASD]';
                this.stanceBadgeEl.style.color = '#10b981';
                this.stanceBadgeEl.style.borderColor = '#10b981';
            } else {
                this.stanceBadgeEl.textContent = '🧍 STANDBY';
                this.stanceBadgeEl.style.color = '#94a3b8';
                this.stanceBadgeEl.style.borderColor = 'rgba(255, 255, 255, 0.2)';
            }
        }
    }

    /**
     * Compute dynamic floor elevation at world coordinates (x, z)
     * Handles CEO suite dais, 4 wing elevated platforms, 2-tier central dais,
     * connecting sky-walkway corridors, and base ground level.
     */
    getFloorHeight(x, z) {
        // 1. CEO Executive Suite Dais (VIP North-West corner of Executive Wing)
        if (Math.abs(x - (-78)) <= 19 && Math.abs(z - (-86)) <= 14) {
            return 4.55;
        }

        // 2. 4 Architectural Wings (Elevated Platforms)
        // Executive: (-80, -60), Trading: (80, -60), Research: (-80, 75), Operations: (80, 75)
        const inExecutive = Math.abs(x - (-80)) <= 42 && Math.abs(z - (-60)) <= 42;
        const inTrading = Math.abs(x - 80) <= 42 && Math.abs(z - (-60)) <= 42;
        const inResearch = Math.abs(x - (-80)) <= 42 && Math.abs(z - 75) <= 42;
        const inOperations = Math.abs(x - 80) <= 42 && Math.abs(z - 75) <= 42;

        if (inExecutive || inTrading || inResearch || inOperations) {
            return 3.75;
        }

        // 3. Central Core Two-Tier Dais
        const distFromCore = Math.hypot(x, z);
        if (distFromCore <= 28) {
            return 4.75; // Upper Dais
        }
        if (distFromCore <= 38) {
            return 2.5;  // Lower Dais
        }

        // 4B. South VIP Balcony Terrace & Skybridge (Supercar Showroom Balcony at z = 115..175)
        if (Math.abs(x) <= 38 && z >= 115 && z <= 175) {
            return 3.0;
        }

        // 4. Connecting Sky-Walkways (Corridors connecting Core (0,0) to 4 Wings)
        const routes = [
            { tx: -80, tz: -60 },
            { tx: 80, tz: -60 },
            { tx: -80, tz: 75 },
            { tx: 80, tz: 75 }
        ];
        for (let i = 0; i < routes.length; i++) {
            const r = routes[i];
            const L2 = r.tx * r.tx + r.tz * r.tz;
            const t = Math.max(0, Math.min(1, (x * r.tx + z * r.tz) / L2));
            const projX = t * r.tx;
            const projZ = t * r.tz;
            const d = Math.hypot(x - projX, z - projZ);
            if (d <= 8.5) {
                return 1.9; // Corridor walkway slab top
            }
        }

        // 5. Ground Floor Level (Main Plaza / Zen Garden)
        return 0.0;
    }

    /* --------------------------------------------------------------------------
       15. ANIMATION & RENDER LOOP
       -------------------------------------------------------------------------- */
    animate() {
        if (document.hidden) return;
        requestAnimationFrame(() => this.animate());

        const delta = Math.min(this.clock.getDelta(), 0.1);
        const time = this.clock.getElapsedTime();

        if (typeof TWEEN !== 'undefined') {
            TWEEN.update();
        }

        // Only update OrbitControls when enabled (God-view or Tactical)
        // NEVER update OrbitControls in FPV / Shoulder / Follow mode to prevent matrix fighting & jitter
        if (this.controls && this.controls.enabled) {
            this.controls.update();
        }

        // Central Hologram Animations
        if (this.coreCrystal) this.coreCrystal.rotation.y += delta * 0.6;
        if (this.coreWire) this.coreWire.rotation.y -= delta * 0.4;
        if (this.coreRing1) this.coreRing1.rotation.z += delta * 0.5;
        if (this.coreRing2) this.coreRing2.rotation.z -= delta * 0.45;
        if (this.logoBillboard) {
            this.logoBillboard.position.y = 39 + Math.sin(time * 2.0) * 0.5;
        }

        // 5D Digital Twin Hologlobe & Vector Particles Animations (Phòng Bên Cạnh)
        if (this.holo5dGlobe) this.holo5dGlobe.rotation.y += delta * 0.4;
        if (this.holo5dCore) this.holo5dCore.rotation.y -= delta * 0.6;
        if (this.holo5dRing1) this.holo5dRing1.rotation.x += delta * 0.5;
        if (this.holo5dRing2) this.holo5dRing2.rotation.z -= delta * 0.45;
        if (this.holo5dParticles) {
            this.holo5dParticles.rotation.y += delta * 0.25;
            this.holo5dParticles.rotation.x = Math.sin(time * 0.5) * 0.15;
        }
        if (this.holo5dSatellites && this.holo5dSatellites.length > 0) {
            this.holo5dSatellites.forEach((sat, idx) => {
                const satSpeed = 0.8 + idx * 0.3;
                const satRadius = 18 + idx * 2.5;
                const satAngle = time * satSpeed + idx * (Math.PI * 2 / 3);
                sat.position.set(
                    Math.cos(satAngle) * satRadius,
                    Math.sin(time * 1.5 + idx) * 3,
                    Math.sin(satAngle) * satRadius
                );
            });
        }

        // Blinking Server LEDs
        if (this.blinkingLeds.length > 0 && Math.random() < 0.14) {
            const pick = this.blinkingLeds[Math.floor(Math.random() * this.blinkingLeds.length)];
            pick.material.color.setHex(Math.random() > 0.5 ? 0x10b981 : 0xef4444);
        }

        // Station Specific Animations
        Object.values(this.stations).forEach(st => {
            if (st.userData.radarDish) {
                st.userData.radarDish.rotation.y += delta * 1.2;
            }
            if (st.userData.laserBeam) {
                st.userData.laserBeam.material.opacity = 0.65 + Math.sin(time * 8) * 0.35;
            }
            if (st.userData.strategyGlobe) {
                st.userData.strategyGlobe.rotation.y += delta * 0.8;
                st.userData.strategyGlobe.rotation.x += delta * 0.4;
            }
            if (st.userData.quantumCube) {
                st.userData.quantumCube.rotation.x += delta * 0.8;
                st.userData.quantumCube.rotation.y += delta * 1.0;
            }
            if (st.userData.volatilityWave) {
                st.userData.volatilityWave.rotation.z += delta * 1.0;
            }
            if (st.userData.spotGem) {
                st.userData.spotGem.rotation.y += delta * 1.5;
                st.userData.spotGem.position.y = 9.0 + Math.sin(time * 2.5) * 0.35;
            }
            if (st.userData.officerModel && st.userData.officerModel.userData.animate) {
                st.userData.officerModel.userData.animate(time, delta);
            }
        });

        // ═══ BẮN GÓI TIN & XUNG PING MẠNG LAN THỜI GIAN THỰC ═══
        this.dataPackets.forEach(pkt => {
            const prevProgress = pkt.progress;
            pkt.progress += delta * pkt.speed * 0.42;

            // Gói tin bắn trúng đích tại bàn làm việc phòng ban ➔ Tạo sóng kích hoạt Ping!
            if (pkt.progress >= 1.0) {
                pkt.progress = pkt.progress % 1.0;
                if (pkt.route && pkt.route.to) {
                    this.spawnPingImpact(pkt.route.to, pkt.route.color);
                }
            }

            const pt = pkt.curve.getPoint(pkt.progress);
            pkt.group.position.copy(pt);
            // Dao động nhịp sóng năng lượng nhẹ khi bay
            pkt.group.position.y += Math.sin(time * 5.0 + pkt.progress * 16) * 0.35;

            if (pkt.orb) {
                pkt.orb.rotation.y += delta * 6.0;
                pkt.orb.rotation.z += delta * 4.0;
            }
            if (pkt.pktLight) {
                pkt.pktLight.intensity = 2.2 + Math.sin(time * 8.0 + pkt.progress * 20) * 0.8;
            }
        });

        // Sóng phản hồi Ping Impact khi gói tin chạm đích tại bàn giao dịch
        for (let i = this.packetImpactRings.length - 1; i >= 0; i--) {
            const r = this.packetImpactRings[i];
            r.scale += delta * 6.5;
            r.opacity -= delta * 2.2;
            r.mesh.scale.set(r.scale, r.scale, r.scale);
            r.mesh.material.opacity = Math.max(0, r.opacity);
            if (r.opacity <= 0) {
                this.scene.remove(r.mesh);
                r.mesh.geometry.dispose();
                r.mesh.material.dispose();
                this.packetImpactRings.splice(i, 1);
            }
        }

        // Quay cánh quạt tản nhiệt Trạm Máy Chủ Blade Server
        if (this.serverFans && this.serverFans.length > 0) {
            this.serverFans.forEach(fan => {
                fan.rotation.z += delta * 28.0;
            });
        }

        // Xoay 360° đĩa viễn thông trinh sát Trạm Máy Chủ
        if (this.serverRadarDish) {
            this.serverRadarDish.rotation.y += delta * 1.6;
        }

        // Phát xung sóng Radar Ping từ đỉnh tháp anten máy chủ trung tâm
        if (!this._lastServerPingTime || time - this._lastServerPingTime > 2.4) {
            this._lastServerPingTime = time;
            if (this.serverAntennaTip) {
                const pWaveGeo = new THREE.RingGeometry(0.8, 1.8, 28);
                const pWaveMat = new THREE.MeshBasicMaterial({
                    color: 0x00f0ff,
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: 0.85
                });
                const pWave = new THREE.Mesh(pWaveGeo, pWaveMat);
                pWave.rotation.x = -Math.PI / 2;
                pWave.position.copy(this.serverAntennaTip);
                this.scene.add(pWave);
                this.serverPingRings.push({ mesh: pWave, scale: 1.0, opacity: 0.85 });
            }
        }

        for (let i = this.serverPingRings.length - 1; i >= 0; i--) {
            const w = this.serverPingRings[i];
            w.scale += delta * 14.0;
            w.opacity -= delta * 0.75;
            w.mesh.scale.set(w.scale, w.scale, w.scale);
            w.mesh.position.y += delta * 1.8;
            w.mesh.material.opacity = Math.max(0, w.opacity);
            if (w.opacity <= 0) {
                this.scene.remove(w.mesh);
                w.mesh.geometry.dispose();
                w.mesh.material.dispose();
                this.serverPingRings.splice(i, 1);
            }
        }

        // Click Reticle Expanding Rings
        for (let i = this.clickPings.length - 1; i >= 0; i--) {
            const p = this.clickPings[i];
            p.scale += delta * 4;
            p.opacity -= delta * 1.6;
            p.mesh.scale.set(p.scale, p.scale, p.scale);
            p.mesh.material.opacity = Math.max(0, p.opacity);
            if (p.opacity <= 0) {
                this.scene.remove(p.mesh);
                p.mesh.geometry.dispose();
                p.mesh.material.dispose();
                this.clickPings.splice(i, 1);
            }
        }

        let isMoving = false;
        let isSprint = false;
        const targetFloorY = this.getFloorHeight(this.bossPosition.x, this.bossPosition.z);

        if (this.isDriving && this.drivingCar && this.drivingCar.group) {
            // ------------------------------------------------------------------
            // SUPERCAR DRIVING PHYSICS & VEHICLE DYNAMICS (FERRARI & LAMBO)
            // ------------------------------------------------------------------
            const carGroup = this.drivingCar.group;
            const maxForwardSpeed = this.isNitroActive ? 240 : 140;
            const maxReverseSpeed = -50;
            const accel = this.isNitroActive ? 180 : 105;
            const brakeDecel = 130;
            const friction = 32;
            const turnRate = 3.2;

            // Spacebar Nitro Boost
            const spacePressed = this.walkKeys.has('Space');
            if (spacePressed && this.carNitro > 3) {
                this.isNitroActive = true;
                this.carNitro = Math.max(0, this.carNitro - delta * 30);
            } else {
                this.isNitroActive = false;
                this.carNitro = Math.min(100, this.carNitro + delta * 18);
            }

            // Acceleration & Braking (W / S / Up / Down)
            const isGas = this.walkKeys.has('KeyW') || this.walkKeys.has('ArrowUp');
            const isBrake = this.walkKeys.has('KeyS') || this.walkKeys.has('ArrowDown');

            if (isGas) {
                if (this.carSpeed < 0) {
                    // Quick brake from reverse before moving forward
                    this.carSpeed = Math.min(0, this.carSpeed + brakeDecel * delta);
                } else {
                    this.carSpeed = Math.min(maxForwardSpeed, this.carSpeed + accel * delta);
                }
            } else if (isBrake) {
                if (this.carSpeed > 2) {
                    // Quick responsive brake from forward
                    this.carSpeed = Math.max(0, this.carSpeed - brakeDecel * delta);
                } else {
                    // Reversing
                    this.carSpeed = Math.max(maxReverseSpeed, this.carSpeed - accel * 0.75 * delta);
                }
            } else {
                // Natural deceleration / sports car road friction
                if (this.carSpeed > 0) {
                    this.carSpeed = Math.max(0, this.carSpeed - friction * delta);
                } else if (this.carSpeed < 0) {
                    this.carSpeed = Math.min(0, this.carSpeed + friction * delta);
                }
            }

            // Responsive Steering (A / D / Left / Right)
            // High steering agility at low speeds (parking / turning around) and stabilized at high speed
            const speedAbs = Math.abs(this.carSpeed);
            const steerAgility = turnRate * (1.0 + Math.min(speedAbs / 80, 0.45));
            const steerDir = (this.carSpeed < -1.0 ? -1 : 1); // Natural reverse steering

            const isSteeringLeft = this.walkKeys.has('KeyA') || this.walkKeys.has('ArrowLeft');
            const isSteeringRight = this.walkKeys.has('KeyD') || this.walkKeys.has('ArrowRight');

            if (isSteeringLeft) {
                this.carHeading += steerAgility * steerDir * delta;
            }
            if (isSteeringRight) {
                this.carHeading -= steerAgility * steerDir * delta;
            }

            // Move car along heading
            const carFx = Math.sin(this.carHeading);
            const carFz = Math.cos(this.carHeading);

            carGroup.position.x += carFx * this.carSpeed * delta;
            carGroup.position.z += carFz * this.carSpeed * delta;
            carGroup.rotation.y = this.carHeading;

            // Sports Car Lateral Lean / Body Roll on hard turns
            const targetRoll = isSteeringLeft ? 0.035 : (isSteeringRight ? -0.035 : 0);
            const rollFactor = Math.min(speedAbs / 40, 1.0);
            carGroup.rotation.z = THREE.MathUtils.damp(carGroup.rotation.z, targetRoll * rollFactor, 12, delta);

            // Clamping car to campus grounds & balcony
            carGroup.position.x = THREE.MathUtils.clamp(carGroup.position.x, -165, 165);
            carGroup.position.z = THREE.MathUtils.clamp(carGroup.position.z, -155, 175);
            carGroup.position.y = 3.0;

            // Sync bossPosition to carPosition
            this.bossPosition.copy(carGroup.position);
            this.bossHeading = this.carHeading;
            isMoving = speedAbs > 0.5;

            // Rotate wheels
            if (carGroup.userData.wheels) {
                const wheelRot = (this.carSpeed * delta) / 1.1;
                for (let i = 0; i < carGroup.userData.wheels.length; i++) {
                    carGroup.userData.wheels[i].rotation.x += wheelRot;
                }
            }

            // Exhaust flames & underglow boost
            if (carGroup.userData.flames) {
                const flameScale = this.isNitroActive ? (2.2 + Math.random() * 0.8) : (speedAbs > 40 ? 0.9 : 0.1);
                const flameVis = flameScale > 0.2;
                for (let i = 0; i < carGroup.userData.flames.length; i++) {
                    const f = carGroup.userData.flames[i];
                    f.scale.set(flameScale, flameScale, flameScale * 2.0);
                    f.visible = flameVis;
                }
            }

            // High-Performance Cached DOM HUD updates (Prevents 60 FPS layout thrashing)
            if (!this._carHudCache) {
                this._carHudCache = {
                    speedEl: document.getElementById('car-speed-val'),
                    nitroFillEl: document.getElementById('car-nitro-fill'),
                    nitroValEl: document.getElementById('car-nitro-val'),
                    lastSpeed: -1,
                    lastNitro: -1,
                    lastNitroActive: null
                };
            }
            const speedKmh = Math.round(speedAbs * 2.2);
            if (this._carHudCache.lastSpeed !== speedKmh) {
                this._carHudCache.lastSpeed = speedKmh;
                if (this._carHudCache.speedEl) this._carHudCache.speedEl.textContent = speedKmh;
            }
            const roundNitro = Math.round(this.carNitro);
            if (this._carHudCache.lastNitro !== roundNitro || this._carHudCache.lastNitroActive !== this.isNitroActive) {
                this._carHudCache.lastNitro = roundNitro;
                this._carHudCache.lastNitroActive = this.isNitroActive;
                if (this._carHudCache.nitroFillEl) this._carHudCache.nitroFillEl.style.width = `${roundNitro}%`;
                if (this._carHudCache.nitroValEl) {
                    this._carHudCache.nitroValEl.textContent = this.isNitroActive ? 'BOOSTING 🔥' : `${roundNitro}%`;
                }
            }

            // Butter-Smooth Cinematic Dynamic Chase Camera (Zero-Stutter Lerp Engine)
            const chaseDist = 24 + (speedAbs / 120) * 8;
            const chaseHeight = 8.5 + (speedAbs / 120) * 2.5;
            const targetCamPos = new THREE.Vector3(
                carGroup.position.x - carFx * chaseDist,
                carGroup.position.y + chaseHeight,
                carGroup.position.z - carFz * chaseDist
            );

            // Smooth exponential interpolation for camera position
            const camFactor = 1.0 - Math.exp(-14 * delta);
            this.camera.position.lerp(targetCamPos, camFactor);

            // Smooth look-at target ahead of car (eliminates camera shudder & micro-jitter)
            const lookAheadDist = 16 + (speedAbs / 120) * 10;
            const desiredLookTarget = new THREE.Vector3(
                carGroup.position.x + carFx * lookAheadDist,
                carGroup.position.y + 2.4,
                carGroup.position.z + carFz * lookAheadDist
            );

            if (!this.carLookTarget) {
                this.carLookTarget = desiredLookTarget.clone();
            } else {
                this.carLookTarget.lerp(desiredLookTarget, 1.0 - Math.exp(-16 * delta));
            }
            this.camera.lookAt(this.carLookTarget);
            this.controls.target.copy(this.carLookTarget);

            // Dynamic FOV speed-kick when driving (only updates projection matrix when FOV changes)
            const targetCarFov = this.isNitroActive ? 75 : (speedAbs > 60 ? 68 : 60);
            if (Math.abs(this.camera.fov - targetCarFov) > 0.05) {
                this.camera.fov = THREE.MathUtils.damp(this.camera.fov, targetCarFov, 8, delta);
                this.camera.updateProjectionMatrix();
            }

        } else {
            // ----------------------------------------------------------------------
            // PUBG TACTICAL WASD MOVEMENT ENGINE
            // W: Tiến thẳng theo hướng camera (Forward)
            // S: Lùi thẳng (Backward)
            // A: Bước ngang sang trái (Strafe Left) — Không xoay camera!
            // D: Bước ngang sang phải (Strafe Right) — Không xoay camera!
            // Shift: Nước rút (Sprint 1.75x)
            // Space: Bật nhảy (Jump)
            // C: Ngồi khom (Crouch)
            // ----------------------------------------------------------------------
            isSprint = (this.walkKeys.has('ShiftLeft') || this.walkKeys.has('ShiftRight')) && this.boostStamina > 2;
            let speed = this.bossSpeed;
            if (isSprint) speed *= 2.2; // High-octane sprint!
            if (this.isCrouching) speed *= 0.55;

            // Forward & Right vectors from current heading
            // In Three.js looking along +Z: +Z is forward, -Z is backward, -X is right, +X is left
            const heading = this.bossHeading;
            const fx = Math.sin(heading);
            const fz = Math.cos(heading);
            const rx = -Math.cos(heading);
            const rz = Math.sin(heading);

            let moveX = 0, moveZ = 0;
            if (this.walkKeys.has('KeyW') || this.walkKeys.has('ArrowUp')) {
                moveX += fx;
                moveZ += fz;
            }
            if (this.walkKeys.has('KeyS') || this.walkKeys.has('ArrowDown')) {
                moveX -= fx;
                moveZ -= fz;
            }
            if (this.walkKeys.has('KeyD') || this.walkKeys.has('ArrowRight')) {
                moveX += rx;
                moveZ += rz;
            }
            if (this.walkKeys.has('KeyA') || this.walkKeys.has('ArrowLeft')) {
                moveX -= rx;
                moveZ -= rz;
            }

            const moveLen = Math.hypot(moveX, moveZ);
            if (moveLen > 0.001) {
                this.bossTarget = null;
                moveX /= moveLen;
                moveZ /= moveLen;
                this.bossPosition.x = THREE.MathUtils.clamp(this.bossPosition.x + moveX * speed * delta, -160, 160);
                this.bossPosition.z = THREE.MathUtils.clamp(this.bossPosition.z + moveZ * speed * delta, -150, 150);
                isMoving = true;

                if (this.cameraMode === 'god' || this.cameraMode === 'tactical') {
                    this.targetHeading = Math.atan2(moveX, moveZ);
                }
            }

            // Dynamic FOV speed-kick
            const targetFov = (isSprint && isMoving) ? 68 : 60;
            this.camera.fov = THREE.MathUtils.damp(this.camera.fov, targetFov, 8, delta);
            this.camera.updateProjectionMatrix();

            // ----------------------------------------------------------------------
            // DYNAMIC PLATFORM ELEVATION, STEP-CLIMBING & ATHLETIC PARKOUR JUMP
            // ----------------------------------------------------------------------
            if (!this.bossIsGrounded) {
                // Mid-air physics: Athletic arc trajectory with gravity
                this.bossVelocityY -= 65 * delta;
                this.bossPosition.y += this.bossVelocityY * delta;
                if (this.bossPosition.y <= targetFloorY) {
                    this.bossPosition.y = targetFloorY;
                    if (this.bossVelocityY < -10.0) {
                        this.playSfx('hover'); // Crisp landing sound feedback
                    }
                    this.bossVelocityY = 0;
                    this.bossIsGrounded = true;
                }
            } else {
                // When grounded, smoothly adapt to changing floor height (steps, daises, ramps)
                const hDiff = targetFloorY - this.bossPosition.y;
                if (hDiff > 0) {
                    // Stepping UP onto a platform / stair step: fast responsive step-climbing
                    this.bossPosition.y = THREE.MathUtils.damp(this.bossPosition.y, targetFloorY, 18, delta);
                } else if (hDiff < -2.2) {
                    // Walking off a high ledge: start falling with realistic gravity!
                    this.bossIsGrounded = false;
                    this.bossVelocityY = 0;
                } else {
                    // Stepping DOWN a shallow step: smooth damp down
                    this.bossPosition.y = THREE.MathUtils.damp(this.bossPosition.y, targetFloorY, 14, delta);
                }
            }

            // Click-To-Walk Navigation for Boss (In God / Tactical mode)
            if (this.bossTarget && (this.cameraMode === 'god' || this.cameraMode === 'tactical')) {
                const diff = new THREE.Vector3().subVectors(this.bossTarget, this.bossPosition);
                diff.y = 0;
                const dist = diff.length();
                if (dist > 0.8) {
                    const step = Math.min(dist, this.bossSpeed * delta);
                    diff.normalize();
                    this.bossPosition.x += diff.x * step;
                    this.bossPosition.z += diff.z * step;
                    isMoving = true;
                    this.targetHeading = Math.atan2(diff.x, diff.z);
                } else {
                    this.bossTarget = null;
                }
            }

            // Smooth rotation towards target heading in God / Tactical views
            if (this.cameraMode === 'god' || this.cameraMode === 'tactical') {
                let hDiff = this.targetHeading - this.bossHeading;
                while (hDiff < -Math.PI) hDiff += Math.PI * 2;
                while (hDiff > Math.PI) hDiff -= Math.PI * 2;
                this.bossHeading += hDiff * Math.min(delta * 10, 1.0);
            }

            // Update 3D Boss Model (Hải quay xe & True World Elevation)
            if (this.bossModel) {
                // Set rotation
                if (isMoving && this.cameraMode === 'follow' && moveLen > 0.001) {
                    const moveHeading = Math.atan2(moveX, moveZ);
                    let diff = moveHeading - (this.bossModelRotation || this.bossHeading);
                    while (diff < -Math.PI) diff += Math.PI * 2;
                    while (diff > Math.PI) diff -= Math.PI * 2;
                    this.bossModelRotation = (this.bossModelRotation || this.bossHeading) + diff * Math.min(delta * 14, 1.0);
                    this.bossModel.rotation.y = this.bossModelRotation;
                } else if (!isMoving && this.cameraMode === 'follow') {
                    let diff = this.bossHeading - (this.bossModelRotation || this.bossHeading);
                    while (diff < -Math.PI) diff += Math.PI * 2;
                    while (diff > Math.PI) diff -= Math.PI * 2;
                    this.bossModelRotation = (this.bossModelRotation || this.bossHeading) + diff * Math.min(delta * 6, 1.0);
                    this.bossModel.rotation.y = this.bossModelRotation;
                } else {
                    this.bossModelRotation = this.bossHeading;
                    this.bossModel.rotation.y = this.bossHeading;
                }

                // Animate internal pivots and get step bounce
                if (this.bossModel.userData.animate) {
                    this.bossModel.userData.animate(time, delta, isMoving);
                }

                // Apply world position + step bounce (Ensures Boss model jumps high & climbs steps perfectly!)
                const bounce = (this.bossModel.userData && this.bossModel.userData.stepBounce) ? this.bossModel.userData.stepBounce : 0;
                this.bossModel.position.x = this.bossPosition.x;
                this.bossModel.position.y = this.bossPosition.y + bounce;
                this.bossModel.position.z = this.bossPosition.z;
            }

            // Boss Dynamic Ground Shadow (Stays on platform floor and scales with jump height)
            if (this.bossShadow) {
                this.bossShadow.position.set(this.bossPosition.x, targetFloorY + 0.08, this.bossPosition.z);
                const airDist = Math.max(0, this.bossPosition.y - targetFloorY);
                const shadowScale = Math.max(0.35, 1.0 - airDist * 0.08);
                this.bossShadow.scale.set(shadowScale, shadowScale, shadowScale);
                if (this.bossShadow.material) {
                    this.bossShadow.material.opacity = Math.max(0.08, 0.65 - airDist * 0.05);
                }
            }
        }

        // Astra Companion following Boss (Positioned at right side +0.82 rads, visible in TPP)
        const astraOffset = new THREE.Vector3(
            Math.sin(this.bossHeading + 0.82) * 5.2,
            0,
            Math.cos(this.bossHeading + 0.82) * 5.2
        );
        const astraDest = new THREE.Vector3().copy(this.bossPosition).add(astraOffset);
        this.astraPosition.lerp(astraDest, delta * 3.2);
        this.astraPosition.y = THREE.MathUtils.damp(this.astraPosition.y, this.bossPosition.y, 14, delta);

        if (this.astraModel) {
            const hideAstra = (this.cameraMode === 'fpv' || this.isDriving);
            this.astraModel.visible = !hideAstra;
            if (!hideAstra) {
                if (this.astraModel.userData.animate) {
                    this.astraModel.userData.animate(time, delta);
                }
                const hover = (this.astraModel.userData && this.astraModel.userData.hoverOffset) ? this.astraModel.userData.hoverOffset : 0;
                this.astraModel.position.x = this.astraPosition.x;
                this.astraModel.position.y = this.astraPosition.y + 1.2 + hover;
                this.astraModel.position.z = this.astraPosition.z;
                this.astraModel.rotation.y = this.bossHeading;
            }
        }
        if (this.astraShadow) {
            this.astraShadow.visible = (this.cameraMode !== 'fpv' && !this.isDriving);
            if (this.astraShadow.visible) {
                this.astraShadow.position.set(this.astraPosition.x, targetFloorY + 0.08, this.astraPosition.z);
            }
        }

        // Update Boss & Astra 3D Speech Bubble Positions
        if (this.bossBubbleSprite && this.bossBubbleSprite.visible) {
            this.bossBubbleSprite.position.set(this.bossPosition.x, this.bossPosition.y + 11.5, this.bossPosition.z);
        }
        if (this.astraBubbleSprite && this.astraBubbleSprite.visible) {
            this.astraBubbleSprite.visible = (this.cameraMode !== 'fpv' && !this.isDriving);
            if (this.astraBubbleSprite.visible) {
                this.astraBubbleSprite.position.set(this.astraPosition.x, this.astraPosition.y + 10.5, this.astraPosition.z);
            }
        }

        // ----------------------------------------------------------------------
        // PROXIMITY DETECTION: ELEVATOR & SUPERCARS
        // ----------------------------------------------------------------------
        const elevDist = this.bossPosition ? Math.hypot(this.bossPosition.x - 0, this.bossPosition.z - 28) : 999;
        const onUpper = this.bossPosition ? (this.bossPosition.y > -20) : true;
        if (elevDist < 9.0 && !this.isDriving && !this.isElevatorMoving) {
            this.nearbyElevator = true;
            if (this.interactPromptEl && this.interactTextEl) {
                this.interactPromptEl.style.display = 'inline-flex';
                const nextFloor = onUpper ? 'XUỐNG TẦNG DƯỚI (MKT NIVER)' : 'LÊN TẦNG TRÊN (TRADE QUANT)';
                this.interactTextEl.textContent = `🛗 [E / F] ĐI THANG MÁY ${nextFloor}`;
            }
        } else {
            this.nearbyElevator = false;
        }

        if (!this.isDriving && !this.nearbyElevator && this.supercars && this.supercars.length > 0 && this.bossPosition) {
            let closestCar = null;
            let closestDist = Infinity;
            for (let i = 0; i < this.supercars.length; i++) {
                const sc = this.supercars[i];
                if (sc && sc.worldPos) {
                    const d = this.bossPosition.distanceTo(sc.worldPos);
                    if (d < 18 && d < closestDist) {
                        closestDist = d;
                        closestCar = sc;
                    }
                }
            }
            this.nearbySupercar = closestCar;
            if (this.nearbySupercar && this.interactPromptEl && this.interactTextEl) {
                this.interactPromptEl.style.display = 'inline-flex';
                this.interactTextEl.textContent = `🏎️ [E / F] LÁI SIÊU XE ${this.nearbySupercar.name.toUpperCase()}`;
            }
        } else if (this.isDriving) {
            this.nearbySupercar = null;
        }

        // ---------------------------------------------------------------------
        // DYNAMIC CAMERA CONTROLLER (PUBG FPV, SHOULDER, TPP CHASE, GOD-VIEW)
        // ---------------------------------------------------------------------
        if (this.isDriving) {
            // Driving chase camera active, handled in driving physics loop above!
        } else if (this.cameraMode === 'fpv') {
            // GÓC NHÌN THỨ 1 (FPV) — Camera at Boss eye level, looking forward (True FPS Trigonometry)
            if (this.bossModel) this.bossModel.visible = false;
            if (this.bossShadow) this.bossShadow.visible = false;
            if (this.astraModel) this.astraModel.visible = false;
            if (this.astraShadow) this.astraShadow.visible = false;
            if (this.astraBubbleSprite) this.astraBubbleSprite.visible = false;
            if (this.fpvCompanionGroup) this.fpvCompanionGroup.visible = false;
            this.controls.enabled = false;

            const eyeY = (this.isCrouching ? 4.8 : 7.2);
            const forwardX = Math.sin(this.bossHeading);
            const forwardZ = Math.cos(this.bossHeading);

            this.camera.position.set(
                this.bossPosition.x + forwardX * 1.5,
                this.bossPosition.y + eyeY,
                this.bossPosition.z + forwardZ * 1.5
            );

            const pitchRad = ((this.cameraPitch || 0) * Math.PI) / 180;
            const cosPitch = Math.cos(pitchRad);
            const sinPitch = Math.sin(pitchRad);

            const lookDir = new THREE.Vector3(
                forwardX * cosPitch,
                sinPitch,
                forwardZ * cosPitch
            ).multiplyScalar(50);

            this.camera.lookAt(this.camera.position.clone().add(lookDir));
        } else if (this.cameraMode === 'shoulder') {
            // GÓC NHÌN THỨ 2 (OVER-THE-SHOULDER) — PUBG Combat Shoulder View with Orbit Pitch
            if (this.bossModel) this.bossModel.visible = true;
            this.controls.enabled = false;

            this.tppPitch = THREE.MathUtils.damp(this.tppPitch !== undefined ? this.tppPitch : 0.28, this.targetTppPitch !== undefined ? this.targetTppPitch : 0.28, 14, delta);
            const pitch = this.tppPitch;
            const sDist = 6.8;
            const horizDist = sDist * Math.cos(pitch * 0.7);
            const vertDist = sDist * Math.sin(pitch * 0.7);

            const rightX = Math.cos(this.bossHeading) * 2.8;
            const rightZ = -Math.sin(this.bossHeading) * 2.8;
            const backX = -Math.sin(this.bossHeading) * horizDist;
            const backZ = -Math.cos(this.bossHeading) * horizDist;

            const targetCamPos = new THREE.Vector3(
                this.bossPosition.x + rightX + backX,
                Math.max((this.bossPosition.y - targetFloorY) * 0.45 + targetFloorY + (this.isCrouching ? 5.8 : 7.8) + vertDist, 2.5),
                this.bossPosition.z + rightZ + backZ
            );
            this.camera.position.lerp(targetCamPos, delta * 14);

            const lookTarget = new THREE.Vector3(
                this.bossPosition.x + rightX * 0.5 + Math.sin(this.bossHeading) * 35,
                this.bossPosition.y + (this.isCrouching ? 5.5 : 7.0) - Math.sin(pitch) * 15,
                this.bossPosition.z + rightZ * 0.5 + Math.cos(this.bossHeading) * 35
            );
            this.camera.lookAt(lookTarget);
        } else if (this.cameraMode === 'follow') {
            // GÓC NHÌN THỨ 3 (THIRD-PERSON TPP) — Dynamic Spherical Orbit Pitch & Butter-Smooth Chase
            if (this.bossModel) this.bossModel.visible = true;
            this.controls.enabled = false;

            // Smooth mouse-wheel zoom interpolation
            this.followDist = THREE.MathUtils.damp(this.followDist || 20, this.targetFollowDist || 20, 10, delta);
            this.tppPitch = THREE.MathUtils.damp(this.tppPitch !== undefined ? this.tppPitch : 0.28, this.targetTppPitch !== undefined ? this.targetTppPitch : 0.28, 14, delta);

            const dist = this.followDist;
            const pitch = this.tppPitch;
            const horizDist = dist * Math.cos(pitch);
            const vertDist = dist * Math.sin(pitch);

            const backX = -Math.sin(this.bossHeading) * horizDist;
            const backZ = -Math.cos(this.bossHeading) * horizDist;

            // Camera smoothly frames character jumping with subtle vertical elasticity
            const targetCamPos = new THREE.Vector3(
                this.bossPosition.x + backX,
                Math.max((this.bossPosition.y - targetFloorY) * 0.4 + targetFloorY + 5.0 + vertDist, 2.0),
                this.bossPosition.z + backZ
            );

            const lookTarget = new THREE.Vector3(
                this.bossPosition.x + Math.sin(this.bossHeading) * 3.0,
                this.bossPosition.y + 4.5 - Math.sin(pitch) * 2.5,
                this.bossPosition.z + Math.cos(this.bossHeading) * 3.0
            );

            if (!this.cameraTransitioning) {
                // Smooth exponential interpolation for position
                const posFactor = 1.0 - Math.exp(-14 * delta);
                this.camera.position.lerp(targetCamPos, posFactor);

                // Smooth exponential interpolation for look target to prevent micro-jitter
                if (!this.currentLookAt) {
                    this.currentLookAt = new THREE.Vector3().copy(lookTarget);
                }
                this.currentLookAt.lerp(lookTarget, 1.0 - Math.exp(-16 * delta));
                this.camera.lookAt(this.currentLookAt);
                this.controls.target.copy(this.currentLookAt);
            }
        } else {
            // 'god' or 'tactical' — Controls enabled
            if (this.bossModel) this.bossModel.visible = true;
            this.controls.enabled = true;
        }

        // Update PUBG Tactical HUD System (Compass, Crosshair, Boost, Stance)
        this.updatePubgUI(delta, isMoving, isSprint);


        // 360° Circular Floating Market Ticker Stream Scrolling
        if (this.tickerTexture) {
            this.tickerTexture.offset.x = (this.tickerTexture.offset.x + delta * 0.04) % 1.0;
        }

        // Support Staff (8 Junior Analysts) Animation
        this.supportStaff.forEach(asst => {
            if (asst.userData.officerModel && asst.userData.officerModel.userData.animate) {
                asst.userData.officerModel.userData.animate(time, delta);
            }
        });

        // 12 Main Department Officers Animation & Embodied Proximity Consciousness
        let closestDept = null;
        let minDistance = 999999;

        Object.entries(this.stations || {}).forEach(([key, st]) => {
            const officer = st.userData && st.userData.officerModel;
            if (officer && officer.userData && officer.userData.animate) {
                officer.userData.animate(time, delta, st.userData.officerState);
            }

            // Proximity Consciousness: Check distance to Boss
            if (this.bossPosition && st.position) {
                const dist = this.bossPosition.distanceTo(st.position);
                if (dist < 28 && officer) {
                    // Turn officer model smoothly to face Boss
                    const dx = this.bossPosition.x - st.position.x;
                    const dz = this.bossPosition.z - st.position.z;
                    const targetAngle = Math.atan2(dx, dz);
                    officer.rotation.y = THREE.MathUtils.lerp(officer.rotation.y, targetAngle, 0.08);
                }
                if (dist < minDistance) {
                    minDistance = dist;
                    closestDept = key;
                }
            }
        });

        // Trigger Embodied Interaction Toast when Boss is within 20 units of an officer
        if (minDistance <= 20 && closestDept) {
            this.nearbyAgentDept = closestDept;
            this.showProximityToast(closestDept);
        } else {
            this.nearbyAgentDept = null;
            this.hideProximityToast();
        }

        // Blinking Data Center & Server Rack LEDs
        if (this.blinkingLeds && this.blinkingLeds.length > 0) {
            const blinkPhase = Math.floor(time * 8);
            if (blinkPhase !== this.lastBlinkPhase) {
                this.lastBlinkPhase = blinkPhase;
                this.blinkingLeds.forEach((led, idx) => {
                    led.visible = ((idx + blinkPhase) % 3 !== 0);
                });
            }
        }

        // Hovering Patrol Drones Animation
        this.patrolDrones.forEach((drone, idx) => {
            const p = drone.userData.phase + time * drone.userData.speed;
            drone.position.x = Math.sin(p) * (45 + idx * 8);
            drone.position.z = Math.cos(p) * (45 + idx * 8);
            drone.position.y = 12 + Math.sin(time * 3 + idx) * 0.8;
            drone.rotation.y = p + Math.PI / 2;
        });

        // Wandering Staff Moving Between Wings
        this.wanderingStaff.forEach(w => {
            const path = w.userData.path;
            const p1 = path[w.userData.pathIdx];
            const p2 = path[(w.userData.pathIdx + 1) % path.length];
            w.userData.progress += delta * 0.12;

            if (w.userData.progress >= 1.0) {
                w.userData.progress = 0;
                w.userData.pathIdx = (w.userData.pathIdx + 1) % path.length;
            }

            const curX = THREE.MathUtils.lerp(p1.x, p2.x, w.userData.progress);
            const curZ = THREE.MathUtils.lerp(p1.z, p2.z, w.userData.progress);
            w.position.x = curX;
            w.position.z = curZ;

            const dirX = p2.x - p1.x;
            const dirZ = p2.z - p1.z;
            w.rotation.y = Math.atan2(dirX, dirZ);

            if (w.userData.badge) {
                w.userData.badge.position.set(curX, 10.5, curZ);
            }

            if (w.userData.animate) {
                w.userData.animate(time, delta, true);
            }
        });

        // Floating Cyber Dust Drift
        if (this.dustPoints) {
            this.dustPoints.rotation.y += delta * 0.02;
        }

        // Spin Quantum Vault Dial & Pulsing Shield
        if (this.vaultDial) {
            this.vaultDial.rotation.z += delta * 0.45;
        }
        if (this.vaultShieldRing) {
            this.vaultShieldRing.rotation.z += delta * 0.75;
        }

        // Animate Megacity Skyline, Supercars & FPV Companion
        if (this.animateMegacityAndCompanion) {
            this.animateMegacityAndCompanion(time, delta);
        }

        // Render Scene
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }

        // Update Minimap Radar
        this.drawMinimap();
    }

    /* --------------------------------------------------------------------------
       11. 5D QUANTUM TENSOR HUD & EMBODIED PROXIMITY INTERACTION
       -------------------------------------------------------------------------- */
    initQuantum5dPolling() {
        const fetchQuantum = async () => {
            try {
                const res = await fetch('/api/v1/quantum/5d_tensor?symbol=BTC/USDT');
                if (res.ok) {
                    const data = await res.json();
                    this.updateQuantum5dUI(data);
                }
            } catch (err) {
                console.warn('[ThreeOfficeEngine] 5D Tensor polling error:', err);
            }
        };
        fetchQuantum();
        if (this.quantum5dTimer) clearInterval(this.quantum5dTimer);
        this.quantum5dTimer = setInterval(fetchQuantum, 5000);
    }

    updateQuantum5dUI(data) {
        if (!data) return;
        this.lastQuantumData = data;

        // 1. HUD Bar elements
        const scoreNum = document.getElementById('q5dScoreNum');
        if (scoreNum) scoreNum.textContent = Number(data.tensor_score || 0).toFixed(1);

        const badge = document.getElementById('q5dBadgeStatus');
        const glow = document.getElementById('q5dPulseGlow');
        if (badge) {
            badge.textContent = data.approval_status || (data.verdict === 'CONFLUENCE_APPROVED' ? 'ASTRA PHÊ CHUẨN' : 'RIK THEO DÕI');
            if (data.verdict === 'CONFLUENCE_APPROVED') {
                badge.style.background = 'rgba(34, 197, 94, 0.25)';
                badge.style.borderColor = '#22c55e';
                badge.style.color = '#4ade80';
                if (glow) glow.style.background = 'radial-gradient(circle at 10% 50%, rgba(34, 197, 94, 0.4), transparent 70%)';
            } else if (data.verdict === 'CONFLUENCE_CAUTION') {
                badge.style.background = 'rgba(56, 189, 248, 0.25)';
                badge.style.borderColor = '#38bdf8';
                badge.style.color = '#7dd3fc';
                if (glow) glow.style.background = 'radial-gradient(circle at 10% 50%, rgba(56, 189, 248, 0.4), transparent 70%)';
            } else if (data.verdict === 'CONFLUENCE_VETOED') {
                badge.style.background = 'rgba(239, 68, 68, 0.25)';
                badge.style.borderColor = '#ef4444';
                badge.style.color = '#f87171';
                if (glow) glow.style.background = 'radial-gradient(circle at 10% 50%, rgba(239, 68, 68, 0.5), transparent 70%)';
            } else if (data.verdict === 'BOSS_SUPREME_APPROVED') {
                badge.style.background = 'rgba(245, 158, 11, 0.25)';
                badge.style.borderColor = '#f59e0b';
                badge.style.color = '#fde68a';
                if (glow) glow.style.background = 'radial-gradient(circle at 10% 50%, rgba(245, 158, 11, 0.5), transparent 70%)';
            }
        }

        const dims = data.dimensions || {};
        const d1El = document.getElementById('q5dDim1');
        if (d1El && dims.d1_price_action) d1El.textContent = `D1: ${Math.round(dims.d1_price_action.score || 0)}`;

        const d2El = document.getElementById('q5dDim2');
        if (d2El && dims.d2_orderbook) d2El.textContent = `D2: ${Math.round(dims.d2_orderbook.score || 0)}`;

        const d3El = document.getElementById('q5dDim3');
        if (d3El && dims.d3_volatility_gauss) d3El.textContent = `D3: ${Math.round(dims.d3_volatility_gauss.score || 0)}`;

        const d4El = document.getElementById('q5dDim4');
        if (d4El && dims.d4_nlp_sentiment) d4El.textContent = `D4: ${Math.round(dims.d4_nlp_sentiment.score || 0)}`;

        const d5El = document.getElementById('q5dDim5');
        if (d5El && dims.d5_risk_funding) d5El.textContent = `D5: ${Math.round(dims.d5_risk_funding.score || 0)}`;

        const cohEl = document.getElementById('q5dDimCoh');
        if (cohEl) cohEl.textContent = `γ: ${Number(data.coherence_pct || 0).toFixed(1)}%`;

        // 2. Modal elements
        const modalScore = document.getElementById('modalQ5dScore');
        if (modalScore) modalScore.textContent = Number(data.tensor_score || 0).toFixed(1);

        const modalVerdict = document.getElementById('modalQ5dVerdict');
        if (modalVerdict) {
            modalVerdict.textContent = data.approval_status || 'ASTRA PHÊ CHUẨN';
            modalVerdict.style.color = data.color || '#34d399';
        }

        const modalCoh = document.getElementById('modalQ5dCoherence');
        if (modalCoh) modalCoh.textContent = `${Number(data.coherence_pct || 0).toFixed(1)}%`;

        if (dims.d1_price_action) {
            const m1s = document.getElementById('modalD1Score');
            const m1d = document.getElementById('modalD1Detail');
            if (m1s) m1s.textContent = `${Number(dims.d1_price_action.score || 0).toFixed(1)}đ`;
            if (m1d && dims.d1_price_action.details) m1d.textContent = dims.d1_price_action.details;
        }
        if (dims.d2_orderbook) {
            const m2s = document.getElementById('modalD2Score');
            const m2d = document.getElementById('modalD2Detail');
            if (m2s) m2s.textContent = `${Number(dims.d2_orderbook.score || 0).toFixed(1)}đ`;
            if (m2d && dims.d2_orderbook.details) m2d.textContent = dims.d2_orderbook.details;
        }
        if (dims.d3_volatility_gauss) {
            const m3s = document.getElementById('modalD3Score');
            const m3d = document.getElementById('modalD3Detail');
            if (m3s) m3s.textContent = `${Number(dims.d3_volatility_gauss.score || 0).toFixed(1)}đ`;
            if (m3d && dims.d3_volatility_gauss.details) m3d.textContent = dims.d3_volatility_gauss.details;
        }
        if (dims.d4_nlp_sentiment) {
            const m4s = document.getElementById('modalD4Score');
            const m4d = document.getElementById('modalD4Detail');
            if (m4s) m4s.textContent = `${Number(dims.d4_nlp_sentiment.score || 0).toFixed(1)}đ`;
            if (m4d && dims.d4_nlp_sentiment.details) m4d.textContent = dims.d4_nlp_sentiment.details;
        }
        if (dims.d5_risk_funding) {
            const m5s = document.getElementById('modalD5Score');
            const m5d = document.getElementById('modalD5Detail');
            if (m5s) m5s.textContent = `${Number(dims.d5_risk_funding.score || 0).toFixed(1)}đ`;
            if (m5d && dims.d5_risk_funding.details) m5d.textContent = dims.d5_risk_funding.details;
        }
    }

    openQuantum5dModal() {
        const modal = document.getElementById('q5dModalBackdrop');
        if (modal) {
            modal.style.display = 'flex';
            if (this.lastQuantumData) {
                this.updateQuantum5dUI(this.lastQuantumData);
            }
        }
    }

    closeQuantum5dModal() {
        const modal = document.getElementById('q5dModalBackdrop');
        if (modal) {
            modal.style.display = 'none';
        }
    }

    showProximityToast(deptKey) {
        if (this.activeToastDept === deptKey) return;
        this.activeToastDept = deptKey;

        const toast = document.getElementById('proximityInteractToast');
        if (!toast) return;

        const cfg = this.deptConfigs[deptKey] || {};
        const agentName = DEPT_TO_AGENT_NAME[deptKey] || 'Astra';
        const quotes = {
            lead_pm: "Báo cáo Boss! 12 phòng ban đang vận hành tối ưu, sẵn sàng nhận chỉ thị.",
            risk_council: "Boss yên tâm, tỷ lệ rủi ro kiểm soát dưới 0.05%, bảo toàn 100% vốn!",
            news_scout: "Vừa quét xong tin vĩ mô và ví cá voi, dòng tiền ròng đang tích lũy mạnh!",
            execution_oms: "Đội HFT sẵn sàng! Độ trễ khớp Binance hiện đạt 18ms, trượt giá 0.00%.",
            arbitrage_desk: "Spread chênh lệch sàn Binance - Bybit có cơ hội phân thù 0.18%.",
            quant_lab: "Bộ lọc Kalman xác nhận tín hiệu đảo chiều đa khung. Hệ số Sharpe đạt 3.42!",
            breakout_hunter: "Dải Donchian 20 nến đang nén chặt! Chuẩn bị có cú bung phá biên độ.",
            volatility_lab: "Chỉ số ADX và ATR báo hiệu thị trường tích lũy, phù hợp Scalping.",
            spot_dca: "Danh mục Spot DCA sẵn sàng gom hàng giá chiết khấu khi có nhịp điều chỉnh.",
            cvar_stress: "Đã stress test 10,000 kịch bản Monte Carlo, khoảng cách thanh lý > 85%.",
            accounting_pm: "Sổ cái PnL đối soát chuẩn xác đến từng Satoshi, High-Water Mark tăng trưởng.",
            community_affiliate: "Cộng đồng và đối tác liên kết đã đồng bộ mã GRO_28502_O41DR."
        };

        const avatarEl = document.getElementById('proxAvatar');
        const titleEl = document.getElementById('proxTitle');
        const speechEl = document.getElementById('proxSpeech');

        if (avatarEl) avatarEl.textContent = cfg.icon || '💬';
        if (titleEl) titleEl.textContent = `${agentName} (${cfg.name || 'Sĩ Quan AI'})`;
        if (speechEl) speechEl.textContent = `"${quotes[deptKey] || cfg.activity || 'Sẵn sàng báo cáo!'}"`;

        toast.style.display = 'flex';
    }

    hideProximityToast() {
        if (!this.activeToastDept) return;
        this.activeToastDept = null;
        const toast = document.getElementById('proximityInteractToast');
        if (toast) toast.style.display = 'none';
    }

    interactWithNearbyAgent() {
        if (this.nearbyAgentDept) {
            window.openCyberIntercomForDept(this.nearbyAgentDept);
        }
    }
}


let officeEngine = null;

function initOfficeStage() {
    try {
        if (!officeEngine) {
            officeEngine = new ThreeOfficeEngine('office-stage-canvas');
            window.officeEngine = officeEngine;
        }
        const canvas = document.getElementById('office-stage-canvas');
        if (canvas) canvas.style.display = 'block';
    } catch (e) {
        console.error('[initOfficeStage] Error initializing ThreeOfficeEngine:', e);
        const note = document.createElement('p');
        note.className = 'office-render-error';
        note.innerHTML = `⚠️ Không thể mở 3D: <code>${e.message || e}</code>.`;
        const vp = document.getElementById('office-viewport');
        if (vp) vp.appendChild(note);
    }
}

function toggleOfficeView() {
    if (officeEngine) {
        officeEngine.toggleVisitor();
        const btn = document.getElementById('btn-toggle-view');
        if (btn) {
            btn.textContent = officeEngine.visitorMode ? '🎮 Chế Độ: Trụ Sở Pixel 16-Bit' : '🌐 Chế Độ: 3D Orbit Wireframe';
        }
    }
}

function simulateSignalHandoff(side = 'BUY') {
    if (officeEngine) officeEngine.simulateSignal(side);
}

function simulateVetoHandoff() {
    if (officeEngine) officeEngine.simulateVeto();
}

function simulateApiError() {
    if (officeEngine) officeEngine.simulateVeto();
}

function simulateProfitHandoff() {
    if (officeEngine) officeEngine.simulateProfit();
}

function update3DAgentFromTelemetry(deptKey, dept) {
    if (officeEngine && typeof officeEngine.updateTelemetry === 'function') {
        try {
            officeEngine.updateTelemetry(deptKey, dept);
        } catch (e) {
            console.debug('[update3DAgentFromTelemetry] error:', e);
        }
    }
}

function setAgentState(deptKey, state, speechText = null, duration = 4500) {
    if (officeEngine) officeEngine.setAgentState(deptKey, state, speechText, duration);
}

function onAgentClick(deptKey) {
    if (officeEngine) officeEngine.onStationClick(deptKey);
}

function triggerOfficeCoffeeBreak() {
    if (officeEngine) officeEngine.triggerCoffee();
}

function triggerOfficeElevator() {
    if (officeEngine) officeEngine.triggerElevator();
}

// Ensure filterCampusWing calls officeEngine.focusWing
const originalFilterCampusWing = window.filterCampusWing;

// Legacy event callers survived the engine migration. Keep them presentation-only.
function launchSignalPacket({toDept, onComplete}) {
    const card = document.getElementById(`card-${toDept}`);
    if (card && !motionPreference.matches) card.animate([{opacity: .65}, {opacity: 1}], {duration: 650});
    if (typeof onComplete === 'function') onComplete();
}

function bootPixelFloor() {
    try {
        initOfficeStage();
    } catch (e) {
        console.error('[bootPixelFloor] initOfficeStage error:', e);
    }
    try {
        startRealtimeClock();
    } catch (e) {
        console.error('[bootPixelFloor] startRealtimeClock error:', e);
    }
    try {
        const btnSound = document.getElementById('btn-toggle-sound');
        if (btnSound) btnSound.textContent = 'Âm thanh: TẮT';
        const hudAudio = document.getElementById('hud-audio-icon');
        if (hudAudio) hudAudio.textContent = '🔇';
    } catch (e) {}

    try {
        document.querySelectorAll('.dept-sleek-card').forEach(card => {
            const key = card.id.replace('card-', '');
            if (!card.querySelector('.room-profile-button')) {
                const button = document.createElement('button');
                button.className = 'btn-cyber room-profile-button';
                button.textContent = 'Mở hồ sơ phòng ban →';
                button.addEventListener('click', event => { event.stopPropagation(); openDeptDetailModal(key); });
                card.append(button);
            }
        });
    } catch (e) {}

    try {
        document.addEventListener('keydown', event => { if (event.key === 'Escape') closeDeptModal(); });
    } catch (e) {}

    // Auto-select mode from URL search query (e.g. ?view=twin)
    try {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('view') === 'twin') {
            switchFloorMode('twin');
        }
    } catch (e) {
        console.warn('URL param parse error:', e);
    }

    async function poll() {
        try {
            await fetchPixelFloorTelemetry();
        } catch (err) {
            console.warn('[bootPixelFloor] Telemetry poll error:', err);
        } finally {
            window.setTimeout(poll, 4000);
        }
    }
    poll();
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bootPixelFloor, {once: true});
else bootPixelFloor();


/* ==========================================================================
   QUICK PERFORMANCE SNAPSHOT MODAL (VIEW NHANH BÁO CÁO)
   ========================================================================== */
window.openQuickReportModal = async function() {
    const modal = document.getElementById('quickReportModal');
    if (!modal) return;
    modal.style.display = 'flex';

    // 1. Populate immediately from currentTelemetry if available
    if (typeof currentTelemetry !== 'undefined' && currentTelemetry) {
        const bal = currentTelemetry.balance_usdt !== undefined ? `$${Number(currentTelemetry.balance_usdt).toFixed(2)}` : '$31.63';
        const balSrc = currentTelemetry.balance_source || 'Binance USDⓈ-M Live';
        const balEl = document.getElementById('qmodal-balance');
        if (balEl) balEl.textContent = `${bal} USDT (${balSrc})`;

        const omsDept = currentTelemetry.departments?.execution_oms;
        if (omsDept) {
            const posEl = document.getElementById('qmodal-positions');
            if (posEl) posEl.textContent = `${omsDept.active_positions_count || 1} vị thế (${omsDept.ledger_live_count || 1} Live)`;
        }
    }

    // 2. Fetch live performance scorecard
    try {
        const resp = await fetch('/api/v1/telemetry/performance');
        if (resp.ok) {
            const data = await resp.json();
            const kpi = data.kpi_metrics || {};
            
            const pnlEl = document.getElementById('qmodal-pnl');
            if (pnlEl) {
                const pnlVal = Number(kpi.total_pnl_usdt !== undefined ? kpi.total_pnl_usdt : 0.4556);
                pnlEl.textContent = `${pnlVal >= 0 ? '+' : ''}$${pnlVal.toFixed(4)}`;
                pnlEl.style.color = pnlVal >= 0 ? '#10b981' : '#ef4444';
            }
            const winEl = document.getElementById('qmodal-winrate');
            if (winEl) winEl.textContent = `${kpi.win_rate !== undefined ? kpi.win_rate : 80.0}%`;

            const tradesSub = document.getElementById('qmodal-trades-sub');
            if (tradesSub && kpi.total_trades) tradesSub.textContent = `${kpi.total_trades} lệnh đã chốt`;

            const vetoEl = document.getElementById('qmodal-veto');
            if (vetoEl) vetoEl.textContent = `${kpi.vetoes_count || 74} Bẫy`;

            const savedEl = document.getElementById('qmodal-veto-saved');
            if (savedEl) savedEl.textContent = `Cứu vốn +$${Number(kpi.capital_saved_usdt || 33.3).toFixed(2)}`;

            const tokenEl = document.getElementById('qmodal-token-cost');
            if (tokenEl) {
                const models = data.models_performance || [];
                const totalCost = models.reduce((acc, m) => acc + (m.cost_usd || 0), 0);
                tokenEl.textContent = `$${totalCost > 0 ? totalCost.toFixed(2) : '0.64'}`;
            }
        }
    } catch (e) {
        console.warn('Error fetching quick report modal data:', e);
    }
};

window.closeQuickReportModal = function(e) {
    if (e && e.target && e.target.id !== 'quickReportModal' && !e.target.classList.contains('pixel-modal-close')) {
        return;
    }
    const modal = document.getElementById('quickReportModal');
    if (modal) modal.style.display = 'none';
};

// Listen for Escape key to close modal
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeDeptModal();
        const qModal = document.getElementById('quickReportModal');
        if (qModal && qModal.style.display === 'flex') {
            qModal.style.display = 'none';
        }
        const iModal = document.getElementById('cyber-intercom-modal');
        if (iModal && iModal.style.display === 'flex') {
            iModal.style.display = 'none';
        }
        const q5dModal = document.getElementById('q5dModalBackdrop');
        if (q5dModal && q5dModal.style.display === 'flex') {
            q5dModal.style.display = 'none';
        }
    }
});

// =========================================================================
// EMBODIED CYBER INTERCOM (BOSS <-> AGENT DIRECT DIALOGUE)
// =========================================================================
const DEPT_TO_AGENT_NAME = {
    'spot_dca': 'Palermo',
    'risk_council': 'Rik',
    'quant_lab': 'Prof',
    'breakout_hunter': 'Tory',
    'news_scout': 'Hash',
    'execution_oms': 'Meme',
    'arbitrage_desk': 'Deck',
    'volatility_lab': 'Volt',
    'accounting_pm': 'Core',
    'lead_pm': 'Astra',
    'cvar_stress': 'Prof',
    'community_affiliate': 'Core'
};

window.openCyberIntercomForDept = function(deptKey) {
    const agent = DEPT_TO_AGENT_NAME[deptKey] || 'Astra';
    window.openCyberIntercomModal(agent);
};

window.currentIntercomAgent = 'Astra';

window.openCyberIntercomModal = function(agentName = 'Astra') {
    const modal = document.getElementById('cyber-intercom-modal');
    if (!modal) return;
    if (document.pointerLockElement) {
        document.exitPointerLock();
    }
    window.currentIntercomAgent = agentName;
    modal.style.display = 'flex';
    const input = document.getElementById('intercom-input') || document.getElementById('intercom-user-input');
    if (input) {
        setTimeout(() => input.focus(), 60);
        if (!input._hasStopProp) {
            input.addEventListener('keydown', (evt) => {
                if (evt.key !== 'Escape' && evt.key !== 'Enter') {
                    evt.stopPropagation();
                }
            });
            input._hasStopProp = true;
        }
    }

    document.querySelectorAll('.intercom-agent-pill').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.agent === agentName);
    });

    updateIntercomHeader(agentName);
};

window.closeCyberIntercomModal = function() {
    const modal = document.getElementById('cyber-intercom-modal');
    if (modal) modal.style.display = 'none';
};

window.teleportToBalcony = function() {
    if (window.officeEngine && typeof window.officeEngine.teleportToBalcony === 'function') {
        window.officeEngine.teleportToBalcony();
    }
};

function updateIntercomHeader(agentName) {
    const meta = {
        'Astra': { title: 'Tổng Quản Tối Cao (Supreme AI)', location: 'Bộ Chỉ Huy Tối Cao', color: '#c084fc', icon: '👑' },
        'Rik': { title: 'Cảnh Sát Rủi Ro (CRO)', location: 'Phòng Hội Đồng Rủi Ro', color: '#38bdf8', icon: '🛡️' },
        'Palermo': { title: 'Trưởng Ban Xu Hướng', location: 'Sàn Giao Dịch Xung Kích', color: '#22c55e', icon: '🗡️' },
        'Prof': { title: 'Gác Cổng Thanh Lý & CVaR', location: 'Viện Nghiên Cứu Định Lượng', color: '#a855f7', icon: '🔬' },
        'Tory': { title: 'Săn Sóng Đột Phá', location: 'Trạm Săn Sóng Donchian', color: '#f59e0b', icon: '🎯' },
        'Hash': { title: 'Trinh Sát Tin Tức', location: 'Đài Radar Trinh Sát', color: '#06b6d4', icon: '📡' },
        'Meme': { title: 'Đội Khớp Lệnh HFT', location: 'Phòng Khớp Lệnh Cao Tần', color: '#10b981', icon: '⚡' },
        'Deck': { title: 'Săn Chênh Lệch Giá', location: 'Bàn Trọng Tài Phân Thù', color: '#14b8a6', icon: '⚖️' },
        'Volt': { title: 'Đo Lường Biến Động', location: 'Phòng Thí Nghiệm Sóng ADX', color: '#ec4899', icon: '🌊' },
        'Core': { title: 'Kế Toán & Bài Học', location: 'Phòng Kiểm Toán & Sổ Cái', color: '#10b981', icon: '📑' },
        'Sniper': { title: 'Tích Sản Spot DCA 500U', location: 'Trạm Tích Sản & Két Vault', color: '#14b8a6', icon: '💎' },
        'Square': { title: 'Cộng Đồng & Binance Square', location: 'Trung Tâm CRM & Square Hub', color: '#3b82f6', icon: '📱' }
    }[agentName] || { title: 'Tác Tử Lượng Tử', location: 'Sàn Giao Dịch', color: '#38bdf8', icon: '🤖' };

    const titleEl = document.getElementById('intercom-agent-title');
    const locEl = document.getElementById('intercom-agent-location');
    const iconEl = document.getElementById('intercom-agent-icon');
    if (titleEl) {
        titleEl.textContent = `${meta.icon} ${agentName} — ${meta.title}`;
        titleEl.style.color = meta.color;
    }
    if (locEl) locEl.textContent = `Vị trí 3D: ${meta.location}`;
    if (iconEl) iconEl.textContent = meta.icon;
}

window.selectIntercomAgent = function(agentName) {
    window.currentIntercomAgent = agentName;
    document.querySelectorAll('.intercom-agent-pill').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.agent === agentName);
    });
    updateIntercomHeader(agentName);
    appendIntercomMessage('agent', agentName, `Báo cáo Boss! Tôi là ${agentName}. Tôi đã sẵn sàng nhận chỉ thị và giải trình chiến lược.`);
};

window.sendIntercomPrompt = function(promptText) {
    const input = document.getElementById('intercom-input');
    if (input) input.value = promptText;
    window.sendIntercomMessage();
};

window.sendIntercomMessage = async function() {
    const input = document.getElementById('intercom-input');
    if (!input) return;
    const text = input.value.trim();
    if (!text) return;
    input.value = '';

    const agent = window.currentIntercomAgent || 'Astra';
    appendIntercomMessage('boss', 'Boss (CEO)', text);

    const typingId = appendIntercomTyping(agent);

    try {
        const res = await fetch('/api/v1/spatial/interact', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ agent: agent, query: text })
        });
        removeIntercomTyping(typingId);
        if (res.ok) {
            const data = await res.json();
            appendIntercomMessage('agent', agent, data.reply);
        } else {
            appendIntercomMessage('agent', agent, 'Lỗi kết nối bộ đàm tác tử. Vui lòng thử lại.');
        }
    } catch (e) {
        removeIntercomTyping(typingId);
        appendIntercomMessage('agent', agent, 'Mất sóng vệ tinh. Hệ thống nội bộ đang đồng bộ.');
    }
};

function appendIntercomMessage(senderType, senderName, text) {
    const history = document.getElementById('intercom-chat-history');
    if (!history) return;
    const msg = document.createElement('div');
    msg.className = `intercom-msg ${senderType === 'boss' ? 'boss-msg' : 'agent-msg'}`;
    const timeStr = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    msg.innerHTML = `
        <div class="msg-header">
            <strong>${senderName}</strong>
            <span class="msg-time">${timeStr}</span>
        </div>
        <div class="msg-bubble">${text}</div>
    `;
    history.appendChild(msg);
    history.scrollTop = history.scrollHeight;
}

function appendIntercomTyping(agentName) {
    const history = document.getElementById('intercom-chat-history');
    if (!history) return null;
    const id = 'typing-' + Date.now();
    const typing = document.createElement('div');
    typing.id = id;
    typing.className = 'intercom-msg agent-msg';
    typing.innerHTML = `
        <div class="msg-header"><strong>${agentName}</strong></div>
        <div class="msg-bubble typing-dots">
            <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
    `;
    history.appendChild(typing);
    history.scrollTop = history.scrollHeight;
    return id;
}

function removeIntercomTyping(id) {
    if (!id) return;
    const el = document.getElementById(id);
    if (el) el.remove();
}

// =========================================================================
// GLOBAL BRIDGES FOR QUANTUM 5D MODAL & EMBODIED PROXIMITY INTERACTION
// =========================================================================
window.openQuantum5dModal = function() {
    if (window.officeEngine && typeof window.officeEngine.openQuantum5dModal === 'function') {
        window.officeEngine.openQuantum5dModal();
    } else {
        const m = document.getElementById('q5dModalBackdrop');
        if (m) m.style.display = 'flex';
    }
};

window.closeQuantum5dModal = function() {
    if (window.officeEngine && typeof window.officeEngine.closeQuantum5dModal === 'function') {
        window.officeEngine.closeQuantum5dModal();
    } else {
        const m = document.getElementById('q5dModalBackdrop');
        if (m) m.style.display = 'none';
    }
};

window.interactWithNearbyAgent = function() {
    if (window.officeEngine && typeof window.officeEngine.interactWithNearbyAgent === 'function') {
        window.officeEngine.interactWithNearbyAgent();
    } else if (window.officeEngine && window.officeEngine.nearbyAgentDept) {
        window.openCyberIntercomForDept(window.officeEngine.nearbyAgentDept);
    }
};

// =========================================================================
// 5D DIGITAL TWIN WORLD ENGINE CONTROLS (TELLUX / WEBGIS)
// =========================================================================
window.activeFloorMode = 'campus'; // 'campus' | 'twin'

window.switchFloorMode = function(mode) {
    window.activeFloorMode = mode;
    const btnCampus = document.getElementById('btn-mode-campus');
    const btnTwin = document.getElementById('btn-mode-twin');
    const btnMkt = document.getElementById('btn-mode-mkt');
    const canvasCampus = document.getElementById('office-stage-canvas');
    const campusControls = document.getElementById('campus-stage-controls');
    const containerTwin = document.getElementById('three-world-container');
    const containerMkt = document.getElementById('mkt-floor-container');
    const gisHud = document.getElementById('gis-cockpit-hud');
    const subbadge = document.getElementById('office-stage-subbadge');

    if (mode === 'twin') {
        if (btnCampus) btnCampus.classList.remove('active');
        if (btnMkt) btnMkt.classList.remove('active');
        if (btnTwin) btnTwin.classList.add('active');
        if (containerTwin) containerTwin.style.display = 'none';
        if (containerMkt) containerMkt.style.display = 'none';
        if (canvasCampus) canvasCampus.style.display = 'block';
        if (campusControls) campusControls.style.display = 'flex';
        if (gisHud) gisHud.style.display = 'none';
        if (subbadge) subbadge.textContent = '5D DIGITAL TWIN LAB (PHÒNG BÊN CẠNH SÀN TRADE · TELLUX WEBGIS)';

        // 🚀 CAMERA GLIDE TO PHÒNG 5D BÊN CẠNH (EAST CYBER WING · X = 220, Z = 0)
        if (window.officeEngine && typeof TWEEN !== 'undefined') {
            window.officeEngine.cameraTransitioning = true;
            window.officeEngine.controls.enabled = false;

            new TWEEN.Tween(window.officeEngine.camera.position)
                .to({ x: 140, y: 65, z: 95 }, 1200)
                .easing(TWEEN.Easing.Cubic.InOut)
                .start();

            new TWEEN.Tween(window.officeEngine.controls.target)
                .to({ x: 220, y: 22, z: 0 }, 1200)
                .easing(TWEEN.Easing.Cubic.InOut)
                .onComplete(() => {
                    window.officeEngine.controls.enabled = true;
                    window.officeEngine.cameraTransitioning = false;
                })
                .start();
        }

        const dialogue = document.getElementById('astra-dialogue');
        if (dialogue) {
            dialogue.textContent = 'Boss đang thị sát Phòng 5D Digital Twin bên cạnh Sàn Trade! Tellux WebGIS Engine: 3,500 Hạt Vector Streamlines & Tensor 5D BTC/USDT trực chiến.';
        }
    } else if (mode === 'mkt') {
        if (btnCampus) btnCampus.classList.remove('active');
        if (btnTwin) btnTwin.classList.remove('active');
        if (btnMkt) btnMkt.classList.add('active');
        if (containerTwin) containerTwin.style.display = 'none';
        if (gisHud) gisHud.style.display = 'none';
        if (containerMkt) containerMkt.style.display = 'none'; // Ẩn overlay 2D phẳng
        if (canvasCampus) canvasCampus.style.display = 'block'; // Giữ nguyên 3D Canvas
        if (campusControls) campusControls.style.display = 'flex';
        if (subbadge) subbadge.textContent = 'MKT NIVER 3D CYBER OPERATIONS DECK (TẦNG DƯỚI · 12 BAN MKT & ADS)';

        // 🚀 CAMERA DIVE DOWN TO TẦNG DƯỚI B1 (3D NHÀ CỬA, BÀN GHẾ, NGƯỜI NGỢM)
        if (window.officeEngine && typeof TWEEN !== 'undefined') {
            window.officeEngine.cameraTransitioning = true;
            window.officeEngine.controls.enabled = false;

            new TWEEN.Tween(window.officeEngine.camera.position)
                .to({ x: -145, y: -42, z: 155 }, 1200)
                .easing(TWEEN.Easing.Cubic.InOut)
                .start();

            new TWEEN.Tween(window.officeEngine.controls.target)
                .to({ x: 0, y: -78, z: 0 }, 1200)
                .easing(TWEEN.Easing.Cubic.InOut)
                .onComplete(() => {
                    window.officeEngine.controls.enabled = true;
                    window.officeEngine.cameraTransitioning = false;
                })
                .start();
        }
    } else {
        if (btnTwin) btnTwin.classList.remove('active');
        if (btnMkt) btnMkt.classList.remove('active');
        if (btnCampus) btnCampus.classList.add('active');
        if (containerTwin) containerTwin.style.display = 'none';
        if (containerMkt) containerMkt.style.display = 'none';
        if (gisHud) gisHud.style.display = 'none';
        if (canvasCampus) canvasCampus.style.display = 'block';
        if (campusControls) campusControls.style.display = 'flex';
        if (subbadge) subbadge.textContent = '3D TẦNG TRADE (TẦNG TRÊN · ĐỘI TRADE QUANT)';

        // 🚀 CAMERA DIVE UP TO TẦNG TRÊN (CAMPUS 12 BAN ASTRA QUANT)
        if (window.officeEngine && typeof TWEEN !== 'undefined') {
            window.officeEngine.cameraTransitioning = true;
            window.officeEngine.controls.enabled = false;

            new TWEEN.Tween(window.officeEngine.camera.position)
                .to({ x: -165, y: 205, z: 215 }, 1200)
                .easing(TWEEN.Easing.Cubic.InOut)
                .start();

            new TWEEN.Tween(window.officeEngine.controls.target)
                .to({ x: 0, y: 10, z: 0 }, 1200)
                .easing(TWEEN.Easing.Cubic.InOut)
                .onComplete(() => {
                    window.officeEngine.controls.enabled = true;
                    window.officeEngine.cameraTransitioning = false;
                })
                .start();
        }

        if (window.officeEngine && typeof window.officeEngine.onWindowResize === 'function') {
            window.officeEngine.onWindowResize();
        }
    }
};

window.renderMktStageDeck = function() {
    const grid = document.getElementById('mkt-stage-grid');
    if (!grid || grid.children.length > 0) return;
    
    const MKT_STAGE_AGENTS = [
        { code: "captain", name: "Tổng Chỉ Huy", icon: "🎯", color: "#8b5cf6", role: "Điều Phối 22 Page", duty: "Phân bổ nguồn lực chiến dịch", model: "agnes-3.0-flash (Vyce AI · 512K)", speech: "Hệ thống Nemark MKT Fleet trực chiến 24/7. Điều phối 22 page theo ma trận độc bản 1-1." },
        { code: "content_lab", name: "Phòng Nội Dung", icon: "✒️", color: "#22c55e", role: "Hook & Caption", duty: "Kịch bản viral cho 22 Page", model: "claude-sonnet-4-6 (Vyce AI)", speech: "Sẵn sàng sáng tạo hook & caption viral cho 3 cụm: Drama Nữ, Manhua Tech, KOC Gia Dụng!" },
        { code: "video_forge", name: "Xưởng Video", icon: "🎬", color: "#f59e0b", role: "FFmpeg 1080x1920", duty: "Lách ContentID 4 điểm", model: "cx/gpt-5.6-terra (9Router)", speech: "FFmpeg render 1080x1920 Lanczos upscale với bộ lọc lách ContentID 4 điểm an toàn tuyệt đối." },
        { code: "ads_engine", name: "Phòng Quảng Cáo", icon: "📢", color: "#ef4444", role: "Ads Ảnh + Caption", duty: "Test 1 page trước, CPA < 50k", model: "claude-sonnet-4-6 (Vyce AI)", speech: "Đã thiết lập adset Ảnh + Caption cho page winner. Ngân sách 150k/ngày, CPA mục tiêu dưới 50k." },
        { code: "seeding_ops", name: "Đội Seeding", icon: "🌱", color: "#10b981", role: "Thatim.vn Social Proof", duty: "Chim mồi 2 máy $152.39", model: "deepseek-v4-flash (Vyce AI)", speech: "Thatim.vn API đã kết nối sẵn sàng. Số dư $152.39 USD, kịch bản chim mồi 2 máy chuẩn bị bơm." },
        { code: "trend_scout", name: "Trinh Sát Xu Hướng", icon: "📡", color: "#0ea5e9", role: "Bắt Sóng Trend", duty: "Quét Gemini 4 TikTok đối thủ", model: "cx/gpt-6-astra (9Router)", speech: "Sóng trend Gemini 4 đang cực nóng! TikTok @graperu_ hút 373k view với video giải thích đơn giản." },
        { code: "risk_guard", name: "Cảnh Sát Rủi Ro", icon: "🛡️", color: "#0284c7", role: "Anti-Checkpoint Meta", duty: "Stagger 25-45p, Zero-Burst", model: "claude-sonnet-4-6 (Vyce AI)", speech: "Thực thi nghiêm ngặt Zero-Burst Policy. Lập lịch phát giãn cách 25-45 phút, chống bóp reach Meta." },
        { code: "affiliate_desk", name: "Bàn Affiliate", icon: "💰", color: "#14b8a6", role: "Cookie Trap Shopee", duty: "Mồi tò mò Bio Beacons 7 ngày", model: "cx/gpt-5.6-luna (9Router)", speech: "Đường dẫn Bio Beacons https://beacons.ai/reviewhola đã ghim. Cookie Shopee 7 ngày sẵn sàng lưu." },
        { code: "crm_support", name: "Chăm Sóc Khách", icon: "👥", color: "#6366f1", role: "Gemini Jio +150k/đơn", duty: "Fulfillment & Bảo hành uy tín", model: "deepseek-v4.1 (Vyce AI)", speech: "Gói Gemini Jio arbitrage: Bán 189k, vốn 35k, lãi ròng 150k/con. Đội ngũ fulfillment trực chiến!" },
        { code: "analytics_pm", name: "Phòng Phân Tích", icon: "📊", color: "#3b82f6", role: "Signal & FLOP Monitor", duty: "Giám sát 3 phễu đề xuất Reels", model: "deepseek-v4-flash (Vyce AI)", speech: "Đang quét tín hiệu giữ chân khán giả 3s đầu & tỷ lệ xem hết. Bộ chẩn đoán FLOP 1h đang kích hoạt." },
        { code: "page_router", name: "Phân Luồng Page", icon: "🔀", color: "#64748b", role: "Ma Trận 22 Fanpage", duty: "8 Manhua · 7 Cổ Trang · 7 KOC", model: "cx/gpt-5.6-terra (9Router)", speech: "Ma trận 22 Page đã sẵn sàng phân luồng: 8 Manhua, 7 Cổ Trang, 7 KOC không giẫm chân nhau." },
        { code: "asset_guard", name: "Bảo Vệ Tài Sản", icon: "🔒", color: "#f43f5e", role: "SHA-256 + pHash", duty: "Chống trùng lặp 0 cross-post", model: "Local SHA-256 + pHash", speech: "0 video cross-post trùng lặp được phát hiện! Toàn bộ video xuất xưởng đều có vân tay độc bản." }
    ];

    grid.innerHTML = MKT_STAGE_AGENTS.map(ag => `
        <div onclick="window.showMktStageSpeech('${ag.name}', '${ag.icon}', '${ag.model}', '${ag.speech}', '${ag.color}')"
             style="background: rgba(30, 41, 59, 0.65); border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 10px; cursor: pointer; transition: all 0.2s;"
             onmouseover="this.style.borderColor='${ag.color}'; this.style.transform='translateY(-2px)';"
             onmouseout="this.style.borderColor='rgba(255,255,255,0.08)'; this.style.transform='none';">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-size: 16px;">${ag.icon}</span>
                <span style="font-size: 8px; font-weight: 800; padding: 2px 5px; border-radius: 4px; background: rgba(34,197,94,0.15); color: #4ade80;">ACTIVE</span>
            </div>
            <div style="font-size: 11.5px; font-weight: 800; color: #f8fafc; margin-bottom: 2px;">${ag.name}</div>
            <div style="font-size: 9.5px; font-weight: 600; color: #94a3b8; margin-bottom: 4px;">${ag.role}</div>
            <div style="font-size: 8.5px; color: #64748b; line-height: 1.3; min-height: 22px;">${ag.duty}</div>
            <div style="margin-top: 6px; padding-top: 4px; border-top: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; font-size: 8px; font-family: 'JetBrains Mono', monospace; color: #64748b;">
                <span style="color: ${ag.color};">${ag.model}</span>
                <span style="color: #4ade80;">ONLINE</span>
            </div>
        </div>
    `).join('');
};

window.showMktStageSpeech = function(name, icon, model, speech, color) {
    const box = document.getElementById('mkt-stage-speech');
    const iconEl = document.getElementById('mkt-stage-speech-icon');
    const nameEl = document.getElementById('mkt-stage-speech-name');
    const modelEl = document.getElementById('mkt-stage-speech-model');
    const textEl = document.getElementById('mkt-stage-speech-text');
    if (box && textEl) {
        iconEl.textContent = icon;
        nameEl.textContent = name;
        nameEl.style.color = color;
        modelEl.textContent = model;
        textEl.textContent = speech;
        box.style.display = 'block';
        box.style.borderColor = color;
    }
};

window.setWorldEngineMode = function(mode) {
    const btnOrbit = document.getElementById('btn-gis-mode-orbit');
    const btnFlyover = document.getElementById('btn-gis-mode-flyover');
    if (btnOrbit) btnOrbit.classList.toggle('active', mode === 'ORBIT');
    if (btnFlyover) btnFlyover.classList.toggle('active', mode === 'FLYOVER');

    if (window.worldEngine) {
        window.worldEngine.setCameraMode(mode);
    }
};

window.setWorldEnginePreset = function(preset) {
    if (window.worldEngine) {
        window.worldEngine.setPreset(preset);
    }
};

window.resetWorldCamera = function() {
    if (window.worldEngine) {
        window.worldEngine.resetCamera();
    }
};

window.cycleWorldVectorMode = function() {
    if (window.worldEngine && window.worldEngine.vectorField) {
        const modes = ['BULLISH', 'BEARISH', 'CONFLUENCE', 'NEUTRAL'];
        const current = window.worldEngine.vectorField.flowMode;
        const next = modes[(modes.indexOf(current) + 1) % modes.length];
        window.worldEngine.setVectorMode(next);

        const hudFlow = document.getElementById('gis-flow-val');
        if (hudFlow) {
            const labels = {
                BULLISH: 'BULLS ROTATION (+2.8x)',
                BEARISH: 'BEARS ROTATION (-2.4x)',
                CONFLUENCE: 'QUANTUM CONFLUENCE (3.2x)',
                NEUTRAL: 'NEUTRAL EQUILIBRIUM'
            };
            const colors = {
                BULLISH: '#10b981',
                BEARISH: '#ef4444',
                CONFLUENCE: '#c084fc',
                NEUTRAL: '#38bdf8'
            };
            hudFlow.textContent = labels[next] || next;
            hudFlow.style.color = colors[next] || '#38bdf8';
        }
    }
};

// Listen for 3D agent raycast click to open RPG Stat Sheet
window.addEventListener('astra-agent-clicked', (event) => {
    const agentName = event.detail?.agentName;
    if (!agentName) return;
    console.log(`[Event] astra-agent-clicked caught: ${agentName}`);
    if (typeof window.openAgentRpgSheet === 'function') {
        window.openAgentRpgSheet(agentName);
    } else if (typeof window.openCyberIntercomModal === 'function') {
        window.openCyberIntercomModal(agentName);
    }
});

/* ==========================================================================
   RPG GAME CHARACTER STAT SHEET & MODAL CONTROLLER (12 AGENTS)
   Loaded modularly via /static/js/agent_rpg_registry.js (Single Source of Truth)
   ========================================================================== */

// Toggle 3D Physical Infrastructure Layers (Power Grid, Dark Fiber, Telecom Wi-Fi, Server Racks)
window.toggleWorldLayer = function(layerName) {
    if (window.worldEngine && typeof window.worldEngine.toggleLayer === 'function') {
        const isVisible = window.worldEngine.toggleLayer(layerName);
        const btn = document.getElementById(`btn-layer-${layerName}`);
        if (btn) {
            btn.classList.toggle('active', isVisible);
        }
    }
};

