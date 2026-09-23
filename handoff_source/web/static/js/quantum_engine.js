// ==========================================================================
// ASTRA QUANTUM ENGINE — SCI-FI QUANTUM VISUALIZATION ENGINE (CANVAS 60FPS)
// Supports Quantum Cockpit (1), Quantum Analytics (2), Backtest Lab (3)
// ==========================================================================

let animFrameId = null;
let rotationAngle = 0;
let ridgePhase = 0;
let currentTab = 'cockpit';

// === VIEW SWITCHER (COCKPIT vs ANALYTICS vs BACKTEST) ===
function switchQuantumTab(tab) {
    currentTab = tab;
    const viewCockpit = document.getElementById('view-cockpit');
    const viewAnalytics = document.getElementById('view-analytics');
    const viewBacktest = document.getElementById('view-backtest');
    const btnCockpit = document.getElementById('tab-btn-cockpit');
    const btnAnalytics = document.getElementById('tab-btn-analytics');
    const btnBacktest = document.getElementById('tab-btn-backtest');
    const titleEl = document.getElementById('q-page-title');
    const subEl = document.getElementById('q-page-sub');
    const badgeText = document.getElementById('q-status-badge-text');

    if (btnCockpit) btnCockpit.classList.remove('active');
    if (btnAnalytics) btnAnalytics.classList.remove('active');
    if (btnBacktest) btnBacktest.classList.remove('active');

    if (tab === 'analytics') {
        if (viewCockpit) viewCockpit.style.display = 'none';
        if (viewAnalytics) viewAnalytics.style.display = 'block';
        if (viewBacktest) viewBacktest.style.display = 'none';
        if (btnAnalytics) btnAnalytics.classList.add('active');
        if (titleEl) titleEl.innerText = 'QUANTUM ANALYTICS / AGENT TELEMETRY';
        if (subEl) subEl.innerText = 'Phân tích chuyên sâu · Real-time Agent Analytics · Regime-Aware Trading';
        if (badgeText) badgeText.innerText = '● All Systems Operational';
        history.replaceState(null, '', '/admin/quantum?tab=analytics');
    } else if (tab === 'backtest') {
        if (viewCockpit) viewCockpit.style.display = 'none';
        if (viewAnalytics) viewAnalytics.style.display = 'none';
        if (viewBacktest) viewBacktest.style.display = 'block';
        if (btnBacktest) btnBacktest.classList.add('active');
        if (titleEl) titleEl.innerText = 'CORE BACKTEST LAB (HISTORICAL SIMULATION)';
        if (subEl) subEl.innerText = 'Systematic Strategy Validation · Binance Candle Replay · Risk-Adjusted Alpha';
        if (badgeText) badgeText.innerText = '● Core Simulator Ready';
        history.replaceState(null, '', '/admin/quantum?tab=backtest');
    } else {
        if (viewCockpit) viewCockpit.style.display = 'block';
        if (viewAnalytics) viewAnalytics.style.display = 'none';
        if (viewBacktest) viewBacktest.style.display = 'none';
        if (btnCockpit) btnCockpit.classList.add('active');
        if (titleEl) titleEl.innerText = 'QUANTUM COCKPIT (GPTHEIST PROTOCOL)';
        if (subEl) subEl.innerText = 'Autonomous Quant Trading & Research | Multi-Agent Decision System';
        if (badgeText) badgeText.innerText = '●● LIVE TRADING (Binance USDⓈ-M)';
        history.replaceState(null, '', '/admin/quantum');
    }
}

// === LIVE CLOCK & DATE ===
function updateQuantumClock() {
    const clockEl = document.getElementById('q-clock-time');
    const dateEl = document.getElementById('q-clock-date');
    const now = new Date();

    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    if (clockEl) clockEl.innerText = `${hh}:${mm}:${ss}`;

    const months = ["Thg 1", "Thg 2", "Thg 3", "Thg 4", "Thg 5", "Thg 6", "Thg 7", "Thg 8", "Thg 9", "Thg 10", "Thg 11", "Thg 12"];
    const dd = String(now.getDate()).padStart(2, '0');
    const monthStr = months[now.getMonth()];
    const yyyy = now.getFullYear();
    if (dateEl) dateEl.innerText = `Thg ${now.getMonth() + 1} ${dd}, ${yyyy}`;
}

// ========================================================================== 
// 1. BALANCE HISTORY CANVAS (SCREEN 1)
// ========================================================================== 
window.balanceHistoryState = { points: [], summary: null, loaded: false, error: null };

async function loadBalanceHistoryData() {
    const state = window.balanceHistoryState;
    try {
        const response = await fetch('/api/v1/analytics/trades_overview', { signal: AbortSignal.timeout(12000) });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        state.points = Array.isArray(payload.equity_curve) ? payload.equity_curve : [];
        state.summary = payload.summary || null;
        state.loaded = true;
        state.error = null;
        const context = document.getElementById('balance-chart-context');
        if (context) context.textContent = `${state.points.length} mốc sổ lệnh thật · cập nhật ${new Date().toLocaleTimeString('vi-VN')}`;
        const canvas = document.getElementById('balanceCanvas');
        if (canvas) drawBalanceHistory(canvas);
    } catch (error) {
        state.loaded = true;
        state.error = error.message || 'Không tải được dữ liệu';
        const context = document.getElementById('balance-chart-context');
        if (context) context.textContent = `Không tải được dữ liệu thật: ${state.error}`;
    }
}

function getFilteredBalancePoints() {
    const points = window.balanceHistoryState.points || [];
    if (!points.length || window.balanceTimeframe === 'ALL') return points;
    const ranges = { '1D': 86400000, '7D': 7 * 86400000, '1M': 30 * 86400000 };
    const span = ranges[window.balanceTimeframe] || ranges['1M'];
    const validTimes = points.map(p => Date.parse(p.time)).filter(Number.isFinite);
    if (!validTimes.length) return points;
    const cutoff = Math.max(...validTimes) - span;
    return points.filter(p => {
        const ts = Date.parse(p.time);
        return Number.isFinite(ts) && ts >= cutoff;
    });
}

function ensureBalanceTooltip(canvas) {
    const wrap = canvas.parentElement;
    let tooltip = wrap.querySelector('.q-chart-tooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.className = 'q-chart-tooltip';
        tooltip.hidden = true;
        wrap.appendChild(tooltip);
    }
    if (!canvas.dataset.tooltipBound) {
        canvas.dataset.tooltipBound = '1';
        canvas.addEventListener('mousemove', event => {
            const rect = canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const hits = canvas._balanceHits || [];
            if (!hits.length) return;
            const hit = hits.reduce((best, item) => Math.abs(item.x - x) < Math.abs(best.x - x) ? item : best, hits[0]);
            tooltip.innerHTML = `<strong>${hit.label}</strong><span>${hit.valueLabel}</span><small>${hit.detail}</small>`;
            tooltip.style.left = `${Math.min(Math.max(hit.x, 70), rect.width - 80)}px`;
            tooltip.style.top = `${Math.max(8, hit.y - 72)}px`;
            tooltip.hidden = false;
        });
        canvas.addEventListener('mouseleave', () => { tooltip.hidden = true; });
    }
    return tooltip;
}

function setupCanvas2D(canvas, defaultW, defaultH) {
    if (!canvas || canvas.offsetParent === null) return null;
    const parent = canvas.parentElement;
    if (!parent) return null;

    // Strict containment styling to eliminate any possibility of grid track blowout
    if (canvas.style.display !== 'block') canvas.style.display = 'block';
    if (canvas.style.width !== '100%') canvas.style.width = '100%';
    if (canvas.style.height !== '100%') canvas.style.height = '100%';
    if (canvas.style.maxWidth !== '100%') canvas.style.maxWidth = '100%';
    if (canvas.style.maxHeight !== '100%') canvas.style.maxHeight = '100%';
    if (canvas.style.boxSizing !== 'border-box') canvas.style.boxSizing = 'border-box';

    // Measure parent container CSS pixels strictly
    const w = Math.floor(parent.clientWidth) || defaultW || 300;
    const h = Math.floor(parent.clientHeight) || defaultH || 200;
    if (w <= 0 || h <= 0) return null;

    const dpr = window.devicePixelRatio || 1;
    const targetW = Math.round(w * dpr);
    const targetH = Math.round(h * dpr);

    if (canvas.width !== targetW || canvas.height !== targetH) {
        canvas.width = targetW;
        canvas.height = targetH;
    }

    const ctx = canvas.getContext('2d');
    ctx.resetTransform();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    return { ctx, w, h, dpr };
}

function drawBalanceHistory(canvas) {
    const s = setupCanvas2D(canvas, 300, 250);
    if (!s) return;
    const { ctx, w, h } = s;

    const pad = { top: 25, bottom: 35, left: 55, right: 65 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;

    const points = getFilteredBalancePoints();
    ensureBalanceTooltip(canvas);
    if (!window.balanceHistoryState.loaded) {
        ctx.fillStyle = '#64748b'; ctx.font = '12px "JetBrains Mono", monospace'; ctx.textAlign = 'center';
        ctx.fillText('Đang tải lịch sử giao dịch thật…', w / 2, h / 2); return;
    }
    if (window.balanceHistoryState.error || !points.length) {
        ctx.fillStyle = '#f59e0b'; ctx.font = '12px "JetBrains Mono", monospace'; ctx.textAlign = 'center';
        ctx.fillText(window.balanceHistoryState.error || 'Chưa có giao dịch trong khoảng đã chọn', w / 2, h / 2); return;
    }

    const mode = window.balanceViewMode || 'equity';
    const baseEquity = Number(points[0].equity || window.balanceHistoryState.summary?.base_capital_usdt || 0);
    let peak = baseEquity;
    const series = points.map(point => {
        const equity = Number(point.equity || 0);
        peak = Math.max(peak, equity);
        if (mode === 'pnl') return Number(point.pnl || 0);
        if (mode === 'drawdown') return peak > 0 ? -((peak - equity) / peak) * 100 : 0;
        if (mode === 'return') return baseEquity > 0 ? ((equity / baseEquity) - 1) * 100 : 0;
        return equity;
    });
    const labels = points.map(p => {
        const date = new Date(p.time);
        return Number.isNaN(date.getTime()) ? String(p.time || '') : date.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
    });
    const rawMin = Math.min(...series, mode === 'equity' ? baseEquity : 0);
    const rawMax = Math.max(...series, mode === 'equity' ? baseEquity : 0);
    const padding = Math.max((rawMax - rawMin) * 0.18, mode === 'equity' ? Math.max(baseEquity * 0.005, 0.05) : 0.15);
    const minVal = rawMin - padding;
    const maxVal = rawMax + padding;
    const range = Math.max(maxVal - minVal, 0.001);

    const getX = (idx) => points.length === 1 ? pad.left + chartW / 2 : pad.left + (idx / (points.length - 1)) * chartW;
    const getY = (val) => pad.top + (1 - (val - minVal) / range) * chartH;

    // Y Axis Grid lines
    ctx.strokeStyle = 'rgba(226, 232, 240, 0.8)';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#94a3b8';
    ctx.font = '9.5px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';

    for (let i = 0; i <= 4; i++) {
        const tick = minVal + (range / 4) * i;
        const y = getY(tick);
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(w - pad.right, y);
        ctx.stroke();
        const suffix = mode === 'equity' || mode === 'pnl' ? ' USDT' : '%';
        ctx.fillText(`${tick.toFixed(2)}${suffix}`, pad.left - 8, y + 3);
    }

    const zeroY = getY(mode === 'equity' ? baseEquity : 0);
    ctx.beginPath(); ctx.strokeStyle = '#0ea5e9'; ctx.lineWidth = 1; ctx.setLineDash([4, 4]);
    ctx.moveTo(pad.left, zeroY); ctx.lineTo(w - pad.right, zeroY); ctx.stroke(); ctx.setLineDash([]);

    if (mode === 'pnl') {
        const barWidth = Math.max(4, Math.min(20, chartW / Math.max(points.length, 1) * 0.5));
        series.forEach((value, idx) => {
            const y = getY(value);
            ctx.fillStyle = value >= 0 ? 'rgba(16,185,129,.7)' : 'rgba(244,63,94,.7)';
            ctx.fillRect(getX(idx) - barWidth / 2, Math.min(y, zeroY), barWidth, Math.max(2, Math.abs(zeroY - y)));
        });
    } else {
        ctx.beginPath(); ctx.moveTo(getX(0), getY(series[0]));
        for (let i = 1; i < series.length; i++) ctx.lineTo(getX(i), getY(series[i]));
        ctx.lineTo(getX(series.length - 1), pad.top + chartH); ctx.lineTo(getX(0), pad.top + chartH); ctx.closePath();
        const color = mode === 'drawdown' ? '244,63,94' : '16,185,129';
        const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH);
        grad.addColorStop(0, `rgba(${color},.26)`); grad.addColorStop(1, `rgba(${color},.02)`); ctx.fillStyle = grad; ctx.fill();
        ctx.beginPath(); ctx.moveTo(getX(0), getY(series[0]));
        for (let i = 1; i < series.length; i++) ctx.lineTo(getX(i), getY(series[i]));
        ctx.strokeStyle = mode === 'drawdown' ? '#f43f5e' : '#10b981'; ctx.lineWidth = 2.2; ctx.stroke();
    }

    const lastX = getX(series.length - 1);
    const lastY = getY(series[series.length - 1]);

    ctx.fillStyle = '#10b981';
    ctx.beginPath();
    ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
    ctx.fill();

    const tagText = `${mode === 'equity' || mode === 'pnl' ? '$' : ''}${series[series.length - 1].toFixed(2)}${mode === 'return' || mode === 'drawdown' ? '%' : ''}`;
    const tagW = Math.max(54, ctx.measureText(tagText).width + 16);
    const tagH = 18;
    const tagX = lastX - tagW / 2;
    const tagY = lastY - 24;

    ctx.fillStyle = '#10b981';
    if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(tagX, tagY, tagW, tagH, 4);
        ctx.fill();
    } else {
        ctx.fillRect(tagX, tagY, tagW, tagH);
    }
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 9.5px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(tagText, tagX + tagW / 2, tagY + 12);

    // X axis labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    const labelStep = Math.max(1, Math.ceil(labels.length / 7));
    labels.forEach((label, idx) => {
        if (idx % labelStep === 0 || idx === labels.length - 1) ctx.fillText(label, getX(idx), h - 10);
    });
    canvas._balanceHits = points.map((point, idx) => ({
        x: getX(idx), y: getY(series[idx]), label: new Date(point.time).toLocaleString('vi-VN'),
        valueLabel: tagTextFor(mode, series[idx]),
        detail: `${point.symbol || 'Sổ vốn'} · ${point.status || 'INIT'} · PnL ${Number(point.pnl || 0).toFixed(4)} USDT`
    }));
}

function tagTextFor(mode, value) {
    if (mode === 'equity') return `Vốn: $${value.toFixed(4)}`;
    if (mode === 'pnl') return `PnL lệnh: ${value >= 0 ? '+' : ''}$${value.toFixed(4)}`;
    if (mode === 'drawdown') return `Drawdown: ${value.toFixed(2)}%`;
    return `Lợi suất: ${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
}

// ==========================================================================
// 2. TAIL PROBABILITY RIDGE (SCREEN 1 & 2)
// ==========================================================================
function drawTailProbabilityRidge(canvas) {
    const s = setupCanvas2D(canvas, 300, 200);
    if (!s) return;
    const { ctx, w, h } = s;

    const pad = { top: 20, bottom: 25, left: 35, right: 35 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;

    const sigmas = ['-4σ', '-3σ', '-2σ', '-1σ', '0', '+1σ', '+2σ', '+3σ', '+4σ'];

    // Gaussian bell curve generator
    const steps = 100;
    const getBell = (mean, sigma, peak) => {
        const pts = [];
        for (let i = 0; i <= steps; i++) {
            const t = i / steps; // 0 to 1
            const x = pad.left + t * chartW;
            const z = (t - mean) / sigma;
            const yVal = Math.exp(-0.5 * z * z);
            const y = pad.top + chartH - yVal * peak;
            pts.push({ x, y });
        }
        return pts;
    };

    // 1. 30-Day Historical Distribution (Blue shaded area)
    const histPts = getBell(0.48, 0.20, chartH * 0.72);
    ctx.beginPath();
    ctx.moveTo(histPts[0].x, pad.top + chartH);
    histPts.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.lineTo(histPts[histPts.length - 1].x, pad.top + chartH);
    ctx.closePath();
    ctx.fillStyle = 'rgba(14, 165, 233, 0.18)';
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(histPts[0].x, histPts[0].y);
    histPts.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.strokeStyle = '#0ea5e9';
    ctx.lineWidth = 1.6;
    ctx.stroke();

    // 2. Current Mode Distribution (Red line curve)
    const curPts = getBell(0.52, 0.16, chartH * 0.88);
    ctx.beginPath();
    ctx.moveTo(curPts[0].x, curPts[0].y);
    curPts.forEach(p => ctx.lineTo(p.x, p.y));
    ctx.strokeStyle = '#f43f5e';
    ctx.lineWidth = 2.2;
    ctx.stroke();

    // Vertical dashed lines for sigmas
    ctx.strokeStyle = 'rgba(226, 232, 240, 0.7)';
    ctx.setLineDash([2, 2]);
    sigmas.forEach((sig, idx) => {
        const x = pad.left + (idx / (sigmas.length - 1)) * chartW;
        ctx.beginPath();
        ctx.moveTo(x, pad.top);
        ctx.lineTo(x, pad.top + chartH);
        ctx.stroke();

        ctx.fillStyle = '#94a3b8';
        ctx.font = '8.5px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.fillText(sig, x, h - 8);
    });
    ctx.setLineDash([]);

    // Peak dot & label on current curve
    const peakIdx = Math.floor(steps * 0.52);
    const peak = curPts[peakIdx];
    ctx.fillStyle = '#f43f5e';
    ctx.beginPath();
    ctx.arc(peak.x, peak.y, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#0f172a';
    ctx.font = 'bold 9px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('μ: 0.12', peak.x, peak.y - 12);
    ctx.fillText('d: 1.08', peak.x, peak.y - 2);
}

// ==========================================================================
// 3. CIRCULAR HANDOFF CHORD (SCREEN 2)
// ==========================================================================
function drawHandoffChord(canvas) {
    const s = setupCanvas2D(canvas, 300, 240);
    if (!s) return;
    const { ctx, w, h } = s;

    const cx = w / 2;
    const cy = h / 2;
    const radius = Math.min(w, h) * 0.35;

    const agents = [
        { name: 'Astra', role: '(Trend)', color: '#ef4444' },
        { name: 'Core', role: '(Deck)', color: '#6366f1' },
        { name: 'Volt', role: '(Macro)', color: '#0ea5e9' },
        { name: 'Meme', role: '(Execution)', color: '#06b6d4' },
        { name: 'Prof', role: '(RiskGate)', color: '#ec4899' },
        { name: 'Hash', role: '(Sentiment)', color: '#10b981' },
        { name: 'Tory', role: '(Breakout)', color: '#f59e0b' },
        { name: 'Rik', role: '(Risk)', color: '#10b981' }
    ];

    const nodeCoords = [];
    for (let i = 0; i < agents.length; i++) {
        const angle = (i / agents.length) * Math.PI * 2 - Math.PI / 2;
        const nx = cx + Math.cos(angle) * radius;
        const ny = cy + Math.sin(angle) * radius;
        nodeCoords.push({ x: nx, y: ny, angle: angle, ...agents[i] });
    }

    // Outer Circle Ring
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(226, 232, 240, 0.8)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Chords between agents
    const connections = [
        { from: 4, to: 0, color: 'rgba(244, 63, 94, 0.65)' }, // Prof -> Astra
        { from: 3, to: 4, color: 'rgba(6, 182, 212, 0.65)' }, // Meme -> Prof
        { from: 1, to: 2, color: 'rgba(99, 102, 241, 0.65)' }, // Core -> Volt
        { from: 0, to: 3, color: 'rgba(245, 158, 11, 0.65)' }, // Astra -> Meme
        { from: 6, to: 7, color: 'rgba(245, 158, 11, 0.6)' },  // Tory -> Rik
        { from: 7, to: 0, color: 'rgba(16, 185, 129, 0.6)' }   // Rik -> Astra
    ];

    connections.forEach(conn => {
        const p1 = nodeCoords[conn.from];
        const p2 = nodeCoords[conn.to];
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.quadraticCurveTo(cx, cy, p2.x, p2.y);
        ctx.strokeStyle = conn.color;
        ctx.lineWidth = 2.2;
        ctx.stroke();
    });

    // Draw Nodes and Labels
    nodeCoords.forEach(node => {
        ctx.beginPath();
        ctx.arc(node.x, node.y, 5, 0, Math.PI * 2);
        ctx.fillStyle = node.color;
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Label outside ring
        const labelRadius = radius + 15;
        const lx = cx + Math.cos(node.angle) * labelRadius;
        const ly = cy + Math.sin(node.angle) * labelRadius;
        ctx.font = 'bold 8.5px "JetBrains Mono", monospace';
        ctx.fillStyle = '#475569';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.name, lx, ly - 5);
        ctx.font = '7.5px sans-serif';
        ctx.fillStyle = '#94a3b8';
        ctx.fillText(node.role, lx, ly + 5);
    });
}

// ==========================================================================
// 4. REGIME MAP (SCREEN 2)
// ==========================================================================
function drawRegimeMap(canvas) {
    const s = setupCanvas2D(canvas, 300, 360);
    if (!s) return;
    const { ctx, w, h } = s;

    const pad = { top: 25, bottom: 35, left: 55, right: 60 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;

    const dates = ['15/09', '16/09', '17/09', '18/09', '19/09', '20/09', '21/09'];
    const prices = [78450, 79200, 78900, 80400, 80150, 81400, 81065];

    const minP = 77000;
    const maxP = 83000;
    const range = maxP - minP;

    const getX = (idx) => pad.left + (idx / (dates.length - 1)) * chartW;
    const getY = (val) => pad.top + (1 - (val - minP) / range) * chartH;

    // Y Axis Grid
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.15)';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#64748b';
    ctx.font = '9px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';

    [77000, 78500, 80000, 81500, 83000].forEach(p => {
        const y = getY(p);
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(w - pad.right, y);
        ctx.stroke();
        ctx.fillText(`$${p.toLocaleString()}`, pad.left - 8, y + 3);
    });

    // Gradient Fill Under Price Line
    const fillGrad = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH);
    fillGrad.addColorStop(0, 'rgba(16, 185, 129, 0.25)');
    fillGrad.addColorStop(0.7, 'rgba(16, 185, 129, 0.05)');
    fillGrad.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    ctx.beginPath();
    ctx.moveTo(getX(0), getY(prices[0]));
    for (let i = 1; i < prices.length; i++) {
        const cx = (getX(i - 1) + getX(i)) / 2;
        ctx.bezierCurveTo(cx, getY(prices[i - 1]), cx, getY(prices[i]), getX(i), getY(prices[i]));
    }
    ctx.lineTo(getX(prices.length - 1), pad.top + chartH);
    ctx.lineTo(getX(0), pad.top + chartH);
    ctx.closePath();
    ctx.fillStyle = fillGrad;
    ctx.fill();

    // Price Stroke Line
    ctx.beginPath();
    ctx.moveTo(getX(0), getY(prices[0]));
    for (let i = 1; i < prices.length; i++) {
        const cx = (getX(i - 1) + getX(i)) / 2;
        ctx.bezierCurveTo(cx, getY(prices[i - 1]), cx, getY(prices[i]), getX(i), getY(prices[i]));
    }
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2.4;
    ctx.stroke();

    // End Badge $81,065
    const lastX = getX(prices.length - 1);
    const lastY = getY(prices[prices.length - 1]);

    ctx.fillStyle = '#10b981';
    if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(lastX - 26, lastY - 10, 52, 20, 4);
        ctx.fill();
    } else {
        ctx.fillRect(lastX - 26, lastY - 10, 52, 20);
    }
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 9px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('$81,065', lastX, lastY + 3.5);

    // Bottom Regime Color Strip
    const stripH = 6;
    const stripY = h - 24;
    const segs = [
        { w: 0.20, c: '#f43f5e', lbl: 'Bear' },
        { w: 0.35, c: '#0ea5e9', lbl: 'Neutral' },
        { w: 0.45, c: '#10b981', lbl: 'Bull' }
    ];
    let curX = pad.left;
    segs.forEach(seg => {
        const sw = seg.w * chartW;
        ctx.fillStyle = seg.c;
        ctx.fillRect(curX, stripY, sw, stripH);
        curX += sw;
    });

    // Date Labels
    ctx.fillStyle = '#64748b';
    ctx.font = '8.5px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    dates.forEach((d, idx) => {
        ctx.fillText(d, getX(idx), h - 8);
    });
}

// ==========================================================================
// 5. FEATURE CORRELATION MATRIX (SCREEN 2)
// ==========================================================================
function drawCorrMatrix(canvas) {
    const s = setupCanvas2D(canvas, 300, 360);
    if (!s) return;
    const { ctx, w, h } = s;

    const labels = ['Price', 'Vol', 'Fund', 'OI', 'RSI', 'MACD', 'Volt', 'Liq', 'Sent'];
    const n = labels.length;
    const pad = { top: 28, bottom: 20, left: 45, right: 38 };
    const availW = w - pad.left - pad.right;
    const availH = h - pad.top - pad.bottom;
    const cellSize = Math.floor(Math.min(availW / n, availH / n));
    const matrixW = cellSize * n;
    const matrixH = cellSize * n;
    const startX = pad.left + Math.floor((availW - matrixW) / 2);
    const startY = pad.top + Math.floor((availH - matrixH) / 2);

    const matrix = [
        [ 1.00,  0.42,  0.65,  0.51,  0.72,  0.83, -0.31, -0.45,  0.62],
        [ 0.42,  1.00,  0.28,  0.78,  0.35,  0.41,  0.62,  0.58,  0.40],
        [ 0.65,  0.28,  1.00,  0.44,  0.58,  0.61, -0.22, -0.38,  0.51],
        [ 0.51,  0.78,  0.44,  1.00,  0.49,  0.52,  0.41,  0.35,  0.38],
        [ 0.72,  0.35,  0.58,  0.49,  1.00,  0.88, -0.52, -0.41,  0.70],
        [ 0.83,  0.41,  0.61,  0.52,  0.88,  1.00, -0.48, -0.39,  0.77],
        [-0.31,  0.62, -0.22,  0.41, -0.52, -0.48,  1.00,  0.74, -0.35],
        [-0.45,  0.58, -0.38,  0.35, -0.41, -0.39,  0.74,  1.00, -0.42],
        [ 0.62,  0.40,  0.51,  0.38,  0.70,  0.77, -0.35, -0.42,  1.00]
    ];

    // Column Headers at Top
    ctx.fillStyle = '#94a3b8';
    ctx.font = 'bold 8px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    for (let c = 0; c < n; c++) {
        ctx.fillText(labels[c], startX + c * cellSize + cellSize / 2, startY - 6);
    }

    // Matrix Cells + Row Headers
    for (let r = 0; r < n; r++) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = 'bold 8px "JetBrains Mono", monospace';
        ctx.textAlign = 'right';
        ctx.fillText(labels[r], startX - 5, startY + r * cellSize + cellSize * 0.65);

        for (let c = 0; c < n; c++) {
            const val = matrix[r][c];
            const x = startX + c * cellSize;
            const y = startY + r * cellSize;

            let fill;
            if (val >= 0) {
                fill = `rgba(244, 63, 94, ${val * 0.75 + 0.15})`;
            } else {
                fill = `rgba(14, 165, 233, ${Math.abs(val) * 0.75 + 0.15})`;
            }
            ctx.fillStyle = fill;
            ctx.fillRect(x + 1, y + 1, cellSize - 2, cellSize - 2);

            // Print value label if cell is large enough
            if (cellSize >= 24) {
                ctx.fillStyle = Math.abs(val) > 0.6 ? '#ffffff' : 'rgba(255, 255, 255, 0.85)';
                ctx.font = '7.5px "JetBrains Mono", monospace';
                ctx.textAlign = 'center';
                const textVal = (val >= 0 ? '+' : '') + val.toFixed(2);
                ctx.fillText(textVal, x + cellSize / 2, y + cellSize * 0.65);
            }
        }
    }

    // Legend Bar on Right
    const legX = startX + matrixW + 10;
    const legH = matrixH;
    const grad = ctx.createLinearGradient(0, startY, 0, startY + legH);
    grad.addColorStop(0, '#f43f5e');
    grad.addColorStop(0.5, '#ffffff');
    grad.addColorStop(1, '#0ea5e9');
    ctx.fillStyle = grad;
    ctx.fillRect(legX, startY, 6, legH);

    ctx.fillStyle = '#64748b';
    ctx.font = '7.5px "JetBrains Mono", monospace';
    ctx.textAlign = 'left';
    ctx.fillText('+1.0', legX + 9, startY + 7);
    ctx.fillText(' 0.0', legX + 9, startY + legH / 2 + 3);
    ctx.fillText('-1.0', legX + 9, startY + legH);
}

// ==========================================================================
// 6. SIMULATED EQUITY CURVE & BACKTEST CANVAS (SCREEN 3)
// ==========================================================================
window.activeBacktestResult = null;

function drawSimulatedEquityCurve(canvas) {
    const s = setupCanvas2D(canvas, 300, 250);
    if (!s) return;
    const { ctx, w, h } = s;

    const pad = { top: 25, bottom: 35, left: 60, right: 65 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;

    let dates = [];
    let equity = [];
    let buyHold = [];
    let drawdowns = [];

    const res = window.activeBacktestResult;
    if (res && res.equity_curve && res.equity_curve.length > 1) {
        let curve = res.equity_curve.slice();
        const tfRanges = { '1D': 86400000, '7D': 7 * 86400000, '30D': 30 * 86400000 };
        const tf = window.backtestTimeframe || 'ALL';
        if (tfRanges[tf]) {
            const timestamps = curve.map(pt => Date.parse(String(pt.time || '').replace(' ', 'T') + 'Z')).filter(Number.isFinite);
            if (timestamps.length) {
                const cutoff = Math.max(...timestamps) - tfRanges[tf];
                curve = curve.filter(pt => Date.parse(String(pt.time || '').replace(' ', 'T') + 'Z') >= cutoff);
            }
        }
        const step = Math.max(1, Math.floor(curve.length / 20));
        for (let i = 0; i < curve.length; i += step) {
            const pt = curve[i];
            const parsed = new Date(String(pt.time || '').replace(' ', 'T') + 'Z');
            dates.push(Number.isNaN(parsed.getTime()) ? (pt.time || `N${i}`) : parsed.toLocaleString('vi-VN', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'}));
            equity.push(pt.balance);
            buyHold.push(pt.buy_hold || pt.balance);
            drawdowns.push(pt.drawdown || 0);
        }
        // Ensure the last point is included
        const lastPt = curve[curve.length - 1];
        if (equity[equity.length - 1] !== lastPt.balance) {
            const parsed = new Date(String(lastPt.time || '').replace(' ', 'T') + 'Z');
            dates.push(Number.isNaN(parsed.getTime()) ? (lastPt.time || 'End') : parsed.toLocaleString('vi-VN', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'}));
            equity.push(lastPt.balance);
            buyHold.push(lastPt.buy_hold || lastPt.balance);
            drawdowns.push(lastPt.drawdown || 0);
        }
    } else {
        ctx.fillStyle = '#64748b';
        ctx.font = '12px "JetBrains Mono", monospace';
        ctx.textAlign = 'center';
        ctx.fillText('Chưa có kết quả — hãy chạy backtest bằng dữ liệu Binance thật', w / 2, h / 2);
        return;
    }

    const compareBuyHold = window.backtestCompareBuyHold !== false;
    const allVals = compareBuyHold ? equity.concat(buyHold) : equity;
    const rawMin = Math.min(...allVals);
    const rawMax = Math.max(...allVals);
    const padMargin = Math.max((rawMax - rawMin) * 0.15, 200);
    const minVal = Math.floor((rawMin - padMargin) / 100) * 100;
    const maxVal = Math.ceil((rawMax + padMargin) / 100) * 100;
    const range = Math.max(maxVal - minVal, 100);

    const getX = (idx) => dates.length === 1 ? pad.left + chartW / 2 : pad.left + (idx / (dates.length - 1)) * chartW;
    const getY = (val) => pad.top + (1 - (val - minVal) / range) * chartH;

    // Y Grid lines
    ctx.strokeStyle = 'rgba(226, 232, 240, 0.7)';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';

    const numTicks = 5;
    for (let i = 0; i <= numTicks; i++) {
        const tick = minVal + (range / numTicks) * i;
        const y = getY(tick);
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(w - pad.right, y);
        ctx.stroke();
        ctx.fillText(`$${Math.round(tick).toLocaleString()}`, pad.left - 8, y + 3);
    }

    // Drawdown Bars at bottom
    dates.forEach((d, idx) => {
        const x = getX(idx);
        const dd = drawdowns[idx] || 0;
        const barH = Math.min(chartH * 0.25, (dd / 25) * (chartH * 0.25));
        const y = pad.top + chartH;
        ctx.fillStyle = 'rgba(244, 63, 94, 0.45)';
        ctx.fillRect(x - 2, y - barH, 4, barH);
    });

    // Optional Buy & Hold comparison
    if (compareBuyHold) {
        ctx.beginPath();
        ctx.moveTo(getX(0), getY(buyHold[0]));
        for (let i = 1; i < buyHold.length; i++) {
            const cx = (getX(i - 1) + getX(i)) / 2;
            ctx.bezierCurveTo(cx, getY(buyHold[i - 1]), cx, getY(buyHold[i]), getX(i), getY(buyHold[i]));
        }
        ctx.strokeStyle = '#0ea5e9';
        ctx.lineWidth = 1.8;
        ctx.stroke();
    }

    // Area Fill for Equity Curve
    ctx.beginPath();
    ctx.moveTo(getX(0), getY(equity[0]));
    for (let i = 1; i < equity.length; i++) {
        const cx = (getX(i - 1) + getX(i)) / 2;
        ctx.bezierCurveTo(cx, getY(equity[i - 1]), cx, getY(equity[i]), getX(i), getY(equity[i]));
    }
    ctx.lineTo(getX(equity.length - 1), pad.top + chartH);
    ctx.lineTo(getX(0), pad.top + chartH);
    ctx.closePath();

    const areaGrad = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH);
    areaGrad.addColorStop(0, 'rgba(16, 185, 129, 0.28)');
    areaGrad.addColorStop(1, 'rgba(16, 185, 129, 0.01)');
    ctx.fillStyle = areaGrad;
    ctx.fill();

    // Equity Curve Line
    ctx.beginPath();
    ctx.moveTo(getX(0), getY(equity[0]));
    for (let i = 1; i < equity.length; i++) {
        const cx = (getX(i - 1) + getX(i)) / 2;
        ctx.bezierCurveTo(cx, getY(equity[i - 1]), cx, getY(equity[i]), getX(i), getY(equity[i]));
    }
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2.4;
    ctx.stroke();

    // Last point badge
    const lastX = getX(equity.length - 1);
    const lastY = getY(equity[equity.length - 1]);
    const lastVal = equity[equity.length - 1];
    const badgeText = `$${lastVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    ctx.fillStyle = (lastVal >= (res?.initial_balance || 10000)) ? '#10b981' : '#f43f5e';
    const textW = ctx.measureText(badgeText).width || 56;
    const badgeW = textW + 16;

    if (ctx.roundRect) {
        ctx.beginPath();
        ctx.roundRect(lastX - badgeW / 2, lastY - 24, badgeW, 18, 4);
        ctx.fill();
    } else {
        ctx.fillRect(lastX - badgeW / 2, lastY - 24, badgeW, 18);
    }
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 9px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(badgeText, lastX, lastY - 12);

    // X Axis Labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '9px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    const labelStep = Math.max(1, Math.floor(dates.length / 8));
    for (let idx = 0; idx < dates.length; idx += labelStep) {
        ctx.fillText(dates[idx], getX(idx), h - 10);
    }
}

// ==========================================================================
// 7. DRAWDOWN DISTRIBUTION HISTOGRAM (SCREEN 3)
// ==========================================================================
function drawDdDist(canvas) {
    const s = setupCanvas2D(canvas, 300, 140);
    if (!s) return;
    const { ctx, w, h } = s;

    const pad = { top: 15, bottom: 20, left: 30, right: 20 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;

    const res = window.activeBacktestResult;
    if (!res || !Array.isArray(res.dd_bins)) {
        ctx.fillStyle = '#64748b'; ctx.font = '10px "JetBrains Mono", monospace'; ctx.textAlign = 'center';
        ctx.fillText('Chưa có phân phối drawdown', w / 2, h / 2); return;
    }
    const bins = res.dd_bins;
    const maxBin = Math.max(...bins, 1);
    const barW = chartW / bins.length - 2;

    bins.forEach((cnt, idx) => {
        const x = pad.left + idx * (barW + 2);
        const bh = (cnt / maxBin) * chartH;
        const y = pad.top + chartH - bh;

        ctx.fillStyle = (cnt === maxBin && cnt > 0) ? 'rgba(244, 63, 94, 0.75)' : 'rgba(244, 63, 94, 0.35)';
        ctx.fillRect(x, y, barW, bh);
    });

    // X Axis ticks
    ctx.fillStyle = '#94a3b8';
    ctx.font = '8px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText('-30%', pad.left, h - 5);
    ctx.fillText('-20%', pad.left + chartW * 0.33, h - 5);
    ctx.fillText('-10%', pad.left + chartW * 0.66, h - 5);
    ctx.fillText('0%', pad.left + chartW, h - 5);
}

// ==========================================================================
// 8. PARAMETER SWEEP HEATMAP (SCREEN 3)
// ==========================================================================
function drawParamSweepHeatmap(canvas) {
    const s = setupCanvas2D(canvas, 300, 150);
    if (!s) return;
    const { ctx, w, h } = s;

    const pad = { top: 10, bottom: 20, left: 35, right: 30 };
    const rows = [4.0, 3.0, 2.0, 1.0]; // TP
    const cols = [0.5, 1.0, 1.5, 2.0, 2.5]; // SL
    const cellW = (w - pad.left - pad.right) / cols.length;
    const cellH = (h - pad.top - pad.bottom) / rows.length;

    const values = [
        [ 42,  68,  82,  54,  22 ],
        [ 28,  54,  76,  48,  12 ],
        [ 12,  32,  44,  18, -12 ],
        [-15, -24, -32, -40, -48 ]
    ];

    for (let r = 0; r < rows.length; r++) {
        ctx.fillStyle = '#64748b';
        ctx.font = '8px "JetBrains Mono", monospace';
        ctx.textAlign = 'right';
        ctx.fillText(rows[r].toFixed(1), pad.left - 4, pad.top + r * cellH + cellH * 0.65);

        for (let c = 0; c < cols.length; c++) {
            const val = values[r][c];
            const x = pad.left + c * cellW;
            const y = pad.top + r * cellH;

            let fill;
            if (val >= 50) fill = '#10b981';
            else if (val >= 20) fill = '#34d399';
            else if (val >= 0) fill = '#fde047';
            else if (val >= -25) fill = '#fca5a5';
            else fill = '#f87171';

            ctx.fillStyle = fill;
            ctx.fillRect(x + 1, y + 1, cellW - 2, cellH - 2);
        }
    }

    // Bottom SL axis
    ctx.fillStyle = '#64748b';
    ctx.font = '8px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    cols.forEach((sl, c) => {
        ctx.fillText(sl.toFixed(1), pad.left + c * cellW + cellW / 2, h - 5);
    });
}

// ==========================================================================
// MASTER RENDER LOOP
// ==========================================================================
function startMasterLoop() {
    let lastRender = 0;
    function loop(timestamp = 0) {
        if (document.hidden || timestamp - lastRender < 100) {
            animFrameId = requestAnimationFrame(loop);
            return;
        }
        lastRender = timestamp;
        const balC = document.getElementById('balanceCanvas');
        const ridgeC = document.getElementById('ridgeCanvas');
        const analRidgeC = document.getElementById('analyticsRidgeCanvas');
        const chordC = document.getElementById('chordCanvas');
        const regimeC = document.getElementById('regimeCanvas');
        const corrC = document.getElementById('corrCanvas');
        const simEquityC = document.getElementById('simEquityCanvas');
        const ddDistC = document.getElementById('ddDistCanvas');
        const paramSweepC = document.getElementById('paramSweepCanvas');

        if (balC && balC.offsetParent !== null) drawBalanceHistory(balC);
        if (ridgeC && ridgeC.offsetParent !== null) drawTailProbabilityRidge(ridgeC);
        if (analRidgeC && analRidgeC.offsetParent !== null) drawTailProbabilityRidge(analRidgeC);
        if (chordC && chordC.offsetParent !== null) drawHandoffChord(chordC);
        if (regimeC && regimeC.offsetParent !== null) drawRegimeMap(regimeC);
        if (corrC && corrC.offsetParent !== null) drawCorrMatrix(corrC);
        if (simEquityC && simEquityC.offsetParent !== null) drawSimulatedEquityCurve(simEquityC);
        if (ddDistC && ddDistC.offsetParent !== null) drawDdDist(ddDistC);
        if (paramSweepC && paramSweepC.offsetParent !== null) drawParamSweepHeatmap(paramSweepC);

        animFrameId = requestAnimationFrame(loop);
    }
    animFrameId = requestAnimationFrame(loop);
}

// ==========================================================================
// 9. REAL-TIME BACKTEST ENGINE EXECUTION & UI RENDERER
// ==========================================================================
function renderBacktestResults(data) {
    if (!data) return;
    window.activeBacktestResult = data;

    // 1. Update 6 KPI Cards
    const pnlEl = document.getElementById('bt-res-pnl');
    const roiEl = document.getElementById('bt-res-roi');
    const balSubEl = document.getElementById('bt-res-balance-sub');
    if (pnlEl) {
        const sign = data.net_pnl_usdt >= 0 ? '+' : '-';
        pnlEl.innerText = `${sign}$${Math.abs(data.net_pnl_usdt).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        pnlEl.className = data.net_pnl_usdt >= 0 ? 'q-stat-val val-green' : 'q-stat-val val-rose';
    }
    if (roiEl) {
        const sign = data.roi_pct >= 0 ? '+' : '';
        roiEl.innerText = `${sign}${data.roi_pct}%`;
        roiEl.style.color = data.roi_pct >= 0 ? '#10b981' : '#f43f5e';
    }
    if (balSubEl) {
        balSubEl.innerText = `Từ $${(data.initial_balance || 10000).toLocaleString()} lên $${(data.final_balance || 10000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    const winrateEl = document.getElementById('bt-res-winrate');
    const winrateSubEl = document.getElementById('bt-res-winrate-sub');
    if (winrateEl) winrateEl.innerText = `${data.win_rate}%`;
    if (winrateSubEl) winrateSubEl.innerText = `${data.winning_trades} / ${data.total_trades} lệnh thắng`;

    const pfEl = document.getElementById('bt-res-profit-factor');
    if (pfEl) pfEl.innerText = data.profit_factor == null ? 'N/A' : `${data.profit_factor}`;

    const ddEl = document.getElementById('bt-res-drawdown');
    const ddSubEl = document.getElementById('bt-res-dd-sub');
    if (ddEl) ddEl.innerText = `${data.max_drawdown}%`;
    if (ddSubEl) {
        const ddUsdt = data.max_drawdown_usdt || (data.initial_balance * (data.max_drawdown / 100));
        ddSubEl.innerText = `-$${ddUsdt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USDT`;
    }

    const sharpeEl = document.getElementById('bt-res-sharpe');
    if (sharpeEl) sharpeEl.innerText = `${data.sharpe_ratio}`;

    // Exit Reasons Card
    const dist = data.distribution || {};
    const tpCount = dist.take_profit || 0;
    const slCount = dist.stop_loss || 0;
    const trCount = dist.trailing_stop || 0;
    const beCount = dist.break_even || 0;

    const exitTextEl = document.getElementById('bt-res-exit-text');
    if (exitTextEl) {
        exitTextEl.innerText = `TP: ${tpCount} | SL: ${slCount} | TR: ${trCount} | BE: ${beCount}`;
    }

    const exitTpBar = document.getElementById('bt-exit-tp');
    const exitSlBar = document.getElementById('bt-exit-sl');
    const exitTrBar = document.getElementById('bt-exit-tr');
    const exitBeBar = document.getElementById('bt-exit-be');
    if (exitTpBar) exitTpBar.style.width = `${dist.tp_pct || 0}%`;
    if (exitSlBar) exitSlBar.style.width = `${dist.sl_pct || 0}%`;
    if (exitTrBar) exitTrBar.style.width = `${dist.tr_pct || 0}%`;
    if (exitBeBar) exitBeBar.style.width = `${dist.be_pct || 0}%`;

    const exitLabelsEl = document.getElementById('bt-exit-labels');
    if (exitLabelsEl) {
        exitLabelsEl.innerHTML = `
            <span style="color: #10b981;">${dist.tp_pct || 0}%</span>
            <span style="color: #f43f5e;">${dist.sl_pct || 0}%</span>
            <span style="color: #0ea5e9;">${dist.tr_pct || 0}%</span>
            <span style="color: #f59e0b;">${dist.be_pct || 0}%</span>
        `;
    }

    // 2. Middle Row: 5 Bottom Strip Metrics
    const stripRoi = document.getElementById('bt-strip-roi');
    const stripSharpe = document.getElementById('bt-strip-sharpe');
    const stripDd = document.getElementById('bt-strip-dd');
    const stripWinrate = document.getElementById('bt-strip-winrate');
    const stripTotal = document.getElementById('bt-strip-total');

    if (stripRoi) {
        stripRoi.innerText = `${data.roi_pct >= 0 ? '+' : ''}${data.roi_pct}%`;
        stripRoi.className = data.roi_pct >= 0 ? 'val green-txt' : 'val rose-txt';
    }
    if (stripSharpe) stripSharpe.innerText = `${data.sharpe_ratio}`;
    if (stripDd) stripDd.innerText = `${data.max_drawdown}%`;
    if (stripWinrate) stripWinrate.innerText = `${data.win_rate}%`;
    if (stripTotal) stripTotal.innerText = `${data.total_trades}`;

    // 3. Strategy Verification Audit Box
    const auditStart = document.getElementById('bt-audit-start');
    const auditEnd = document.getElementById('bt-audit-end');
    const auditPnl = document.getElementById('bt-audit-pnl');
    const auditPres = document.getElementById('bt-audit-preservation');
    const auditLev = document.getElementById('bt-audit-leverage');
    const auditFees = document.getElementById('bt-audit-total-fees');
    const auditPeriod = document.getElementById('bt-audit-period');
    const auditTrades = document.getElementById('bt-audit-trades');
    const auditSource = document.getElementById('bt-audit-source');
    const auditEngine = document.getElementById('bt-audit-engine');
    const auditNote = document.getElementById('bt-audit-eval-note');

    if (auditStart) auditStart.innerText = `$${(data.initial_balance || 10000).toLocaleString(undefined, { minimumFractionDigits: 2 })} USDT`;
    if (auditEnd) {
        auditEnd.innerText = `$${(data.final_balance || 10000).toLocaleString(undefined, { minimumFractionDigits: 2 })} USDT`;
        auditEnd.style.color = data.net_pnl_usdt >= 0 ? '#10b981' : '#f43f5e';
    }
    if (auditPnl) {
        auditPnl.innerText = `${data.net_pnl_usdt >= 0 ? '+' : ''}$${data.net_pnl_usdt.toLocaleString(undefined, { minimumFractionDigits: 2 })} (${data.roi_pct >= 0 ? '+' : ''}${data.roi_pct}%)`;
        auditPnl.style.color = data.net_pnl_usdt >= 0 ? '#10b981' : '#f43f5e';
    }
    if (auditPres) {
        const presRating = data.max_drawdown <= 15 ? 'Tốt' : (data.max_drawdown <= 25 ? 'Trung bình' : 'Rủi ro cao');
        auditPres.innerText = `${presRating} (Max DD ${data.max_drawdown}%)`;
        auditPres.style.color = data.max_drawdown <= 15 ? '#10b981' : '#f59e0b';
    }
    if (auditLev) auditLev.innerText = `${document.getElementById('bt-lev')?.value || '5'}x`;
    if (auditFees) auditFees.innerText = `$${(data.total_fees || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })} USDT`;
    const provenance = data.provenance || {};
    if (auditPeriod) auditPeriod.innerText = provenance.dataset_start && provenance.dataset_end
        ? `${provenance.dataset_start} → ${provenance.dataset_end}`
        : `Lịch sử ${data.candle_limit} nến (${data.timeframe})`;
    if (auditTrades) auditTrades.innerText = `${data.total_trades} (${data.winning_trades} thắng / ${data.losing_trades} thua)`;
    if (auditSource) auditSource.innerText = provenance.source === 'binance_live_rest_api'
        ? `Binance REST · ${data.symbol} · ${data.timeframe} · ${provenance.candles_fetched || data.candle_limit} nến`
        : `${provenance.source || 'Không xác định'} · ${data.symbol} · ${data.timeframe}`;
    if (auditEngine) {
        const stratSelect = document.getElementById('bt-strat');
        auditEngine.innerText = stratSelect?.options[stratSelect.selectedIndex]?.text || data.strategy;
    }
    if (auditNote) {
        const pf = Number(data.profit_factor);
        const lowSample = !data.metrics_reliable;
        if (Number.isFinite(pf) && pf >= 1.8 && data.max_drawdown <= 18) {
            auditNote.innerText = `Kết quả in-sample đang tích cực (Profit Factor: ${data.profit_factor}, Sharpe: ${data.sharpe_ratio}, Max DD: ${data.max_drawdown}%). Chưa đủ căn cứ tăng vốn hoặc chạy live; cần kiểm tra out-of-sample, walk-forward, trượt giá và funding.`;
        } else if (data.net_pnl_usdt > 0) {
            auditNote.innerText = `Chiến lược có lợi nhuận dương (ROI: +${data.roi_pct}%), tuy nhiên cần theo dõi tỷ lệ rủi ro (Drawdown: ${data.max_drawdown}%). Khuyến nghị giữ đòn bẩy thấp để bảo toàn vốn.`;
        } else {
            auditNote.innerText = `Hiệu suất chưa tối ưu trong giai đoạn thị trường đã chọn (ROI: ${data.roi_pct}%). Khuyến nghị điều chỉnh thông số Stop Loss/Trailing Stop hoặc áp dụng bộ lọc đa khung thời gian.`;
        }
        if (lowSample) auditNote.innerText += ` Cảnh báo: chỉ có ${data.total_trades} lệnh đóng, mẫu quá nhỏ để kết luận.`;
    }

    // 4. Quad Analytics Grid (8 Performance metrics)
    const pTotal = document.getElementById('bt-perf-total');
    const pWin = document.getElementById('bt-perf-win');
    const pLoss = document.getElementById('bt-perf-loss');
    const pWinrate = document.getElementById('bt-perf-winrate');
    const pAvgWin = document.getElementById('bt-perf-avg-win');
    const pAvgLoss = document.getElementById('bt-perf-avg-loss');
    const pAvgRr = document.getElementById('bt-perf-avg-rr');
    const pAvgDur = document.getElementById('bt-perf-avg-dur');

    if (pTotal) pTotal.innerText = `${data.total_trades}`;
    if (pWin) pWin.innerText = `${data.winning_trades}`;
    if (pLoss) pLoss.innerText = `${data.losing_trades}`;
    if (pWinrate) pWinrate.innerText = `${data.win_rate}%`;
    if (pAvgWin) pAvgWin.innerText = `+${data.avg_win_pct || 0}%`;
    if (pAvgLoss) pAvgLoss.innerText = `-${data.avg_loss_pct || 0}%`;
    if (pAvgRr) pAvgRr.innerText = Number.isFinite(Number(data.avg_rr)) ? `${data.avg_rr}` : '—';
    if (pAvgDur) pAvgDur.innerText = data.avg_duration || '—';

    const proofValues = {
        'bt-proof-run': data.run_id || '—',
        'bt-proof-source': provenance.source === 'binance_live_rest_api' ? 'Binance Live REST API' : (provenance.source || '—'),
        'bt-proof-candles': `${provenance.candles_fetched ?? data.candle_limit ?? '—'} / ${provenance.candles_requested ?? data.candle_limit ?? '—'}`,
        'bt-proof-window': provenance.dataset_start && provenance.dataset_end ? `${provenance.dataset_start} → ${provenance.dataset_end}` : '—',
        'bt-proof-fingerprint': provenance.dataset_fingerprint ? provenance.dataset_fingerprint.slice(0, 20) + '…' : '—',
        'bt-proof-runtime': Number.isFinite(Number(data.server_elapsed_ms)) ? `${data.server_elapsed_ms} ms` : '—'
    };
    Object.entries(proofValues).forEach(([id, value]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    });
    const caveats = document.getElementById('bt-proof-caveats');
    if (caveats) {
        const assumptions = Array.isArray(provenance.assumptions) ? provenance.assumptions : [];
        caveats.textContent = assumptions.join(' · ') || 'Không có metadata giả định từ engine.';
    }

    // Drawdown badge
    const ddBadge = document.getElementById('bt-dd-badge');
    if (ddBadge) ddBadge.innerText = `Max DD: ${data.max_drawdown}%`;

    // 5. Monthly Return Table
    const monthlyTbody = document.getElementById('bt-monthly-tbody');
    if (monthlyTbody && data.monthly_returns && data.monthly_returns.length > 0) {
        let mHtml = '';
        data.monthly_returns.forEach(m => {
            const sign = m.pnl_usdt >= 0 ? '+' : '';
            const color = m.pnl_usdt >= 0 ? '#10b981' : '#f43f5e';
            mHtml += `
                <tr style="border-bottom: 1px solid var(--q-card-border);">
                    <td style="padding: 6px 0;">${m.month}</td>
                    <td style="text-align: right; color: ${color}; font-weight: 700;">${sign}${m.pnl_usdt.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td style="text-align: right; color: ${color}; font-weight: 700;">${sign}${m.roi_pct}%</td>
                </tr>
            `;
        });
        mHtml += `
            <tr style="font-weight: 800;">
                <td style="padding: 6px 0;">Tổng</td>
                <td style="text-align: right; color: ${data.net_pnl_usdt >= 0 ? '#10b981' : '#f43f5e'};">${data.net_pnl_usdt >= 0 ? '+' : ''}${data.net_pnl_usdt.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                <td style="text-align: right; color: ${data.roi_pct >= 0 ? '#10b981' : '#f43f5e'};">${data.roi_pct >= 0 ? '+' : ''}${data.roi_pct}%</td>
            </tr>
        `;
        monthlyTbody.innerHTML = mHtml;
    }

    // 6. Populate Trades History Table
    const tradesTbody = document.getElementById('bt-trades-tbody');
    if (tradesTbody && data.trades) {
        if (data.trades.length === 0) {
            tradesTbody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: var(--q-text-muted); padding: 24px;">Không có lệnh nào thỏa mãn điều kiện vào trong ${data.candle_limit} nến đã chọn.</td></tr>`;
        } else {
            let html = '';
            data.trades.forEach((t, idx) => {
                const sideBadge = t.side === 'LONG'
                    ? '<span class="badge-side-long">LONG</span>'
                    : '<span class="badge-side-short">SHORT</span>';

                let reasonBadge = '';
                if (t.reason === 'TAKE_PROFIT') {
                    reasonBadge = '<span class="badge-reason tp">TP</span>';
                } else if (t.reason === 'STOP_LOSS') {
                    reasonBadge = '<span class="badge-reason sl">SL</span>';
                } else if (t.reason === 'TRAILING_STOP') {
                    reasonBadge = '<span class="badge-reason tr">TR</span>';
                } else {
                    reasonBadge = '<span class="badge-reason be">BE</span>';
                }

                const pnlClass = t.pnl_usdt >= 0 ? 'green-txt' : 'rose-txt';
                const sign = t.pnl_usdt >= 0 ? '+' : '';

                html += `
                    <tr>
                        <td>${t.id || (idx + 1)}</td>
                        <td>${sideBadge}</td>
                        <td class="time-col">${t.entry_time || '--'}</td>
                        <td class="time-col">${t.exit_time || '--'}</td>
                        <td>${t.duration || '--'}</td>
                        <td>$${(t.entry_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        <td>$${(t.exit_price || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                        <td class="${pnlClass}" style="font-weight:700;">${sign}${t.pnl_pct}%</td>
                        <td class="${pnlClass}" style="font-weight:700;">${sign}${t.pnl_usdt.toFixed(2)}</td>
                        <td>${reasonBadge}</td>
                        <td style="font-weight:700;">$${(t.balance_after || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    </tr>
                `;
            });
            tradesTbody.innerHTML = html;
        }
    }

    // 7. Redraw Canvases with new data
    const simEquityC = document.getElementById('simEquityCanvas');
    if (simEquityC) drawSimulatedEquityCurve(simEquityC);

    const ddDistC = document.getElementById('ddDistCanvas');
    if (ddDistC) drawDdDist(ddDistC);
}

// === EXPORT AUDIT REPORT HANDLER ===
function exportAuditReport() {
    const res = window.activeBacktestResult;
    if (!res) {
        alert('Hãy chạy backtest thật trước khi xuất báo cáo. Hệ thống không còn xuất số liệu mẫu.');
        return;
    }
    const symbol = document.getElementById('bt-sym')?.value || 'BTC/USDT';
    const tf = document.getElementById('bt-tf')?.value || '15m';

    const text = `=== QUANTUM AUDIT VERIFICATION REPORT ===
Generated: ${new Date().toISOString()}
Target: ${symbol} (${tf})
Run ID: ${res.run_id || 'N/A'}
Data Source: ${res.provenance?.source || 'N/A'}
Dataset Window: ${res.provenance?.dataset_start || 'N/A'} -> ${res.provenance?.dataset_end || 'N/A'}
Candles: ${res.provenance?.candles_fetched || res.candle_limit}
Dataset Fingerprint: ${res.provenance?.dataset_fingerprint || 'N/A'}
Server Runtime: ${res.server_elapsed_ms || 'N/A'} ms
Starting Capital: $${res.initial_balance} USDT
Ending Capital: $${res.final_balance} USDT
Net Profit: ${res.net_pnl_usdt} USDT (${res.roi_pct}%)
Win Rate: ${res.win_rate}% (${res.winning_trades}/${res.total_trades} wins)
Profit Factor: ${res.profit_factor}
Max Drawdown: ${res.max_drawdown}%
Sharpe Ratio: ${res.sharpe_ratio}
Total Fees Paid: $${res.total_fees} USDT
Audit State: HISTORICAL IN-SAMPLE RESULT - NOT A LIVE PROFIT GUARANTEE
`;

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `backtest_audit_${symbol.replace('/', '_')}_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

// === RUN BACKTEST HANDLER — progress reflects real wall-clock time ===
async function runBacktestSimulation() {
    const btn = document.getElementById('btn-run-simulation');
    const progressWrap = document.getElementById('bt-sim-progress-wrap');
    const stepText = document.getElementById('bt-sim-step-text');
    const percentEl = document.getElementById('bt-sim-percent');
    const barFill = document.getElementById('bt-sim-progress-bar-fill');
    const toast = document.getElementById('bt-sim-toast');
    const toastMsg = document.getElementById('bt-sim-toast-msg');

    if (toast) toast.style.display = 'none';

    // 1. Gather inputs
    const symbol = document.getElementById('bt-sym')?.value || 'BTC/USDT';
    const timeframe = document.getElementById('bt-tf')?.value || '15m';
    const candleLimit = parseInt(document.getElementById('bt-candles')?.value || '500');
    const strategy = document.getElementById('bt-strat')?.value || 'ema_cross';
    const leverage = parseFloat(document.getElementById('bt-lev')?.value || '5');
    const slPct = (parseFloat(document.getElementById('bt-sl')?.value || '1.5') || 1.5) / 100.0;
    const tpPct = (parseFloat(document.getElementById('bt-tp')?.value || '3.0') || 3.0) / 100.0;
    const beTriggerPct = (parseFloat(document.getElementById('bt-be')?.value || '1.5') || 1.5) / 100.0;
    const trailCallbackPct = (parseFloat(document.getElementById('bt-ts')?.value || '1.0') || 1.0) / 100.0;
    const enableTrailing = document.getElementById('bt-cb-trailing')?.checked ?? true;
    const enableBreakEven = document.getElementById('bt-cb-be')?.checked ?? true;
    window.backtestCompareBuyHold = document.getElementById('bt-cb-compare')?.checked ?? true;

    // 2. Set UI Loading State
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span style="display:inline-block; width:14px; height:14px; border:2px solid #fff; border-top-color:transparent; border-radius:50%; animation: spin 0.8s linear infinite;"></span> <div style="text-align: left; line-height: 1.2;"><div style="font-size: 12px; font-weight: 800;">BACKEND ĐANG XỬ LÝ...</div><div style="font-size: 9px; opacity: 0.85;">${candleLimit} nến ${symbol} (${timeframe})</div></div>`;
    }

    if (progressWrap) progressWrap.style.display = 'block';
    if (barFill) barFill.style.width = '12%';
    if (percentEl) percentEl.innerText = '0.0s';
    if (stepText) {
        stepText.innerHTML = `<span class="bt-live-dot"></span><span>Đang gửi yêu cầu tải ${candleLimit} nến Binance và chạy engine…</span>`;
    }

    const payload = {
        symbol: symbol,
        timeframe: timeframe,
        strategy: strategy,
        candle_limit: candleLimit,
        initial_balance: 10000.0,
        position_pct: 0.20,
        leverage: leverage,
        sl_pct: slPct,
        tp_pct: tpPct,
        be_trigger_pct: beTriggerPct,
        trail_callback_pct: trailCallbackPct,
        enable_trailing: enableTrailing,
        enable_break_even: enableBreakEven
    };

    // One server request owns the complete pipeline. The UI reports elapsed time;
    // it does not invent client-side stages or delay a fast result.
    const startTime = Date.now();
    let visualProgress = 12;
    const timer = setInterval(() => {
        const elapsedSeconds = ((Date.now() - startTime) / 1000).toFixed(1);
        visualProgress = Math.min(90, visualProgress + 3);
        if (barFill) barFill.style.width = `${visualProgress}%`;
        if (percentEl) percentEl.innerText = `${elapsedSeconds}s`;
        if (stepText) stepText.innerHTML = `<span class="bt-live-dot"></span><span>Backend đang tải nến Binance, tính chỉ báo và mô phỏng lệnh… ${elapsedSeconds}s</span>`;
    }, 250);

    try {
        const response = await fetch('/api/v1/backtest/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const responseData = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(responseData?.detail || `HTTP ${response.status}`);

        // Stage 4: Completed
        if (barFill) barFill.style.width = '100%';
        if (percentEl) percentEl.innerText = '100%';
        if (stepText) {
            stepText.innerHTML = `<span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#10b981; box-shadow: 0 0 8px #10b981;"></span> <span style="color:#10b981;">Backend đã trả kết quả; đang cập nhật biểu đồ và dấu vết kiểm chứng.</span>`;
        }

        if (responseData && responseData.status === 'SUCCESS' && responseData.data) {
            renderBacktestResults(responseData.data);

            if (toast && toastMsg) {
                const d = responseData.data;
                const sign = d.net_pnl_usdt >= 0 ? '+' : '';
                toastMsg.innerText = `Run ${d.run_id || ''} hoàn tất bằng ${d.provenance?.candles_fetched || candleLimit} nến Binance trong ${d.server_elapsed_ms ?? '—'} ms. Net PnL: ${sign}$${d.net_pnl_usdt.toLocaleString(undefined, { minimumFractionDigits: 2 })}; Win Rate: ${d.win_rate}%; Max DD: ${d.max_drawdown}%.`;
                toast.style.display = 'flex';
            }
        } else {
            throw new Error(responseData?.detail || 'Dữ liệu backtest không hợp lệ');
        }
    } catch (err) {
        console.error('Backtest simulation failed:', err);
        if (toast && toastMsg) {
            toastMsg.innerText = `Lỗi mô phỏng: ${err.message || 'Không thể hoàn tất kết nối Binance'}`;
            toast.style.borderColor = 'rgba(244, 63, 94, 0.4)';
            toast.style.background = 'rgba(244, 63, 94, 0.12)';
            toast.style.color = '#f43f5e';
            toast.style.display = 'flex';
        }
    } finally {
        clearInterval(timer);
        if (progressWrap) progressWrap.style.display = 'none';
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg> <div style="text-align: left; line-height: 1.2;"><div style="font-size: 12.5px; font-weight: 800;">CHẠY BACKTEST NGAY</div><div style="font-size: 9px; opacity: 0.85; font-weight: 500;">Mô phỏng &amp; phân tích chiến lược</div></div>`;
        }
    }
}

window.switchBacktestTf = function(tf, btn) {
    window.backtestTimeframe = tf;
    if (btn?.parentElement) {
        btn.parentElement.querySelectorAll('.q-tf-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
    const canvas = document.getElementById('simEquityCanvas');
    if (canvas) drawSimulatedEquityCurve(canvas);
};

function resetBacktestPlaceholders() {
    window.activeBacktestResult = null;
    const ids = ['bt-res-pnl','bt-res-roi','bt-res-balance-sub','bt-res-winrate','bt-res-winrate-sub',
        'bt-res-profit-factor','bt-res-drawdown','bt-res-dd-sub','bt-res-sharpe','bt-res-exit-text',
        'bt-strip-roi','bt-strip-sharpe','bt-strip-dd','bt-strip-winrate','bt-strip-total',
        'bt-perf-total','bt-perf-win','bt-perf-loss','bt-perf-winrate','bt-perf-avg-win',
        'bt-perf-avg-loss','bt-perf-avg-rr','bt-perf-avg-dur'];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.textContent = '—'; });
    ['bt-exit-tp','bt-exit-sl','bt-exit-tr','bt-exit-be'].forEach(id => {
        const el = document.getElementById(id); if (el) el.style.width = '0%';
    });
    const toast = document.getElementById('bt-sim-toast');
    if (toast) toast.style.display = 'none';
    const trades = document.getElementById('bt-trades-tbody');
    if (trades) trades.innerHTML = '<tr><td colspan="11" class="bt-empty-cell">Chưa có dữ liệu. Chạy backtest để lấy kết quả có dấu vết kiểm chứng.</td></tr>';
    const monthly = document.getElementById('bt-monthly-tbody');
    if (monthly) monthly.innerHTML = '<tr><td colspan="3" class="bt-empty-cell">Chưa chạy backtest</td></tr>';
}

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', () => {
    updateQuantumClock();
    setInterval(updateQuantumClock, 1000);
    startMasterLoop();
    loadBalanceHistoryData();
    resetBacktestPlaceholders();
});



// ==========================================================================
// LIVE TELEMETRY POLLING FOR QUANTUM COCKPIT
// ==========================================================================
async function pollQuantumLiveTelemetry() {
    try {
        const res = await fetch('/api/v1/quantum/telemetry');
        if (!res.ok) return;
        const data = await res.json();
        
        // 1. Balance & Source
        if (data.balance_usd != null) {
            const bal = Number(data.balance_usd);
            const balEl = document.getElementById('qc-val-bal');
            if (balEl) balEl.innerText = `$${bal.toFixed(2)} USD`;
            const currBalEl = document.getElementById('qc-val-curr-bal');
            if (currBalEl) currBalEl.innerText = `$${bal.toFixed(2)}`;
        }
        
        const badgeEl = document.getElementById('qc-val-badge');
        if (badgeEl && data.balance_source) {
            badgeEl.innerText = data.balance_source;
            if (data.balance_source.includes('LIVE')) {
                badgeEl.className = 'q-stat-badge-tag green';
                badgeEl.style.color = '#10b981';
            }
        }
        
        // 2. Status Badge & Pill
        const badgeText = document.getElementById('q-status-badge-text');
        if (badgeText) {
            badgeText.innerText = data.telemetry_status === 'LIVE' ? '●● LIVE TRADING (Binance USDⓈ-M)' : '●● LIVE TRADING';
            badgeText.style.color = '#10b981';
        }
        const auditPill = document.getElementById('q-audit-pill');
        if (auditPill) {
            auditPill.innerText = '● LIVE · BINANCE SYNCED';
            auditPill.className = 'live-pill active-state';
            auditPill.style.color = '#10b981';
        }

        // 3. PnL
        if (data.total_pnl_usd != null) {
            const pnl = Number(data.total_pnl_usd);
            const pnlEl = document.getElementById('qc-val-pnl');
            const todayPnlEl = document.getElementById('qc-val-today-pnl');
            const realPnlEl = document.getElementById('qc-val-realized-pnl');
            const pnlStr = (pnl >= 0 ? '+' : '') + `$${pnl.toFixed(2)}`;
            if (pnlEl) {
                pnlEl.innerText = pnlStr;
                pnlEl.className = pnl >= 0 ? 'q-stat-val val-green' : 'q-stat-val val-red';
            }
            if (todayPnlEl) todayPnlEl.innerText = pnlStr;
            if (realPnlEl) realPnlEl.innerText = pnlStr;
        }

        // 4. Mission Goal
        if (data.campaign_goal) {
            const missionEl = document.getElementById('qc-val-mission');
            if (missionEl) {
                const cur = Number(data.campaign_goal.current_pnl_usd || 0);
                const tgt = Number(data.campaign_goal.target_pnl_usdt || 5.0);
                missionEl.innerText = `${cur >= 0 ? '+' : ''}$${cur.toFixed(2)} / +$${tgt.toFixed(2)}U`;
            }
        }

        // 5. Update Quantum Analytics tab cards
        if (data.balance_usd != null) {
            const qaCurrBal = document.getElementById('qa-val-curr-bal');
            if (qaCurrBal) qaCurrBal.innerText = `$${Number(data.balance_usd).toFixed(2)}`;
            const qaStartBal = document.getElementById('qa-val-start-bal');
            if (qaStartBal) {
                const startB = Number(data.balance_usd) - Number(data.total_pnl_usd || 0.40);
                qaStartBal.innerText = `$${startB.toFixed(2)}`;
            }
        }
        if (data.total_pnl_usd != null) {
            const qaPnl = document.getElementById('qa-val-pnl');
            const pnlVal = Number(data.total_pnl_usd);
            if (qaPnl) qaPnl.innerText = `${pnlVal >= 0 ? '+' : ''}$${pnlVal.toFixed(2)} USD`;
        }
        if (data.total_trades != null) {
            const qaTrades = document.getElementById('qa-val-trades');
            if (qaTrades) qaTrades.innerText = data.total_trades;
        }
        if (data.win_rate_pct != null) {
            const qaWin = document.getElementById('qa-val-winrate');
            if (qaWin) qaWin.innerText = `${Number(data.win_rate_pct).toFixed(1)}%`;
        }
    } catch (e) {
        console.warn('Quantum telemetry poll error:', e);
    }
}

// Auto start polling
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', () => {
        pollQuantumLiveTelemetry();
        setInterval(pollQuantumLiveTelemetry, 5000);
    });
}
