// === CLIENT PORTAL APP LOGIC ===
async function updateClientStats() {
    try {
        const res = await fetch('/api/v1/status');
        const data = await res.json();

        // Update public KPI metrics
        const winrateEl = document.getElementById('client-winrate');
        if (winrateEl) winrateEl.innerText = data.performance.win_rate + '%';

        const tradesEl = document.getElementById('client-trades-count');
        if (tradesEl) tradesEl.innerText = data.performance.total_trades;

        const pnlPctEl = document.getElementById('client-pnl-pct');
        if (pnlPctEl) {
            const p = data.performance.avg_pnl_percent;
            pnlPctEl.innerText = (p >= 0 ? '+' : '') + p + '%';
            pnlPctEl.style.color = p >= 0 ? 'var(--emerald)' : 'var(--crimson)';
        }

        const regimeEl = document.getElementById('client-regime');
        if (regimeEl) regimeEl.innerText = 'BULLISH_TREND';

        const priceEl = document.getElementById('client-btc-price');
        if (priceEl && data.last_price > 0) {
            priceEl.innerText = '$' + data.last_price.toLocaleString(undefined, {minimumFractionDigits: 2});
        }

        // Render public trades table if on track record page
        const publicTradesTable = document.getElementById('public-trades-tbody');
        if (publicTradesTable && data.recent_trades) {
            if (data.recent_trades.length === 0) {
                publicTradesTable.innerHTML = `
                    <tr>
                        <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 30px;">
                            Chưa có dữ liệu giao dịch hoàn tất. Hệ thống đang chờ tín hiệu vào lệnh.
                        </td>
                    </tr>
                `;
            } else {
                publicTradesTable.innerHTML = '';
                data.recent_trades.forEach(t => {
                    const isWin = (t.pnl_usdt || 0) >= 0;
                    const pnlColor = isWin ? 'var(--emerald)' : 'var(--crimson)';
                    publicTradesTable.innerHTML += `
                        <tr>
                            <td><strong>${t.symbol}</strong></td>
                            <td><span class="badge ${t.side === 'BUY' ? 'badge-green' : 'badge-red'}">${t.side}</span></td>
                            <td>$${t.entry_price.toLocaleString()}</td>
                            <td>${t.exit_price ? '$' + t.exit_price.toLocaleString() : '--'}</td>
                            <td style="color: ${pnlColor}; font-weight: 700;">
                                ${t.pnl_percent ? (t.pnl_percent >= 0 ? '+' : '') + t.pnl_percent.toFixed(2) + '%' : '0.00%'}
                            </td>
                            <td><span class="badge badge-blue">${t.status}</span></td>
                        </tr>
                    `;
                });
            }
        }
    } catch (e) {
        console.error("Client stats error:", e);
    }
}

// === HOME INTERACTIVE DEMO TRADING HELPERS ===
async function homeSubmitDemo() {
    const amtInput = document.getElementById('home-demo-amt');
    const amount = parseFloat(amtInput ? amtInput.value : 50) || 50.0;
    
    try {
        const res = await fetch('/api/v1/demo/place_order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                side: 'BUY',
                amount_usdt: amount,
                sl_pct: 0.015,
                tp_pct: 0.030,
                force: true
            })
        });
        const data = await res.json();
        if (res.ok) {
            alert("🎉 " + data.message + "\n\n👉 Kiểm tra bot Telegram @tienductradev1_bot để xem thông báo khớp lệnh!");
        } else {
            alert("❌ Lỗi: " + (data.detail || data.message));
        }
    } catch (e) {
        alert("Lỗi gửi lệnh: " + e);
    }
}

async function homeSimulate(changePct) {
    try {
        const res = await fetch('/api/v1/demo/simulate_tick', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ change_pct: changePct })
        });
        const data = await res.json();
        alert("🔔 " + data.message);
    } catch (e) {
        alert("Lỗi mô phỏng: " + e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateClientStats();
    setInterval(updateClientStats, 3000);
});

