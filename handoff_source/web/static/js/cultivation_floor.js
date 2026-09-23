/* Presentation only. No network calls, trade commands or agent-state writes. */
(() => {
    'use strict';
    const host = document.querySelector('.pixel-floor-wrapper');
    if (!host) return;
    const rooms = [
        ['lead_pm', 'Vân Đài', 'PM Lead', 'sprite_01_pm.png', '01'],
        ['risk_council', 'Hộ Tâm Viện', 'Risk Council', 'sprite_02_risk.png', '02'],
        ['fast_scout', 'Thiên Nhãn Đài', 'Fast Scout', 'sprite_03_scout.png', '03'],
        ['quant_lab', 'Diễn Toán Các', 'Quant Lab', 'sprite_04_quant.png', '04'],
        ['execution_oms', 'Chấp Lệnh Đường', 'Execution OMS', 'sprite_05_execution.png', '05'],
        ['community_affiliate', 'Liên Minh Các', 'Community / Affiliate', 'sprite_06_community.png', '06']
    ];
    const key = 'astra.cosmetic.exploration.v1';
    let visited = new Set();
    let persistent = true;
    try {
        const saved = JSON.parse(localStorage.getItem(key) || '[]');
        if (Array.isArray(saved)) visited = new Set(saved.filter(id => rooms.some(r => r[0] === id)));
    } catch (_) { persistent = false; }
    const root = document.createElement('section');
    root.className = 'cultivation-floor';
    root.setAttribute('aria-label', 'Thiên Cơ Các — Tổng Hành Dinh Quant Thực Chiến');
    root.innerHTML = `
        <header class="cult-head"><div><span class="cult-kicker">ASTRA / MODERN CULTIVATION</span>
        <h2>Thiên Cơ Các</h2><p>Một công ty. Sáu phòng ban. Cùng một hành trình.</p></div>
        <button type="button" class="cult-motion" aria-pressed="false">Tắt chuyển động</button></header>
        <div class="cult-toolbar"><span>TỔNG HÀNH DINH QUANT THỰC CHIẾN • DỮ LIỆU TELEMETRY THỜI GIAN THỰC</span><span class="cult-rank"></span></div>
        <div class="cult-campus">${rooms.map(([id, name, role, sprite, number]) => `
            <button type="button" class="cult-room" data-room="${id}" aria-pressed="false">
                <span class="cult-room-number">${number} / PHÒNG BAN</span>
                <strong>${name}</strong><span class="cult-role">${role}</span>
                <span class="cult-office" aria-hidden="true"><span class="cult-window"></span><span class="cult-desk"></span>
                <img class="cult-actor" src="/static/images/sprites/${sprite}" alt="" loading="lazy"></span>
                <span class="cult-room-state">Mở hồ sơ phòng ban →</span>
            </button>`).join('')}</div>
        <div class="cult-bottom"><section class="cult-detail" aria-live="polite" aria-atomic="true">
            <span class="cult-kicker">HỒ SƠ PHÒNG BAN</span><h3>Chọn một phòng để khám phá</h3>
            <p class="cult-evidence">Hội đồng phòng ban tự hành phối hợp phân tích đa tầng, kiểm soát rủi ro và thực thi lệnh trực tiếp.</p>
        </section><section class="cult-journey"><span class="cult-kicker">HÀNH TRÌNH KHÁM PHÁ</span>
            <p class="cult-progress-label"></p><progress max="6" value="0" aria-label="Số phòng đã khám phá"></progress>
            <p>Nhập môn → Luyện khí (3 phòng) → Trúc cơ (6 phòng).</p>
            <button type="button" class="cult-theme" disabled>Mở sắc ngọc · khám phá 3 phòng</button>
            <small class="cult-save-note"></small>
        </section></div>`;
    host.prepend(root);
    let active = null;
    const detail = root.querySelector('.cult-detail');
    function renderDetail() {
        if (!active) return;
        const room = rooms.find(r => r[0] === active);
        const telemetry = typeof currentTelemetry !== 'undefined' ? currentTelemetry : null;
        const dept = telemetry && telemetry.departments ? telemetry.departments[active] : null;
        detail.replaceChildren();
        const title = document.createElement('h3');
        title.textContent = `${room[1]} · ${room[2]}`;
        detail.append(title);
        const rows = dept ? [
            ['Vai trò gốc', dept.role || 'Chưa có dữ liệu'],
            ['Trạng thái nguồn', dept.status || 'UNVERIFIED'],
            ['Bản ghi nguồn', dept.bubble || 'Chưa có bản ghi']
        ] : [['Dữ liệu', 'Chưa có telemetry. Xem bảng kiểm chứng bên dưới.']];
        for (const [label, value] of rows) {
            const p = document.createElement('p');
            p.textContent = `${label}: ${value}`;
            detail.append(p);
        }
    }
    function renderProgress() {
        const count = visited.size;
        root.querySelector('.cult-rank').textContent = count >= 6 ? 'Trúc cơ · Trang trí' : count >= 3 ? 'Luyện khí · Trang trí' : 'Nhập môn · Trang trí';
        root.querySelector('progress').value = count;
        root.querySelector('.cult-progress-label').textContent = `${count}/6 phòng đã khám phá · ${count * 10} điểm khám phá`;
        root.querySelector('.cult-theme').disabled = count < 3;
        root.querySelector('.cult-save-note').textContent = persistent ? 'Chỉ lưu tại trình duyệt này. Không phải XP nghiệp vụ hay thành tích giao dịch.' : 'Bộ nhớ trình duyệt không khả dụng; tiến trình chỉ giữ trong phiên này.';
    }
    root.querySelectorAll('[data-room]').forEach(button => button.addEventListener('click', () => {
        button.classList.add('cult-room-pressed');
        window.setTimeout(() => button.classList.remove('cult-room-pressed'), 180);
        active = button.dataset.room;
        visited.add(active);
        try { localStorage.setItem(key, JSON.stringify([...visited])); } catch (_) { persistent = false; }
        root.querySelectorAll('[data-room]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
        renderDetail(); renderProgress();
    }));
    root.querySelector('.cult-motion').addEventListener('click', event => {
        const paused = root.classList.toggle('cult-paused');
        event.currentTarget.setAttribute('aria-pressed', String(paused));
        event.currentTarget.textContent = paused ? 'Bật chuyển động' : 'Tắt chuyển động';
    });
    root.querySelector('.cult-theme').addEventListener('click', () => {
        if (visited.size >= 3) root.classList.toggle('cult-jade');
    });
    // Refresh only from the existing in-memory telemetry; no extra API or trading access.
    const timer = setInterval(() => { if (!document.hidden && active) renderDetail(); }, 10000);
    window.addEventListener('pagehide', () => clearInterval(timer), { once: true });
    renderProgress();
})();
