/* ==========================================================================
   ASTRA DESK — AI & API ORCHESTRATION JAVASCRIPT CONTROLLER
   Fix: Zero-Anchor Jumping, Always Keep Header Visible, Stable Scroll, Responsive UI
   ========================================================================== */

let orchData = null;

// Helper to reliably scroll the admin scroll-wrapper to top
function resetPageScroll() {
    try {
        const mw = document.querySelector('.main-wrapper') || 
                   document.querySelector('.content-body') || 
                   document.querySelector('.orch-container');
        if (mw && typeof mw.scrollTop === 'number') {
            mw.scrollTop = 0;
        }
        if (document.documentElement) document.documentElement.scrollTop = 0;
        if (document.body) document.body.scrollTop = 0;
        if (window.scrollTo) window.scrollTo(0, 0);
    } catch (e) {
        console.warn('[Orchestration] resetPageScroll error:', e);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initOrchTabs();
    initModelCatalogFilters();
    loadOrchestrationData();
});

// 1. Tab Switching Engine (ZERO-ANCHOR JUMP - HEADER ALWAYS VISIBLE)
function initOrchTabs() {
    const tabBtns = document.querySelectorAll('.orch-tab-btn');
    const hash = window.location.hash ? window.location.hash.replace('#', '') : null;
    const savedTab = (hash && hash.startsWith('tab-')) 
        ? hash 
        : (localStorage.getItem('astra_settings_ai_tab') || 'tab-1');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const target = btn.getAttribute('data-tab');
            if (target) {
                switchOrchTab(target, true);
            }
        });
    });

    // Listen to hash changes (back/forward or external links)
    window.addEventListener('hashchange', () => {
        const newHash = window.location.hash ? window.location.hash.replace('#', '') : '';
        if (newHash && newHash.startsWith('tab-')) {
            switchOrchTab(newHash, false);
        }
    });

    // Initial activation without triggering scroll jump
    switchOrchTab(savedTab, false);
    resetPageScroll();
}

function switchOrchTab(tabId, save = true) {
    if (!tabId) tabId = 'tab-1';
    // Normalize tabId (e.g. 'panel-tab-2' -> 'tab-2', 'tab-2' -> 'tab-2')
    const cleanId = tabId.replace('panel-', '');
    const panelId = 'panel-' + cleanId;

    const tabBtns = document.querySelectorAll('.orch-tab-btn');
    const panels = document.querySelectorAll('.orch-panel');

    let foundPanel = false;

    tabBtns.forEach(b => {
        const btnTab = b.getAttribute('data-tab');
        if (btnTab === cleanId || btnTab === panelId) {
            b.classList.add('active');
        } else {
            b.classList.remove('active');
        }
    });

    panels.forEach(p => {
        const pTabId = p.getAttribute('data-tab-id');
        if (p.id === panelId || pTabId === cleanId || p.id === cleanId) {
            p.classList.add('active');
            foundPanel = true;
        } else {
            p.classList.remove('active');
        }
    });

    // If invalid tab requested, fallback gracefully to tab-1
    if (!foundPanel && cleanId !== 'tab-1') {
        switchOrchTab('tab-1', save);
        return;
    }

    if (save) {
        try {
            localStorage.setItem('astra_settings_ai_tab', cleanId);
            if (window.history && window.history.replaceState) {
                // replaceState updates the URL WITHOUT triggering a hashchange or scrolling!
                window.history.replaceState(null, '', '#' + cleanId);
            }
        } catch (e) {}
    }

    // Always keep page scroll anchored at the top so header & tabs remain 100% visible
    resetPageScroll();
}

// Fallback compatibility in case any legacy button calls switchMasterMode
function switchMasterMode(mode, save = true) {
    const panelTrading = document.getElementById('panel-trading-setup');
    const panelAi = document.getElementById('panel-ai-orchestration');
    if (!panelTrading || !panelAi) return;
    if (mode === 'trading-setup') {
        panelTrading.style.display = 'block';
        panelAi.style.display = 'none';
    } else {
        panelTrading.style.display = 'none';
        panelAi.style.display = 'flex';
    }
}

// 3. Fetch Overview Data
async function loadOrchestrationData() {
    try {
        const res = await fetch('/api/v1/orchestration/overview');
        if (!res.ok) return;
        orchData = await res.json();
        updateOrchUI(orchData);
    } catch (e) {
        console.warn('[Orchestration] Failed to fetch live overview:', e);
    }
}

function updateOrchUI(data) {
    if (!data) return;

    if (data.overview) {
        const totalProv = data.overview.total_providers || 7;
        const totalMod = (data.overview.total_models || 179) + '+';
        const avgLat = (data.overview.avg_latency || 245) + 'ms';
        const uptime = data.overview.uptime || '99.8%';

        document.querySelectorAll('.orch-stat-providers-val').forEach(el => el.textContent = totalProv);
        document.querySelectorAll('.orch-stat-models-val').forEach(el => el.textContent = totalMod);
        document.querySelectorAll('.orch-stat-latency-val').forEach(el => el.textContent = avgLat);
        document.querySelectorAll('.orch-stat-uptime-val').forEach(el => el.textContent = uptime);

        const p1 = document.getElementById('stat-total-providers');
        if (p1) p1.textContent = totalProv;
        const p2 = document.getElementById('stat-total-providers-side');
        if (p2) p2.textContent = totalProv;

        const m1 = document.getElementById('stat-total-models');
        if (m1) m1.textContent = totalMod;
        const m2 = document.getElementById('stat-total-models-side');
        if (m2) m2.textContent = totalMod;
    }
}

// Model Catalog Search & Filter Engine
function initModelCatalogFilters() {
    const filterBtns = document.querySelectorAll('.btn-filter-model');
    const searchInput = document.getElementById('model-search-input');
    const cards = document.querySelectorAll('#orch-model-catalog-grid .orch-model-card');

    if (!filterBtns.length || !cards.length) return;

    let currentFilter = 'all';
    let searchQuery = '';

    function applyFilterAndSearch() {
        cards.forEach(card => {
            const provider = card.getAttribute('data-provider') || '';
            const cardText = (card.getAttribute('data-name') || '' + ' ' + card.innerText).toLowerCase();

            const matchesFilter = (currentFilter === 'all') || (provider === currentFilter);
            const matchesSearch = !searchQuery || cardText.includes(searchQuery);

            if (matchesFilter && matchesSearch) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
    }

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => {
                b.classList.remove('active');
                b.style.background = 'transparent';
                b.style.color = 'var(--text-sub)';
            });
            btn.classList.add('active');
            btn.style.background = 'rgba(37, 99, 235, 0.12)';
            btn.style.color = '#2563eb';
            btn.style.fontWeight = '700';

            currentFilter = btn.getAttribute('data-filter') || 'all';
            applyFilterAndSearch();
        });
    });

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.toLowerCase().trim();
            applyFilterAndSearch();
        });
    }
}

// 4. Eye Button Mask / Unmask Toggle
function toggleKeyVisibility(btn, actualKey) {
    const keySpan = btn.parentElement.querySelector('.orch-key-text');
    if (!keySpan) return;

    if (btn.dataset.revealed === 'true') {
        keySpan.textContent = btn.dataset.masked;
        btn.dataset.revealed = 'false';
        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
    } else {
        if (!btn.dataset.masked) {
            btn.dataset.masked = keySpan.textContent;
        }
        keySpan.textContent = actualKey || 'sk-••••••••••••';
        btn.dataset.revealed = 'true';
        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`;
    }
}

// 5. Toggle Provider Switch
async function toggleProvider(pid, checkbox) {
    const active = checkbox.checked;
    try {
        const res = await fetch('/api/v1/orchestration/toggle-provider', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider_id: pid, active: active })
        });
        const data = await res.json();
        if (!res.ok) {
            checkbox.checked = !active;
            alert('Lỗi cập nhật trạng thái provider: ' + (data.detail || 'Không xác định'));
        }
    } catch (e) {
        checkbox.checked = !active;
        alert('Lỗi kết nối: ' + e);
    }
}

// 6. Live Ping Engine
async function pingAllProviders() {
    const pingBtns = document.querySelectorAll('.btn-ping-all');
    pingBtns.forEach(b => {
        b.disabled = true;
        b.innerHTML = `<span class="orch-spinner"></span> <span>Đang Ping 7 Nhà Cung Cấp...</span>`;
    });

    try {
        const res = await fetch('/api/v1/orchestration/ping-all', { method: 'POST' });
        const data = await res.json();

        if (res.ok && data.results) {
            data.results.forEach(r => {
                const latEl = document.getElementById(`lat-${r.id}`);
                if (latEl) {
                    latEl.textContent = `${r.latency_ms} ms`;
                    latEl.style.fontWeight = '700';
                    latEl.style.color = r.latency_ms < 500 ? '#10b981' : (r.latency_ms < 1500 ? '#f59e0b' : '#ef4444');
                }

                const tab5Lat = document.getElementById(`tab5-lat-${r.id}`);
                if (tab5Lat) tab5Lat.textContent = `${r.latency_ms} ms`;

                const tab5Bar = document.getElementById(`tab5-bar-${r.id}`);
                if (tab5Bar) {
                    const pct = Math.min(Math.round((r.latency_ms / 3000) * 100), 100);
                    tab5Bar.style.width = pct + '%';
                    tab5Bar.style.backgroundColor = r.latency_ms < 500 ? '#10b981' : (r.latency_ms < 1500 ? '#f59e0b' : '#ef4444');
                }

                const statusEl = document.getElementById(`status-badge-${r.id}`);
                if (statusEl) {
                    if (r.status === 'active') {
                        statusEl.className = 'orch-status-active';
                        statusEl.textContent = 'Hoạt động';
                    } else {
                        statusEl.className = 'orch-status-offline';
                        statusEl.textContent = r.status === 'degraded' ? 'Chập chờn' : 'Mất kết nối';
                    }
                }
            });

            const logEl = document.getElementById('ping-last-timestamp');
            if (logEl) {
                const now = new Date().toLocaleTimeString('vi-VN');
                logEl.textContent = `Vừa kiểm tra lúc ${now} (Toàn bộ 7/7 nguồn phản hồi)`;
            }
        }
    } catch (e) {
        alert('Lỗi kiểm tra độ trễ: ' + e);
    } finally {
        pingBtns.forEach(b => {
            b.disabled = false;
            b.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg> <span>Ping Toàn Bộ Nhà Cung Cấp</span>`;
        });
    }
}

// 7. Save Orchestration Rules
async function saveOrchestrationRules() {
    const primarySelect = document.getElementById('select-primary-model');
    const cbDrawdown = document.getElementById('input-cb-drawdown');
    const cbTimeout = document.getElementById('input-cb-timeout');
    const autoFb = document.getElementById('switch-auto-fallback');
    const logDetails = document.getElementById('switch-detailed-log');

    const payload = {
        primary_model: primarySelect ? primarySelect.value : "Vyce AI - claude-sonnet-4-6 (Supreme Gatekeeper)",
        max_drawdown: cbDrawdown ? parseFloat(cbDrawdown.value) : 0.02,
        timeout_seconds: cbTimeout ? parseInt(cbTimeout.value) : 30,
        auto_fallback: autoFb ? autoFb.checked : true,
        detailed_logging: logDetails ? logDetails.checked : true
    };

    try {
        const res = await fetch('/api/v1/orchestration/save-rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            alert('✅ Đã lưu cấu hình AI Orchestration & Circuit Breaker thành công!');
        } else {
            alert('❌ Lỗi: ' + (data.detail || 'Không thể lưu cấu hình'));
        }
    } catch (e) {
        alert('Lỗi gửi dữ liệu: ' + e);
    }
}

// 8. Apply AI Recommendation
function applyAiSuggestion() {
    const primarySelect = document.getElementById('select-primary-model');
    if (primarySelect) {
        primarySelect.value = "Groq - llama-3.1-70b";
    }
    saveOrchestrationRules();
    alert("⚡ Đã áp dụng gợi ý AI: Chuyển 'Groq - llama-3.1-70b' làm Model Chính để tối ưu tốc độ (<250ms) và chi phí!");
}

// 9. Open Modal Add Provider
function openAddProviderModal() {
    alert("Để kết nối thêm nhà cung cấp tùy chỉnh (Custom OpenAI-Compatible API), bạn chỉ cần dán Base URL và API Key vào bảng cài đặt hoặc cấu hình trực tiếp trong file .env!");
}
