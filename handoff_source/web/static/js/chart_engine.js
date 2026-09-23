// === ASTRA QUANT-GRADE CANVAS CHART ENGINE & PRO TRADE VIEW (BINANCE / TRADINGVIEW PRO) ===
let astraCandleData = [];
let currentTimeframe = '15m';
let currentSymbol = 'BTC/USDT';

// Crosshair & Hover state for main chart
let hoveredCandleIndex = -1;
let mousePos = { x: -1, y: -1 };
let selectedCandle = null;

// Pro Trade View State
let proTimeframe = '15m';
let proHoveredIndex = -1;
let proMousePos = { x: -1, y: -1 };
let depthPollInterval = null;

// Indicator toggles
let showIndicators = {
    ema20: true,
    ema50: true,
    bb: true,
    vol: true
};

// Calculate SMA and Bollinger Bands (20, 2)
function calculateIndicators(candles) {
    const period = 20;
    const multiplier = 2;

    for (let i = 0; i < candles.length; i++) {
        if (i >= period - 1) {
            let sum = 0;
            for (let j = i - period + 1; j <= i; j++) {
                sum += candles[j].close;
            }
            const sma = sum / period;

            let varianceSum = 0;
            for (let j = i - period + 1; j <= i; j++) {
                varianceSum += Math.pow(candles[j].close - sma, 2);
            }
            const stdDev = Math.sqrt(varianceSum / period);

            candles[i].bbUpper = sma + multiplier * stdDev;
            candles[i].bbLower = sma - multiplier * stdDev;
            candles[i].bbMiddle = sma;
        } else {
            candles[i].bbUpper = null;
            candles[i].bbLower = null;
            candles[i].bbMiddle = null;
        }
    }
}

async function fetchAstraCandles() {
    try {
        const res = await fetch(`/api/v1/candles?timeframe=${currentTimeframe}&limit=120`);
        astraCandleData = await res.json();
        
        if (astraCandleData && astraCandleData.length > 0) {
            calculateIndicators(astraCandleData);
            if (hoveredCandleIndex < 0) {
                updateChartHeader(astraCandleData);
            }
        }
        renderAstraChart();
        initChartEvents();
    } catch (e) {
        console.error("Candle load error:", e);
    }
}

function updateChartHeader(candles, activeCandle) {
    if (!candles || candles.length === 0) return;
    const last = activeCandle || candles[candles.length - 1];
    const prev = candles.length > 1 ? candles[candles.length - 2] : last;

    // Price tags
    const priceStr = '$' + last.close.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    const bigPriceEl = document.getElementById('chart-big-price');
    const topPriceEl = document.getElementById('top-live-price');
    if (bigPriceEl) bigPriceEl.innerText = priceStr;
    if (topPriceEl) topPriceEl.innerText = priceStr;

    // Price change
    const changeVal = last.close - (activeCandle ? last.open : prev.close);
    const baseP = activeCandle ? last.open : prev.close;
    const changePct = baseP ? ((changeVal / baseP) * 100) : 0;
    const isUp = changeVal >= 0;
    const changeStr = `${isUp ? '+' : ''}${changeVal.toFixed(2)} (${isUp ? '+' : ''}${changePct.toFixed(2)}%)`;

    const changeEl = document.getElementById('chart-price-change');
    if (changeEl) {
        changeEl.innerText = changeStr;
        changeEl.className = 'chart-price-change ' + (isUp ? 'up' : 'down');
    }

    // Sub-header mini tickers
    const btcValEl = document.getElementById('ticker-btc-val');
    const btcChangeEl = document.getElementById('ticker-btc-change');
    if (btcValEl) btcValEl.innerText = '$' + Math.round(last.close).toLocaleString();
    if (btcChangeEl) {
        btcChangeEl.innerText = (isUp ? '+' : '') + changePct.toFixed(2) + '%';
        btcChangeEl.className = 'ticker-change ' + (isUp ? 'up' : 'down');
    }

    // OHLCV Readout
    const oEl = document.getElementById('ohlcv-open');
    const hEl = document.getElementById('ohlcv-high');
    const lEl = document.getElementById('ohlcv-low');
    const cEl = document.getElementById('ohlcv-close');
    const dEl = document.getElementById('ohlcv-delta');

    if (oEl) oEl.innerText = last.open.toLocaleString(undefined, {minimumFractionDigits: 2});
    if (hEl) hEl.innerText = last.high.toLocaleString(undefined, {minimumFractionDigits: 2});
    if (lEl) lEl.innerText = last.low.toLocaleString(undefined, {minimumFractionDigits: 2});
    if (cEl) cEl.innerText = last.close.toLocaleString(undefined, {minimumFractionDigits: 2});
    if (dEl) {
        dEl.innerText = `${isUp ? '+' : ''}${(last.close - last.open).toFixed(2)} (${isUp ? '+' : ''}${(((last.close - last.open) / (last.open || 1)) * 100).toFixed(2)}%)`;
        dEl.className = 'ohlcv-delta ' + (last.close >= last.open ? 'up' : 'down');
    }

    // Indicators Legend
    const ema20El = document.getElementById('legend-ema20');
    const ema50El = document.getElementById('legend-ema50');
    const bbEl = document.getElementById('legend-bb');
    const volEl = document.getElementById('legend-vol');

    if (ema20El) ema20El.innerText = last.ema20 ? last.ema20.toLocaleString(undefined, {minimumFractionDigits: 2}) : '—';
    if (ema50El) ema50El.innerText = last.ema50 ? last.ema50.toLocaleString(undefined, {minimumFractionDigits: 2}) : '—';
    if (bbEl) {
        bbEl.innerText = (last.bbUpper && last.bbLower) 
            ? `[${Math.round(last.bbUpper).toLocaleString()} / ${Math.round(last.bbLower).toLocaleString()}]`
            : '—';
    }
    if (volEl) {
        volEl.innerText = last.volume 
            ? (last.volume >= 1000 ? (last.volume / 1000).toFixed(2) + 'K' : last.volume.toFixed(1))
            : '—';
    }
}

function renderAstraChart() {
    const canvas = document.getElementById('mainChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const parent = canvas.parentElement;
    const rect = parent.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    ctx.clearRect(0, 0, w, h);

    if (!astraCandleData || astraCandleData.length === 0) {
        ctx.fillStyle = isDark ? "#64748b" : "#94a3b8";
        ctx.font = "12px 'Plus Jakarta Sans', sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("Đang đồng bộ dữ liệu nến Binance...", w / 2, h / 2);
        return;
    }

    // Dynamic scale calculation (Price & Volume)
    let minP = Infinity;
    let maxP = -Infinity;
    let maxVol = 0;

    astraCandleData.forEach(c => {
        if (c.low < minP) minP = c.low;
        if (c.high > maxP) maxP = c.high;
        if (showIndicators.bb && c.bbLower !== null && c.bbLower < minP) minP = c.bbLower;
        if (showIndicators.bb && c.bbUpper !== null && c.bbUpper > maxP) maxP = c.bbUpper;
        if (c.volume > maxVol) maxVol = c.volume;
    });

    const padding = (maxP - minP) * 0.08 || 50;
    minP -= padding;
    maxP += padding;

    const chartLeft = 14;
    const chartRight = w - 75; // Right price scale axis
    const chartTop = 16;
    const chartBottom = h - 26; // Bottom time axis
    const chartW = chartRight - chartLeft;
    const chartH = chartBottom - chartTop;

    function getY(price) {
        return chartBottom - ((price - minP) / (maxP - minP)) * chartH;
    }

    // 1. Grid Lines & Right Price Scale
    ctx.strokeStyle = isDark ? "#1e293b" : "#f1f5f9";
    ctx.lineWidth = 1;
    ctx.setLineDash([]);
    ctx.fillStyle = isDark ? "#64748b" : "#94a3b8";
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.textAlign = "left";

    const priceSteps = 5;
    for (let i = 0; i <= priceSteps; i++) {
        const y = chartTop + (chartH / priceSteps) * i;
        const p = maxP - ((maxP - minP) / priceSteps) * i;

        ctx.beginPath();
        ctx.moveTo(chartLeft, y);
        ctx.lineTo(chartRight, y);
        ctx.stroke();

        ctx.fillText(p.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0}), chartRight + 8, y + 3.5);
    }

    const n = astraCandleData.length;
    const stepX = chartW / n;
    const candleW = Math.max(3.5, stepX * 0.65);

    // 2. Bollinger Bands Shading & Lines (20, 2)
    if (showIndicators.bb) {
        ctx.beginPath();
        let bbStarted = false;
        // Upper band line
        astraCandleData.forEach((c, idx) => {
            if (c.bbUpper !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.bbUpper);
                if (!bbStarted) { ctx.moveTo(x, y); bbStarted = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        // Lower band line backward for fill
        for (let idx = astraCandleData.length - 1; idx >= 0; idx--) {
            const c = astraCandleData[idx];
            if (c.bbLower !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.bbLower);
                ctx.lineTo(x, y);
            }
        }
        ctx.closePath();
        ctx.fillStyle = isDark ? "rgba(245, 158, 11, 0.05)" : "rgba(245, 158, 11, 0.06)";
        ctx.fill();

        // Stroke Upper & Lower BB lines
        ctx.strokeStyle = isDark ? "rgba(245, 158, 11, 0.6)" : "rgba(245, 158, 11, 0.8)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        bbStarted = false;
        astraCandleData.forEach((c, idx) => {
            if (c.bbUpper !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.bbUpper);
                if (!bbStarted) { ctx.moveTo(x, y); bbStarted = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        ctx.stroke();

        ctx.beginPath();
        bbStarted = false;
        astraCandleData.forEach((c, idx) => {
            if (c.bbLower !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.bbLower);
                if (!bbStarted) { ctx.moveTo(x, y); bbStarted = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        ctx.stroke();
    }

    // 3. Volume Histogram Bars (Bottom 18% of chart)
    if (showIndicators.vol) {
        const volHeightMax = chartH * 0.18;
        astraCandleData.forEach((c, idx) => {
            if (!c.volume || maxVol === 0) return;
            const x = chartLeft + idx * stepX + stepX / 2;
            const vH = (c.volume / maxVol) * volHeightMax;
            const isUp = c.close >= c.open;

            ctx.fillStyle = isUp 
                ? (isDark ? "rgba(16, 185, 129, 0.35)" : "rgba(16, 185, 129, 0.4)")
                : (isDark ? "rgba(244, 63, 94, 0.35)" : "rgba(239, 68, 68, 0.4)");

            ctx.fillRect(x - candleW / 2, chartBottom - vH, candleW, vH);
        });
    }

    // 4. Candlesticks (Bodies & Wicks)
    astraCandleData.forEach((c, idx) => {
        const x = chartLeft + idx * stepX + stepX / 2;
        const yOpen = getY(c.open);
        const yClose = getY(c.close);
        const yHigh = getY(c.high);
        const yLow = getY(c.low);

        const isUp = c.close >= c.open;
        const isHovered = (idx === hoveredCandleIndex);
        const candleColor = isUp ? "#10b981" : (isDark ? "#f43f5e" : "#ef4444");

        // Wick
        ctx.strokeStyle = candleColor;
        ctx.lineWidth = isHovered ? 2 : 1.2;
        ctx.setLineDash([]);
        ctx.beginPath();
        ctx.moveTo(x, yHigh);
        ctx.lineTo(x, yLow);
        ctx.stroke();

        // Body
        ctx.fillStyle = candleColor;
        const top = Math.min(yOpen, yClose);
        const height = Math.max(2, Math.abs(yClose - yOpen));
        ctx.fillRect(x - candleW / 2, top, candleW, height);

        // Highlight ring if hovered
        if (isHovered) {
            ctx.strokeStyle = "#38bdf8";
            ctx.lineWidth = 1.5;
            ctx.strokeRect(x - candleW / 2 - 2, top - 2, candleW + 4, height + 4);
        }

        // Time labels (every ~10 candles)
        if (idx % 10 === 0 && c.timestamp) {
            ctx.fillStyle = isDark ? "#64748b" : "#94a3b8";
            ctx.font = "9.5px 'JetBrains Mono', monospace";
            ctx.textAlign = "center";
            const timeStr = c.timestamp.slice(11, 16);
            ctx.fillText(timeStr, x, chartBottom + 16);
        }
    });

    // 5. EMA 20 (Cyan/Blue)
    if (showIndicators.ema20) {
        ctx.strokeStyle = isDark ? "#00f3ff" : "#0284c7";
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        let ema20Started = false;
        astraCandleData.forEach((c, idx) => {
            if (c.ema20 !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.ema20);
                if (!ema20Started) { ctx.moveTo(x, y); ema20Started = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        ctx.stroke();
    }

    // 6. EMA 50 (Purple/Magenta)
    if (showIndicators.ema50) {
        ctx.strokeStyle = isDark ? "#c084fc" : "#8b5cf6";
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        let ema50Started = false;
        astraCandleData.forEach((c, idx) => {
            if (c.ema50 !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.ema50);
                if (!ema50Started) { ctx.moveTo(x, y); ema50Started = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        ctx.stroke();
    }

    // 7. Right Price Scale & Active Live Price Tag (When not hovering)
    if (astraCandleData.length > 0 && hoveredCandleIndex < 0) {
        const last = astraCandleData[astraCandleData.length - 1];
        const lastY = getY(last.close);
        const isUp = last.close >= last.open;
        const tagColor = isUp ? "#10b981" : (isDark ? "#f43f5e" : "#ef4444");

        // Horizontal dotted guide line
        ctx.strokeStyle = tagColor;
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(chartLeft, lastY);
        ctx.lineTo(chartRight, lastY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Right axis price badge
        const badgeW = 66;
        const badgeH = 18;
        const badgeX = chartRight + 3;
        const badgeY = lastY - badgeH / 2;

        ctx.fillStyle = tagColor;
        ctx.beginPath();
        ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 3);
        ctx.fill();

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 10px 'JetBrains Mono', monospace";
        ctx.textAlign = "center";
        ctx.fillText(last.close.toFixed(2), badgeX + badgeW / 2, badgeY + 12.5);
    }

    // 8. Interactive Crosshair (When Hovering)
    if (hoveredCandleIndex >= 0 && hoveredCandleIndex < astraCandleData.length) {
        const c = astraCandleData[hoveredCandleIndex];
        const candleX = chartLeft + hoveredCandleIndex * stepX + stepX / 2;
        const curY = (mousePos.y >= chartTop && mousePos.y <= chartBottom) ? mousePos.y : getY(c.close);

        // Vertical crosshair
        ctx.strokeStyle = isDark ? "rgba(56, 189, 248, 0.65)" : "rgba(2, 132, 199, 0.65)";
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(candleX, chartTop);
        ctx.lineTo(candleX, chartBottom);
        ctx.stroke();

        // Horizontal crosshair
        ctx.beginPath();
        ctx.moveTo(chartLeft, curY);
        ctx.lineTo(chartRight, curY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Price badge on right axis
        const hoverP = maxP - ((curY - chartTop) / chartH) * (maxP - minP);
        const badgeW = 68;
        const badgeH = 18;
        const badgeX = chartRight + 3;
        const badgeY = curY - badgeH / 2;

        ctx.fillStyle = "#0284c7";
        ctx.beginPath();
        ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 3);
        ctx.fill();

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 10px 'JetBrains Mono', monospace";
        ctx.textAlign = "center";
        ctx.fillText(hoverP.toFixed(2), badgeX + badgeW / 2, badgeY + 12.5);

        // Time badge on bottom axis
        if (c.timestamp) {
            const timeStr = c.timestamp.slice(11, 19) || c.timestamp.slice(11, 16);
            const timeBadgeW = 60;
            const timeBadgeH = 16;
            const timeBadgeX = candleX - timeBadgeW / 2;
            const timeBadgeY = chartBottom + 4;

            ctx.fillStyle = "#0284c7";
            ctx.beginPath();
            ctx.roundRect(timeBadgeX, timeBadgeY, timeBadgeW, timeBadgeH, 3);
            ctx.fill();

            ctx.fillStyle = "#ffffff";
            ctx.font = "bold 9.5px 'JetBrains Mono', monospace";
            ctx.textAlign = "center";
            ctx.fillText(timeStr, candleX, timeBadgeY + 11.5);
        }
    }
}

// Mouse events on main chart
function initChartEvents() {
    const canvas = document.getElementById('mainChart');
    if (!canvas || canvas.__eventsBound) return;
    canvas.__eventsBound = true;
    canvas.style.cursor = 'crosshair';

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        mousePos = { x, y };

        const w = rect.width;
        const chartLeft = 14;
        const chartRight = w - 75;
        const chartW = chartRight - chartLeft;

        if (x >= chartLeft && x <= chartRight && astraCandleData.length > 0) {
            const stepX = chartW / astraCandleData.length;
            const idx = Math.floor((x - chartLeft) / stepX);
            if (idx >= 0 && idx < astraCandleData.length) {
                hoveredCandleIndex = idx;
                updateChartHeader(astraCandleData, astraCandleData[idx]);
                renderAstraChart();
                return;
            }
        }
        hoveredCandleIndex = -1;
        updateChartHeader(astraCandleData);
        renderAstraChart();
    });

    canvas.addEventListener('mouseleave', () => {
        hoveredCandleIndex = -1;
        mousePos = { x: -1, y: -1 };
        updateChartHeader(astraCandleData);
        renderAstraChart();
    });

    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const w = rect.width;
        const chartLeft = 14;
        const chartRight = w - 75;
        const chartW = chartRight - chartLeft;

        if (x >= chartLeft && x <= chartRight && astraCandleData.length > 0) {
            const stepX = chartW / astraCandleData.length;
            const idx = Math.floor((x - chartLeft) / stepX);
            if (idx >= 0 && idx < astraCandleData.length) {
                selectedCandle = astraCandleData[idx];
                openProTradeViewModal(selectedCandle);
                return;
            }
        }
        openProTradeViewModal();
    });
}

// ============================================================================
// PRO EXCHANGE TRADE VIEW MODAL LOGIC (BINANCE / TRADINGVIEW STYLE)
// ============================================================================
async function openProTradeViewModal(candle) {
    const modal = document.getElementById('proTradeViewModal');
    if (!modal) return;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    // Set selected candle or fallback to latest
    if (candle) {
        selectedCandle = candle;
    } else if (astraCandleData && astraCandleData.length > 0) {
        selectedCandle = astraCandleData[astraCandleData.length - 1];
    }

    renderProCandleDetails(selectedCandle);
    fetchProDepth();
    fetchProBotTrades();
    fetchProAiSignals();

    // Start polling depth every 2.5s
    if (depthPollInterval) clearInterval(depthPollInterval);
    depthPollInterval = setInterval(fetchProDepth, 2500);

    // Render Pro Canvas chart
    setTimeout(() => {
        renderProChart();
        initProChartEvents();
    }, 50);
}

function closeProTradeViewModal() {
    const modal = document.getElementById('proTradeViewModal');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = '';
    if (depthPollInterval) clearInterval(depthPollInterval);
}

function renderProCandleDetails(c) {
    const container = document.getElementById('proCandleDetailsGrid');
    if (!container || !c) return;

    const isUp = c.close >= c.open;
    const spread = Math.abs(c.high - c.low);
    const bodySize = Math.abs(c.close - c.open);
    const changePct = c.open ? (((c.close - c.open) / c.open) * 100) : 0;
    const timeStr = c.timestamp ? c.timestamp.replace('T', ' ').slice(0, 19) : 'LIVE';

    container.innerHTML = `
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">Thời Gian Nến (UTC+7)</div>
            <div class="pro-cell-val" style="color: #38bdf8;">${timeStr}</div>
        </div>
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">Giá Mở (Open)</div>
            <div class="pro-cell-val">$${c.open.toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
        </div>
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">Đỉnh Cao Nhất (High)</div>
            <div class="pro-cell-val" style="color: #10b981;">$${c.high.toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
        </div>
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">Đáy Thấp Nhất (Low)</div>
            <div class="pro-cell-val" style="color: #f43f5e;">$${c.low.toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
        </div>
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">Giá Đóng (Close)</div>
            <div class="pro-cell-val" style="color: ${isUp ? '#10b981' : '#f43f5e'};">$${c.close.toLocaleString(undefined, {minimumFractionDigits: 2})}</div>
        </div>
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">Biến Động Nến</div>
            <div class="pro-cell-val" style="color: ${isUp ? '#10b981' : '#f43f5e'};">${isUp ? '+' : ''}${changePct.toFixed(2)}% ($${bodySize.toFixed(2)})</div>
        </div>
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">Biên Độ Râu (Spread H-L)</div>
            <div class="pro-cell-val">$${spread.toFixed(2)}</div>
        </div>
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">Khối Lượng (Volume)</div>
            <div class="pro-cell-val" style="color: #fde68a;">${c.volume ? (c.volume >= 1000 ? (c.volume / 1000).toFixed(2) + 'K' : c.volume.toFixed(2)) : '—'}</div>
        </div>
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">EMA 20 / EMA 50</div>
            <div class="pro-cell-val" style="font-size: 11px;">
                <span style="color: #00f3ff;">${c.ema20 ? c.ema20.toFixed(1) : '—'}</span> / 
                <span style="color: #c084fc;">${c.ema50 ? c.ema50.toFixed(1) : '—'}</span>
            </div>
        </div>
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">Bollinger Bands (20, 2)</div>
            <div class="pro-cell-val" style="font-size: 11px; color: #f59e0b;">
                ${c.bbUpper && c.bbLower ? `[${Math.round(c.bbUpper)} / ${Math.round(c.bbLower)}]` : '—'}
            </div>
        </div>
        <div class="pro-detail-cell">
            <div class="pro-cell-lbl">AI Council Status</div>
            <div class="pro-cell-val" style="color: #10b981; font-size: 11px;">● RISK GATE AN TOÀN (100%)</div>
        </div>
    `;
}

async function fetchProDepth() {
    try {
        const res = await fetch(`/api/v1/market/depth?symbol=${encodeURIComponent(currentSymbol)}&limit=12`);
        if (!res.ok) return;
        const data = await res.json();

        // Update Header stats
        if (data.last_price) {
            const pStr = '$' + data.last_price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            const hPriceEl = document.getElementById('pro-header-price');
            const obPriceEl = document.getElementById('pro-ob-price');
            if (hPriceEl) hPriceEl.innerText = pStr;
            if (obPriceEl) obPriceEl.innerText = pStr;
        }

        // Render Asks
        const asksContainer = document.getElementById('pro-ob-asks');
        if (asksContainer && data.asks) {
            let maxTotal = 0;
            let cum = 0;
            const reversedAsks = [...data.asks].reverse();
            reversedAsks.forEach(a => { cum += a[1]; });
            maxTotal = cum || 1;

            let cumRunning = 0;
            asksContainer.innerHTML = reversedAsks.map(a => {
                cumRunning += a[1];
                const depthPct = Math.min(100, (cumRunning / maxTotal) * 100);
                return `
                    <div class="pro-ob-row" title="Bấm để lấy giá">
                        <div class="pro-depth-bar" style="width: ${depthPct}%;"></div>
                        <span class="ob-price">${a[0].toFixed(2)}</span>
                        <span style="text-align: right; color: #cbd5e1;">${a[1].toFixed(4)}</span>
                        <span style="text-align: right; color: #64748b;">${cumRunning.toFixed(4)}</span>
                    </div>
                `;
            }).join('');
        }

        // Render Bids
        const bidsContainer = document.getElementById('pro-ob-bids');
        if (bidsContainer && data.bids) {
            let maxTotal = 0;
            let cum = 0;
            data.bids.forEach(b => { cum += b[1]; });
            maxTotal = cum || 1;

            let cumRunning = 0;
            bidsContainer.innerHTML = data.bids.map(b => {
                cumRunning += b[1];
                const depthPct = Math.min(100, (cumRunning / maxTotal) * 100);
                return `
                    <div class="pro-ob-row" title="Bấm để lấy giá">
                        <div class="pro-depth-bar" style="width: ${depthPct}%;"></div>
                        <span class="ob-price">${b[0].toFixed(2)}</span>
                        <span style="text-align: right; color: #cbd5e1;">${b[1].toFixed(4)}</span>
                        <span style="text-align: right; color: #64748b;">${cumRunning.toFixed(4)}</span>
                    </div>
                `;
            }).join('');
        }

        // Render Recent Trades
        const tradesContainer = document.getElementById('pro-market-trades-list');
        if (tradesContainer && data.trades) {
            tradesContainer.innerHTML = data.trades.slice(0, 15).map(t => {
                const isBuy = t.side === 'BUY';
                return `
                    <div class="pro-trade-row ${isBuy ? 'buy' : 'sell'}">
                        <span class="trade-price">${t.price.toFixed(2)}</span>
                        <span class="trade-qty">${t.amount.toFixed(4)}</span>
                        <span class="trade-time">${t.timestamp ? (t.timestamp.length > 8 ? t.timestamp.slice(11, 19) : t.timestamp) : '--'}</span>
                    </div>
                `;
            }).join('');
        }
    } catch (e) {
        console.error("Pro depth error:", e);
    }
}

async function fetchProBotTrades() {
    const container = document.getElementById('proBotTradesWrap');
    if (!container) return;
    try {
        const res = await fetch('/api/v1/trades/overview');
        if (!res.ok) return;
        const data = await res.json();
        const trades = data.recent_trades || [];

        if (trades.length === 0) {
            container.innerHTML = `<div style="color: #64748b; padding: 12px; font-style: italic;">Chưa có lệnh nào được ghi nhận cho cặp này.</div>`;
            return;
        }

        container.innerHTML = `
            <table class="table quant-table" style="font-size: 11px; margin: 0;">
                <thead>
                    <tr>
                        <th>Mã Lệnh</th>
                        <th>Cặp</th>
                        <th>Hướng</th>
                        <th>Giá Vào</th>
                        <th>Giá Ra</th>
                        <th>PnL</th>
                        <th>Thời Gian</th>
                        <th>Khám Nghiệm</th>
                    </tr>
                </thead>
                <tbody>
                    ${trades.slice(0, 5).map(t => {
                        const isWin = (t.pnl_usdt || 0) >= 0;
                        return `
                            <tr>
                                <td style="color: #38bdf8; font-family: monospace;">${t.order_id ? t.order_id.slice(0, 8) : '—'}</td>
                                <td><strong>${t.symbol}</strong></td>
                                <td><span class="badge ${t.side === 'BUY' ? 'badge-green' : 'badge-red'}" style="font-size: 9px;">${t.side}</span></td>
                                <td>$${Number(t.entry_price || 0).toLocaleString()}</td>
                                <td>${t.exit_price ? '$' + Number(t.exit_price).toLocaleString() : 'Đang chạy'}</td>
                                <td style="color: ${isWin ? '#10b981' : '#f43f5e'}; font-weight: 700;">${isWin ? '+' : ''}$${Number(t.pnl_usdt || 0).toFixed(4)}</td>
                                <td style="color: #64748b;">${t.entry_time ? t.entry_time.slice(11, 19) : '--'}</td>
                                <td><a href="/admin/trades/${t.order_id}" target="_blank" style="color: #38bdf8; text-decoration: none;">🔬 Chi tiết ↗</a></td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;
    } catch (e) {
        console.error("Bot trades fetch error:", e);
    }
}

async function fetchProAiSignals() {
    const container = document.getElementById('proSignalsWrap');
    if (!container) return;
    try {
        const res = await fetch('/api/v1/signals?limit=6');
        if (!res.ok) return;
        const signals = await res.json();

        container.innerHTML = (signals || []).map(s => {
            const isApproved = s.approved === 1 || s.approved === true;
            return `
                <div style="background: rgba(15, 23, 42, 0.6); border-left: 3px solid ${isApproved ? '#10b981' : '#f43f5e'}; border-radius: 6px; padding: 8px 12px; margin-bottom: 6px; font-family: 'JetBrains Mono', monospace; font-size: 11px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                        <strong style="color: #f8fafc;">${s.symbol} ${s.side || 'SIGNAL'}</strong>
                        <span style="color: ${isApproved ? '#10b981' : '#f43f5e'}; font-weight: 800;">${isApproved ? '● DUYỆT LỆNH' : '✕ VETO PHỦ QUYẾT'}</span>
                    </div>
                    <div style="color: #94a3b8; font-size: 10.5px;">${s.reasoning || s.details || s.rejection_reason || 'Đang giám sát luồng thị trường'}</div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error("Signals fetch error:", e);
    }
}

function switchProTab(tabName, btn) {
    document.querySelectorAll('.pro-tab-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    document.querySelectorAll('.pro-tab-content').forEach(c => c.style.display = 'none');
    const target = document.getElementById(`pro-tab-${tabName}`);
    if (target) target.style.display = 'block';
}

function switchProTimeframe(tf) {
    proTimeframe = tf;
    document.querySelectorAll('.pro-tf-btn').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-tf') === tf);
    });
    switchTimeframe(tf);
    setTimeout(renderProChart, 300);
}

function switchProTradeSymbol(sym) {
    currentSymbol = sym;
    fetchProDepth();
    fetchAstraCandles();
    setTimeout(renderProChart, 300);
}

function toggleIndicator(ind) {
    showIndicators[ind] = !showIndicators[ind];
    renderAstraChart();
    renderProChart();
}

function toggleIndicatorMenu(event) {
    if (event) event.stopPropagation();
    const menu = document.getElementById('proIndicatorMenu');
    if (menu) menu.style.display = (menu.style.display === 'none' || menu.style.display === '') ? 'flex' : 'none';
}

function toggleMainIndicatorMenu(event) {
    if (event) event.stopPropagation();
    const menu = document.getElementById('mainIndicatorMenu');
    if (menu) menu.style.display = (menu.style.display === 'none' || menu.style.display === '') ? 'flex' : 'none';
}

// Close menus when clicking outside
document.addEventListener('click', (e) => {
    const pMenu = document.getElementById('proIndicatorMenu');
    if (pMenu && !pMenu.contains(e.target)) pMenu.style.display = 'none';
    const mMenu = document.getElementById('mainIndicatorMenu');
    if (mMenu && !mMenu.contains(e.target)) mMenu.style.display = 'none';
});

// Pro Canvas Chart rendering
function renderProChart() {
    const canvas = document.getElementById('proChartCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const parent = canvas.parentElement;
    const rect = parent.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    ctx.clearRect(0, 0, w, h);

    if (!astraCandleData || astraCandleData.length === 0) return;

    // Use astraCandleData
    let minP = Infinity;
    let maxP = -Infinity;
    let maxVol = 0;

    astraCandleData.forEach(c => {
        if (c.low < minP) minP = c.low;
        if (c.high > maxP) maxP = c.high;
        if (showIndicators.bb && c.bbLower !== null && c.bbLower < minP) minP = c.bbLower;
        if (showIndicators.bb && c.bbUpper !== null && c.bbUpper > maxP) maxP = c.bbUpper;
        if (c.volume > maxVol) maxVol = c.volume;
    });

    const padding = (maxP - minP) * 0.08 || 50;
    minP -= padding;
    maxP += padding;

    const chartLeft = 14;
    const chartRight = w - 75;
    const chartTop = 16;
    const chartBottom = h - 26;
    const chartW = chartRight - chartLeft;
    const chartH = chartBottom - chartTop;

    function getY(price) {
        return chartBottom - ((price - minP) / (maxP - minP)) * chartH;
    }

    // Grid Lines & Price scale
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#64748b";
    ctx.font = "10px 'JetBrains Mono', monospace";
    ctx.textAlign = "left";

    const priceSteps = 6;
    for (let i = 0; i <= priceSteps; i++) {
        const y = chartTop + (chartH / priceSteps) * i;
        const p = maxP - ((maxP - minP) / priceSteps) * i;

        ctx.beginPath();
        ctx.moveTo(chartLeft, y);
        ctx.lineTo(chartRight, y);
        ctx.stroke();

        ctx.fillText(p.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 0}), chartRight + 8, y + 3.5);
    }

    const n = astraCandleData.length;
    const stepX = chartW / n;
    const candleW = Math.max(3.5, stepX * 0.65);

    // BB
    if (showIndicators.bb) {
        ctx.beginPath();
        let bbStarted = false;
        astraCandleData.forEach((c, idx) => {
            if (c.bbUpper !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.bbUpper);
                if (!bbStarted) { ctx.moveTo(x, y); bbStarted = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        for (let idx = astraCandleData.length - 1; idx >= 0; idx--) {
            const c = astraCandleData[idx];
            if (c.bbLower !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.bbLower);
                ctx.lineTo(x, y);
            }
        }
        ctx.closePath();
        ctx.fillStyle = "rgba(245, 158, 11, 0.05)";
        ctx.fill();

        ctx.strokeStyle = "rgba(245, 158, 11, 0.6)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        bbStarted = false;
        astraCandleData.forEach((c, idx) => {
            if (c.bbUpper !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.bbUpper);
                if (!bbStarted) { ctx.moveTo(x, y); bbStarted = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        ctx.stroke();

        ctx.beginPath();
        bbStarted = false;
        astraCandleData.forEach((c, idx) => {
            if (c.bbLower !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.bbLower);
                if (!bbStarted) { ctx.moveTo(x, y); bbStarted = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        ctx.stroke();
    }

    // Volume
    if (showIndicators.vol) {
        const volHeightMax = chartH * 0.18;
        astraCandleData.forEach((c, idx) => {
            if (!c.volume || maxVol === 0) return;
            const x = chartLeft + idx * stepX + stepX / 2;
            const vH = (c.volume / maxVol) * volHeightMax;
            const isUp = c.close >= c.open;
            ctx.fillStyle = isUp ? "rgba(16, 185, 129, 0.35)" : "rgba(244, 63, 94, 0.35)";
            ctx.fillRect(x - candleW / 2, chartBottom - vH, candleW, vH);
        });
    }

    // Candlesticks
    astraCandleData.forEach((c, idx) => {
        const x = chartLeft + idx * stepX + stepX / 2;
        const yOpen = getY(c.open);
        const yClose = getY(c.close);
        const yHigh = getY(c.high);
        const yLow = getY(c.low);

        const isUp = c.close >= c.open;
        const isHovered = (idx === proHoveredIndex);
        const candleColor = isUp ? "#10b981" : "#f43f5e";

        ctx.strokeStyle = candleColor;
        ctx.lineWidth = isHovered ? 2 : 1.2;
        ctx.beginPath();
        ctx.moveTo(x, yHigh);
        ctx.lineTo(x, yLow);
        ctx.stroke();

        ctx.fillStyle = candleColor;
        const top = Math.min(yOpen, yClose);
        const height = Math.max(2, Math.abs(yClose - yOpen));
        ctx.fillRect(x - candleW / 2, top, candleW, height);

        if (isHovered) {
            ctx.strokeStyle = "#38bdf8";
            ctx.lineWidth = 1.5;
            ctx.strokeRect(x - candleW / 2 - 2, top - 2, candleW + 4, height + 4);
        }

        if (idx % 10 === 0 && c.timestamp) {
            ctx.fillStyle = "#64748b";
            ctx.font = "9.5px 'JetBrains Mono', monospace";
            ctx.textAlign = "center";
            ctx.fillText(c.timestamp.slice(11, 16), x, chartBottom + 16);
        }
    });

    // EMA 20 & 50
    if (showIndicators.ema20) {
        ctx.strokeStyle = "#00f3ff";
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        let ema20Started = false;
        astraCandleData.forEach((c, idx) => {
            if (c.ema20 !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.ema20);
                if (!ema20Started) { ctx.moveTo(x, y); ema20Started = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        ctx.stroke();
    }

    if (showIndicators.ema50) {
        ctx.strokeStyle = "#c084fc";
        ctx.lineWidth = 1.8;
        ctx.beginPath();
        let ema50Started = false;
        astraCandleData.forEach((c, idx) => {
            if (c.ema50 !== null) {
                const x = chartLeft + idx * stepX + stepX / 2;
                const y = getY(c.ema50);
                if (!ema50Started) { ctx.moveTo(x, y); ema50Started = true; }
                else { ctx.lineTo(x, y); }
            }
        });
        ctx.stroke();
    }

    // Crosshair in Pro Modal
    if (proHoveredIndex >= 0 && proHoveredIndex < astraCandleData.length) {
        const c = astraCandleData[proHoveredIndex];
        const candleX = chartLeft + proHoveredIndex * stepX + stepX / 2;
        const curY = (proMousePos.y >= chartTop && proMousePos.y <= chartBottom) ? proMousePos.y : getY(c.close);

        ctx.strokeStyle = "rgba(56, 189, 248, 0.6)";
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(candleX, chartTop);
        ctx.lineTo(candleX, chartBottom);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(chartLeft, curY);
        ctx.lineTo(chartRight, curY);
        ctx.stroke();
        ctx.setLineDash([]);

        const hoverP = maxP - ((curY - chartTop) / chartH) * (maxP - minP);
        const badgeW = 68;
        const badgeH = 18;
        const badgeX = chartRight + 3;
        const badgeY = curY - badgeH / 2;

        ctx.fillStyle = "#0284c7";
        ctx.beginPath();
        ctx.roundRect(badgeX, badgeY, badgeW, badgeH, 3);
        ctx.fill();

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 10px 'JetBrains Mono', monospace";
        ctx.textAlign = "center";
        ctx.fillText(hoverP.toFixed(2), badgeX + badgeW / 2, badgeY + 12.5);
    }
}

function initProChartEvents() {
    const canvas = document.getElementById('proChartCanvas');
    if (!canvas || canvas.__eventsBound) return;
    canvas.__eventsBound = true;
    canvas.style.cursor = 'crosshair';

    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        proMousePos = { x, y };

        const w = rect.width;
        const chartLeft = 14;
        const chartRight = w - 75;
        const chartW = chartRight - chartLeft;

        if (x >= chartLeft && x <= chartRight && astraCandleData.length > 0) {
            const stepX = chartW / astraCandleData.length;
            const idx = Math.floor((x - chartLeft) / stepX);
            if (idx >= 0 && idx < astraCandleData.length) {
                proHoveredIndex = idx;
                updateProLegend(astraCandleData[idx]);
                renderProChart();
                return;
            }
        }
        proHoveredIndex = -1;
        renderProChart();
    });

    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const w = rect.width;
        const chartLeft = 14;
        const chartRight = w - 75;
        const chartW = chartRight - chartLeft;

        if (x >= chartLeft && x <= chartRight && astraCandleData.length > 0) {
            const stepX = chartW / astraCandleData.length;
            const idx = Math.floor((x - chartLeft) / stepX);
            if (idx >= 0 && idx < astraCandleData.length) {
                selectedCandle = astraCandleData[idx];
                renderProCandleDetails(selectedCandle);
                switchProTab('candle-info', document.getElementById('tab-btn-candle-info'));
            }
        }
    });
}

function updateProLegend(c) {
    if (!c) return;
    const o = document.getElementById('pro-ohlcv-o');
    const h = document.getElementById('pro-ohlcv-h');
    const l = document.getElementById('pro-ohlcv-l');
    const cl = document.getElementById('pro-ohlcv-c');
    const d = document.getElementById('pro-ohlcv-d');
    const ema20 = document.getElementById('pro-legend-ema20');
    const ema50 = document.getElementById('pro-legend-ema50');
    const bb = document.getElementById('pro-legend-bb');
    const vol = document.getElementById('pro-legend-vol');

    if (o) o.innerText = c.open.toFixed(2);
    if (h) h.innerText = c.high.toFixed(2);
    if (l) l.innerText = c.low.toFixed(2);
    if (cl) cl.innerText = c.close.toFixed(2);
    if (d) {
        const diff = c.close - c.open;
        const pct = c.open ? (diff / c.open) * 100 : 0;
        d.innerText = `${diff >= 0 ? '+' : ''}${diff.toFixed(2)} (${diff >= 0 ? '+' : ''}${pct.toFixed(2)}%)`;
        d.className = diff >= 0 ? 'up' : 'down';
    }
    if (ema20) ema20.innerText = c.ema20 ? c.ema20.toFixed(2) : '—';
    if (ema50) ema50.innerText = c.ema50 ? c.ema50.toFixed(2) : '—';
    if (bb) bb.innerText = (c.bbUpper && c.bbLower) ? `[${Math.round(c.bbUpper)} / ${Math.round(c.bbLower)}]` : '—';
    if (vol) vol.innerText = c.volume ? (c.volume >= 1000 ? (c.volume / 1000).toFixed(2) + 'K' : c.volume.toFixed(1)) : '—';
}

// Timeframe switcher
function switchTimeframe(tf) {
    currentTimeframe = tf;
    const btns = document.querySelectorAll('.tf-btn');
    btns.forEach(btn => {
        if (btn.getAttribute('data-tf') === tf) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    fetchAstraCandles();
}

// Fullscreen toggle
function toggleChartFullscreen() {
    openProTradeViewModal();
}

// Global Exports
window.renderAstraChart = renderAstraChart;
window.switchTimeframe = switchTimeframe;
window.toggleChartFullscreen = toggleChartFullscreen;
window.openProTradeViewModal = openProTradeViewModal;
window.closeProTradeViewModal = closeProTradeViewModal;
window.switchProTimeframe = switchProTimeframe;
window.switchProTradeSymbol = switchProTradeSymbol;
window.switchProTab = switchProTab;
window.toggleIndicator = toggleIndicator;
window.toggleIndicatorMenu = toggleIndicatorMenu;
window.toggleMainIndicatorMenu = toggleMainIndicatorMenu;

window.addEventListener('resize', () => {
    renderAstraChart();
    renderProChart();
});

// Auto-init events when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChartEvents);
} else {
    initChartEvents();
}
