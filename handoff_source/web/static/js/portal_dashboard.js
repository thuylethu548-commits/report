/**
 * ASTRA QUANT CLIENT PORTAL DASHBOARD CONTROLLER
 * Canvas Equity Curve, Portfolio Donut, Tab Switching & Live Interactions
 */

// Sample Time-Series Data for 30D (Matching Mockup 1 & Mockup 3)
const EQUITY_DATA_30D = [
    { date: '01/11', equity: 30000, profit: 0, btcPct: 0 },
    { date: '03/11', equity: 33500, profit: 3500, btcPct: 2.1 },
    { date: '05/11', equity: 38200, profit: 8200, btcPct: 5.4 },
    { date: '07/11', equity: 42000, profit: 12000, btcPct: 9.8 },
    { date: '09/11', equity: 41200, profit: 11200, btcPct: 8.5 },
    { date: '11/11', equity: 44800, profit: 14800, btcPct: 14.2 },
    { date: '13/11', equity: 43500, profit: 13500, btcPct: 12.0 },
    { date: '15/11', equity: 48900, profit: 18900, btcPct: 19.5 },
    { date: '17/11', equity: 47200, profit: 17200, btcPct: 17.8 },
    { date: '19/11', equity: 51400, profit: 21400, btcPct: 23.4 },
    { date: '21/11', equity: 50800, profit: 20800, btcPct: 22.1 },
    { date: '23/11', equity: 54200, profit: 24200, btcPct: 28.6 },
    { date: '25/11', equity: 53800, profit: 23800, btcPct: 27.2 },
    { date: '27/11', equity: 56217, profit: 26217, btcPct: 35.2 }
];

// Portfolio Allocation Data
const PORTFOLIO_ALLOCATION = [
    { asset: 'BTC', pct: 45.2, value: 22600, color: '#3b82f6' },
    { asset: 'ETH', pct: 28.1, value: 14050, color: '#06b6d4' },
    { asset: 'BNB', pct: 12.4, value: 6200, color: '#f59e0b' },
    { asset: 'SOL', pct: 8.7, value: 4350, color: '#a855f7' },
    { asset: 'Khác', pct: 5.6, value: 2800, color: '#64748b' }
];

let currentChartTab = 'equity'; // 'equity' | 'profit' | 'roi' | 'drawdown'
let currentTimeframe = '30D';

/* ==========================================================================
   1. CANVAS EQUITY CURVE & PERFORMANCE CHART
   ========================================================================== */
function drawEquityCurve(data = EQUITY_DATA_30D) {
    const canvas = document.getElementById('equityCurveCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    ctx.clearRect(0, 0, w, h);

    const padding = { top: 25, right: 30, bottom: 35, left: 55 };
    const chartW = w - padding.left - padding.right;
    const chartH = h - padding.top - padding.bottom;

    // Determine min and max based on view
    let minVal = 25000;
    let maxVal = 65000;

    if (currentChartTab === 'profit') {
        minVal = -2000;
        maxVal = 10000;
    } else if (currentChartTab === 'roi') {
        minVal = -5;
        maxVal = 30;
    } else if (currentChartTab === 'drawdown') {
        minVal = -15;
        maxVal = 2;
    }

    // Grid lines & Y-axis labels
    ctx.lineWidth = 1;
    ctx.strokeStyle = document.documentElement.getAttribute('data-theme') === 'dark' ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)';
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = 'right';

    const ySteps = 4;
    for (let i = 0; i <= ySteps; i++) {
        const val = minVal + (maxVal - minVal) * (i / ySteps);
        const y = padding.top + chartH - (i / ySteps) * chartH;

        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartW, y);
        ctx.stroke();

        let label = '';
        if (currentChartTab === 'profit' || currentChartTab === 'equity') {
            label = `$${(val / 1000).toFixed(0)}k`;
        } else {
            label = `${val.toFixed(1)}%`;
        }
        ctx.fillText(label, padding.left - 8, y + 3);
    }

    // X-axis dates
    ctx.textAlign = 'center';
    const xStep = chartW / (data.length - 1);
    data.forEach((d, i) => {
        if (i % 2 === 0 || i === data.length - 1) {
            const x = padding.left + i * xStep;
            ctx.fillText(d.date, x, h - 10);
        }
    });

    // Helper: Map data point to canvas coords
    function getCoords(val, index) {
        const x = padding.left + index * xStep;
        const normalized = (val - minVal) / (maxVal - minVal);
        const y = padding.top + chartH - normalized * chartH;
        return { x, y };
    }

    // 1. Draw BTC Benchmark Line (Dashed Orange)
    if (currentChartTab === 'profit' || currentChartTab === 'equity') {
        ctx.save();
        ctx.setLineDash([4, 4]);
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 1.5;
        ctx.beginPath();

        data.forEach((d, i) => {
            const btcVal = currentChartTab === 'profit' ? (d.btcPct * 120) : (30000 + d.btcPct * 400);
            const pt = getCoords(btcVal, i);
            if (i === 0) ctx.moveTo(pt.x, pt.y);
            else ctx.lineTo(pt.x, pt.y);
        });
        ctx.stroke();
        ctx.restore();
    }

    // 2. Draw Main Equity Curve with Area Gradient
    const isProfitView = currentChartTab === 'profit';
    const mainValues = data.map(d => isProfitView ? d.profit / 4.2 : d.equity);

    // Gradient fill under curve
    const grad = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartH);
    if (isProfitView) {
        grad.addColorStop(0, 'rgba(16, 185, 129, 0.28)');
        grad.addColorStop(1, 'rgba(16, 185, 129, 0.01)');
    } else {
        grad.addColorStop(0, 'rgba(37, 99, 235, 0.28)');
        grad.addColorStop(1, 'rgba(37, 99, 235, 0.01)');
    }

    ctx.beginPath();
    const firstPt = getCoords(mainValues[0], 0);
    ctx.moveTo(firstPt.x, padding.top + chartH);
    ctx.lineTo(firstPt.x, firstPt.y);

    for (let i = 0; i < data.length - 1; i++) {
        const p0 = getCoords(mainValues[i], i);
        const p1 = getCoords(mainValues[i + 1], i + 1);
        const midX = (p0.x + p1.x) / 2;
        ctx.bezierCurveTo(midX, p0.y, midX, p1.y, p1.x, p1.y);
    }

    const lastPt = getCoords(mainValues[mainValues.length - 1], data.length - 1);
    ctx.lineTo(lastPt.x, padding.top + chartH);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Stroke line
    ctx.beginPath();
    ctx.moveTo(firstPt.x, firstPt.y);
    for (let i = 0; i < data.length - 1; i++) {
        const p0 = getCoords(mainValues[i], i);
        const p1 = getCoords(mainValues[i + 1], i + 1);
        const midX = (p0.x + p1.x) / 2;
        ctx.bezierCurveTo(midX, p0.y, midX, p1.y, p1.x, p1.y);
    }
    ctx.strokeStyle = isProfitView ? '#10b981' : '#2563eb';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Highlight end point with glowing badge
    ctx.beginPath();
    ctx.arc(lastPt.x, lastPt.y, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#fff';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = isProfitView ? '#10b981' : '#2563eb';
    ctx.stroke();

    // Value tooltip callout at end
    const valText = isProfitView ? '+$6,217' : '$56,217';
    ctx.fillStyle = isProfitView ? '#10b981' : '#2563eb';
    ctx.beginPath();
    if (ctx.roundRect) {
        ctx.roundRect(lastPt.x - 30, lastPt.y - 26, 56, 18, 4);
    } else {
        ctx.rect(lastPt.x - 30, lastPt.y - 26, 56, 18);
    }
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 10px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(valText, lastPt.x - 2, lastPt.y - 14);
}

/* ==========================================================================
   2. CANVAS PORTFOLIO ALLOCATION DONUT CHART
   ========================================================================== */
function drawAllocationDonut() {
    const canvas = document.getElementById('allocationDonutCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    ctx.clearRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h / 2;
    const outerRadius = Math.min(w, h) / 2 - 4;
    const innerRadius = outerRadius * 0.65;

    let startAngle = -Math.PI / 2;

    PORTFOLIO_ALLOCATION.forEach(item => {
        const sliceAngle = (item.pct / 100) * (Math.PI * 2);
        const endAngle = startAngle + sliceAngle;

        ctx.beginPath();
        ctx.arc(cx, cy, outerRadius, startAngle, endAngle);
        ctx.arc(cx, cy, innerRadius, endAngle, startAngle, true);
        ctx.closePath();

        ctx.fillStyle = item.color;
        ctx.fill();

        startAngle = endAngle;
    });

    // Center circle & text
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    ctx.beginPath();
    ctx.arc(cx, cy, innerRadius - 2, 0, Math.PI * 2);
    ctx.fillStyle = isDark ? '#0f172a' : '#ffffff';
    ctx.fill();

    ctx.textAlign = 'center';
    ctx.fillStyle = isDark ? '#f8fafc' : '#0f172a';
    ctx.font = 'bold 12px "JetBrains Mono", monospace';
    ctx.fillText('$50,000', cx, cy - 2);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '9.5px "Plus Jakarta Sans", sans-serif';
    ctx.fillText('Tổng vốn', cx, cy + 12);
}

/* ==========================================================================
   3. TAB SWITCHING & USER INTERACTIONS (SMOOTH IN-PLACE, NO JUMPING)
   ========================================================================== */
function switchPortalMainTab(tabName, btn) {
    // 1. Update top tabs active state
    document.querySelectorAll('.portal-tab-btn').forEach(b => b.classList.remove('active'));
    if (btn) {
        btn.classList.add('active');
    } else {
        const matchingBtn = document.getElementById(`tab-btn-${tabName}`);
        if (matchingBtn) matchingBtn.classList.add('active');
    }

    // 2. Update sidebar active item
    document.querySelectorAll('.portal-nav-item').forEach(it => it.classList.remove('active'));
    const sidebarMap = {
        'overview': 'nav-item-dashboard',
        'performance': 'nav-item-performance',
        'strategies': 'nav-item-strategies',
        'risk': 'nav-item-risk',
        'activity': 'nav-item-copy',
        'trade': 'nav-item-trade',
        'agents': 'nav-item-ai'
    };
    const targetNavId = sidebarMap[tabName];
    if (targetNavId) {
        const navEl = document.getElementById(targetNavId);
        if (navEl) navEl.classList.add('active');
    }

    // 3. Update URL hash cleanly
    history.replaceState(null, '', `#${tabName}`);

    // 4. Ensure viewport stays comfortably at top
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // 5. Manage section display
    const perfSection = document.getElementById('performance');
    const bottomGrid = document.querySelector('.portal-bottom-grid');
    const posCard = document.getElementById('positions');
    const ordersCard = document.getElementById('recent-orders');
    const stratCard = document.getElementById('strategies');
    const newsCard = document.getElementById('news');
    const tradeSection = document.getElementById('trade-section');
    const agentsSection = document.getElementById('agents-section');

    if (tabName === 'overview') {
        if (perfSection) perfSection.style.display = 'grid';
        if (bottomGrid) bottomGrid.style.display = 'grid';
        if (posCard) { posCard.style.display = 'flex'; posCard.style.gridColumn = 'auto'; }
        if (ordersCard) { ordersCard.style.display = 'flex'; ordersCard.style.gridColumn = 'auto'; }
        if (stratCard) { stratCard.style.display = 'flex'; stratCard.style.gridColumn = 'auto'; }
        if (newsCard) { newsCard.style.display = 'flex'; newsCard.style.gridColumn = 'auto'; }
        if (tradeSection) tradeSection.style.display = 'none';
        if (agentsSection) agentsSection.style.display = 'none';

        setTimeout(() => {
            drawEquityCurve();
            drawAllocationDonut();
        }, 50);
    } else if (tabName === 'performance') {
        if (perfSection) perfSection.style.display = 'grid';
        if (bottomGrid) bottomGrid.style.display = 'grid';
        if (posCard) posCard.style.display = 'none';
        if (ordersCard) ordersCard.style.display = 'none';
        if (stratCard) { stratCard.style.display = 'flex'; stratCard.style.gridColumn = '1 / -1'; }
        if (newsCard) newsCard.style.display = 'none';
        if (tradeSection) tradeSection.style.display = 'none';
        if (agentsSection) agentsSection.style.display = 'none';

        setTimeout(() => {
            drawEquityCurve();
            drawAllocationDonut();
        }, 50);
    } else if (tabName === 'strategies') {
        if (perfSection) perfSection.style.display = 'none';
        if (bottomGrid) bottomGrid.style.display = 'grid';
        if (posCard) posCard.style.display = 'none';
        if (ordersCard) ordersCard.style.display = 'none';
        if (stratCard) { stratCard.style.display = 'flex'; stratCard.style.gridColumn = '1 / -1'; }
        if (newsCard) newsCard.style.display = 'none';
        if (tradeSection) tradeSection.style.display = 'none';
        if (agentsSection) agentsSection.style.display = 'none';
    } else if (tabName === 'risk') {
        if (perfSection) perfSection.style.display = 'none';
        if (bottomGrid) bottomGrid.style.display = 'grid';
        if (posCard) { posCard.style.display = 'flex'; posCard.style.gridColumn = '1 / -1'; }
        if (ordersCard) ordersCard.style.display = 'none';
        if (stratCard) stratCard.style.display = 'none';
        if (newsCard) newsCard.style.display = 'none';
        if (tradeSection) tradeSection.style.display = 'none';
        if (agentsSection) agentsSection.style.display = 'none';
    } else if (tabName === 'activity') {
        if (perfSection) perfSection.style.display = 'none';
        if (bottomGrid) bottomGrid.style.display = 'grid';
        if (posCard) posCard.style.display = 'none';
        if (ordersCard) { ordersCard.style.display = 'flex'; ordersCard.style.gridColumn = 'auto'; }
        if (stratCard) stratCard.style.display = 'none';
        if (newsCard) { newsCard.style.display = 'flex'; newsCard.style.gridColumn = 'auto'; }
        if (tradeSection) tradeSection.style.display = 'none';
        if (agentsSection) agentsSection.style.display = 'none';
    } else if (tabName === 'trade') {
        if (perfSection) perfSection.style.display = 'none';
        if (bottomGrid) bottomGrid.style.display = 'none';
        if (tradeSection) tradeSection.style.display = 'block';
        if (agentsSection) agentsSection.style.display = 'none';
    } else if (tabName === 'agents') {
        if (perfSection) perfSection.style.display = 'none';
        if (bottomGrid) bottomGrid.style.display = 'none';
        if (tradeSection) tradeSection.style.display = 'none';
        if (agentsSection) agentsSection.style.display = 'block';
    }
}

function switchChartTab(tabKey, btn) {
    currentChartTab = tabKey;
    document.querySelectorAll('.chart-tab-pill').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    drawEquityCurve();
}

function switchTimeframe(tf, btn) {
    currentTimeframe = tf;
    document.querySelectorAll('.tf-pill').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    // Simulate different data for timeframe
    let factor = 1;
    if (tf === '7D') factor = 0.7;
    else if (tf === '90D') factor = 1.3;
    else if (tf === '1Y') factor = 1.8;

    const adjustedData = EQUITY_DATA_30D.map(d => ({
        ...d,
        equity: Math.round(d.equity * factor),
        profit: Math.round(d.profit * factor)
    }));

    drawEquityCurve(adjustedData);
}

function switchPairPerfTab(mode, btn) {
    document.querySelectorAll('.pair-tab-pill').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    const pairs = [
        { name: 'BTC/USDT', pnl: '+$2,843.12', roi: '+18.4%', orders: '82 lệnh', pct: 90 },
        { name: 'ETH/USDT', pnl: '+$1,982.21', roi: '+12.1%', orders: '54 lệnh', pct: 65 },
        { name: 'BNB/USDT', pnl: '+$756.43', roi: '+8.6%', orders: '26 lệnh', pct: 40 },
        { name: 'SOL/USDT', pnl: '+$423.11', roi: '+6.3%', orders: '15 lệnh', pct: 25 },
        { name: 'Khác', pnl: '+$212.45', roi: '+4.1%', orders: '6 lệnh', pct: 15 }
    ];

    pairs.forEach((p, i) => {
        const valEl = document.getElementById(`pair-val-${i}`);
        if (valEl) {
            if (mode === 'pnl') valEl.textContent = p.pnl;
            else if (mode === 'roi') valEl.textContent = p.roi;
            else if (mode === 'orders') valEl.textContent = p.orders;
        }
    });
}

function filterRecentOrders(status, btn) {
    document.querySelectorAll('.order-filter-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    const rows = document.querySelectorAll('.order-table-row');
    rows.forEach(r => {
        if (status === 'all') {
            r.style.display = '';
        } else if (status === 'closed') {
            r.style.display = r.getAttribute('data-status') === 'closed' ? '' : 'none';
        } else if (status === 'open') {
            r.style.display = r.getAttribute('data-status') === 'open' ? '' : 'none';
        }
    });
}

function filterNews(category, btn) {
    document.querySelectorAll('.news-filter-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    const items = document.querySelectorAll('.news-item');
    items.forEach(it => {
        if (category === 'all' || it.getAttribute('data-category') === category) {
            it.style.display = 'flex';
        } else {
            it.style.display = 'none';
        }
    });
}

/* ==========================================================================
   4. COPY-TRADE & ORDER ACTIONS (MODERN MODAL & TOAST)
   ========================================================================== */
function toggleMasterCopy() {
    const btn = document.getElementById('masterCopyToggleBtn');
    if (!btn) return;
    const isRunning = btn.textContent.includes('ĐANG BẬT');
    if (isRunning) {
        btn.textContent = '○ ĐÃ TẠM DỪNG';
        btn.style.background = '#d97706';
        if (window.showToast) window.showToast('Đã tạm dừng nhận lệnh Copy-Trade mới từ hệ thống.', 'info');
    } else {
        btn.textContent = '● ĐANG BẬT';
        btn.style.background = '';
        if (window.showToast) window.showToast('Đã kích hoạt tự động sao chép lệnh từ Astra AI Fleet!', 'success');
    }
}

async function emergencyCloseAll() {
    if (window.showConfirmModal) {
        const confirmed = await window.showConfirmModal(
            'Dừng Khẩn Cấp',
            'Bạn có chắc chắn muốn ĐÓNG TOÀN BỘ VỊ THẾ theo giá thị trường và tạm dừng toàn bộ hoạt động sao chép lệnh ngay lập tức?'
        );
        if (confirmed) {
            if (window.showToast) window.showToast('Đang gửi lệnh đóng toàn bộ vị thế tới Execution OMS...', 'info');
            setTimeout(() => {
                if (window.showToast) window.showToast('Đã đóng toàn bộ vị thế thành công! Trạng thái tài khoản an toàn.', 'success');
                const rows = document.querySelectorAll('#positions tbody tr');
                rows.forEach(r => {
                    r.style.opacity = '0.35';
                });
                const masterBtn = document.getElementById('masterCopyToggleBtn');
                if (masterBtn) {
                    masterBtn.textContent = '○ ĐÃ TẠM DỪNG';
                    masterBtn.style.background = '#d97706';
                }
            }, 700);
        }
    }
}

async function closePosition(symbol) {
    if (window.showConfirmModal) {
        const confirmed = await window.showConfirmModal(
            'Đóng Vị Thế',
            `Bạn có chắc chắn muốn đóng vị thế ${symbol} theo giá thị trường ngay bây giờ?`
        );
        if (confirmed) {
            if (window.showToast) window.showToast(`Đang gửi lệnh đóng vị thế ${symbol} tới Execution OMS...`, 'info');
            setTimeout(() => {
                if (window.showToast) window.showToast(`Đã đóng vị thế ${symbol} thành công!`, 'success');
                const row = document.getElementById(`pos-row-${symbol.replace('/', '')}`);
                if (row) {
                    row.style.opacity = '0.4';
                    row.innerHTML = `<td colspan="7" style="text-align: center; color: var(--portal-green); font-weight: 700;">ĐÃ ĐÓNG VỊ THẾ ${symbol} THÀNH CÔNG</td>`;
                }
            }, 600);
        }
    } else {
        const row = document.getElementById(`pos-row-${symbol.replace('/', '')}`);
        if (row) {
            row.style.opacity = '0.4';
            row.innerHTML = `<td colspan="7" style="text-align: center; color: var(--portal-green); font-weight: 700;">ĐÃ ĐÓNG VỊ THẾ ${symbol} THÀNH CÔNG</td>`;
        }
    }
}

// Live Ticker Slight Price Fluctuation (Simulated Real-Time Feel)
function startLiveTickerPulse() {
    setInterval(() => {
        const btcEl = document.getElementById('ticker-header-btc');
        if (btcEl) {
            const current = 81049.90;
            const delta = (Math.random() - 0.48) * 12;
            const newPrice = (current + delta).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            btcEl.textContent = newPrice;
        }
    }, 2500);
}

// Window resize handler for responsive canvas
window.addEventListener('resize', () => {
    drawEquityCurve();
    drawAllocationDonut();
});

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    // Check initial hash without jumping
    const hash = window.location.hash.replace('#', '');
    if (hash === 'strategies') {
        switchPortalMainTab('strategies');
    } else if (hash === 'performance') {
        switchPortalMainTab('performance');
    } else if (hash === 'positions' || hash === 'risk') {
        switchPortalMainTab('risk');
    } else if (hash === 'recent-orders' || hash === 'activity') {
        switchPortalMainTab('activity');
    } else if (hash === 'trade') {
        switchPortalMainTab('trade');
    } else if (hash === 'agents') {
        switchPortalMainTab('agents');
    } else {
        switchPortalMainTab('overview');
    }

    setTimeout(() => {
        drawEquityCurve();
        drawAllocationDonut();
    }, 100);

    startLiveTickerPulse();
});

// Window Exports
window.switchPortalMainTab = switchPortalMainTab;
window.drawEquityCurve = drawEquityCurve;
window.drawAllocationDonut = drawAllocationDonut;
window.toggleMasterCopy = toggleMasterCopy;
window.emergencyCloseAll = emergencyCloseAll;
window.closePosition = closePosition;
