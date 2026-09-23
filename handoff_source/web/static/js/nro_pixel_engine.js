/**
 * ============================================================================
 * ASTRA NRO PIXEL GAME ENGINE (DRAGON BOY CHIBI STYLE)
 * - 6 Autonomous Agents as Animated Chibi Characters
 * - Walking, Idle Bouncing, Emotes, Classic NRO Speech Bubbles
 * - Real-Time Debate Simulation & Desk-to-Desk Pathfinding
 * ============================================================================
 */

(function () {
    'use strict';

    // Character Definitions
    const NRO_AGENTS = {
        lead_pm: {
            id: 'lead_pm',
            name: '01. PM Lead',
            model: 'Gemini 3.8',
            color: '#38bdf8',
            home: { x: 50, y: 18 },
            facing: 'right',
            state: 'seated',
            hairColor: '#0284c7',
            suitColor: '#0f172a',
            accessory: '👑'
        },
        risk_council: {
            id: 'risk_council',
            name: '02. CRO Veto',
            model: 'Claude Sonnet 4.6',
            color: '#f59e0b',
            home: { x: 18, y: 15 },
            facing: 'right',
            state: 'seated',
            hairColor: '#e2e8f0',
            suitColor: '#78350f',
            accessory: '🛡️'
        },
        fast_scout: {
            id: 'fast_scout',
            name: '03. Fast Scout',
            model: 'DeepSeek Flash',
            color: '#10b981',
            home: { x: 82, y: 15 },
            facing: 'left',
            state: 'seated',
            hairColor: '#fbbf24',
            suitColor: '#064e3b',
            accessory: '⚡'
        },
        quant_lab: {
            id: 'quant_lab',
            name: '04. Quant Lab',
            model: 'Algo Engine',
            color: '#a855f7',
            home: { x: 18, y: 62 },
            facing: 'right',
            state: 'seated',
            hairColor: '#c084fc',
            suitColor: '#3b0764',
            accessory: '🔬'
        },
        execution_oms: {
            id: 'execution_oms',
            name: '05. Execution',
            model: 'Binance OMS',
            color: '#f43f5e',
            home: { x: 50, y: 62 },
            facing: 'right',
            state: 'seated',
            hairColor: '#fb7185',
            suitColor: '#881337',
            accessory: '🎯'
        },
        community_affiliate: {
            id: 'community_affiliate',
            name: '06. CRM Square',
            model: 'Binance Square',
            color: '#06b6d4',
            home: { x: 82, y: 62 },
            facing: 'left',
            state: 'seated',
            hairColor: '#22d3ee',
            suitColor: '#164e63',
            accessory: '📢'
        }
    };

    // Meeting Hub coordinate (Center of floor)
    const MEETING_HUB = { x: 50, y: 42 };

    let currentMode = 'work'; // 'work' | 'debate' | 'freeroam'
    let roamInterval = null;
    let debateTimeout = null;
    let speedMultiplier = 1.0;

    /**
     * Generate Chibi NRO Vector Avatar
     */
    function createChibiAvatarSvg(agent) {
        return `
        <svg viewBox="0 0 64 80" width="60" height="74" style="image-rendering: pixelated; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.6));">
            <!-- Head & Spiked Hair (NRO Saiyan / Chibi Style) -->
            <path d="M 12 28 C 4 12, 16 0, 32 0 C 48 0, 60 12, 52 28 Z" fill="${agent.hairColor}" stroke="#000000" stroke-width="2.5"/>
            <polygon points="10,24 0,10 18,18" fill="${agent.hairColor}" stroke="#000000" stroke-width="2"/>
            <polygon points="22,14 18,2 32,10" fill="${agent.hairColor}" stroke="#000000" stroke-width="2"/>
            <polygon points="42,14 46,2 32,10" fill="${agent.hairColor}" stroke="#000000" stroke-width="2"/>
            <polygon points="54,24 64,10 46,18" fill="${agent.hairColor}" stroke="#000000" stroke-width="2"/>

            <!-- Head Base -->
            <ellipse cx="32" cy="30" rx="18" ry="16" fill="#fed7aa" stroke="#000000" stroke-width="2.5"/>

            <!-- Big Anime / NRO Eyes -->
            <ellipse cx="25" cy="28" rx="4.5" ry="6" fill="#000000"/>
            <circle cx="24" cy="26" r="2" fill="#ffffff"/>
            <ellipse cx="39" cy="28" rx="4.5" ry="6" fill="#000000"/>
            <circle cx="38" cy="26" r="2" fill="#ffffff"/>

            <!-- Cheeks Blush -->
            <ellipse cx="20" cy="34" rx="2.5" ry="1.5" fill="#f43f5e" opacity="0.6"/>
            <ellipse cx="44" cy="34" rx="2.5" ry="1.5" fill="#f43f5e" opacity="0.6"/>

            <!-- Smile / Smug Mouth -->
            <path d="M 28 35 Q 32 38 36 35" fill="none" stroke="#000000" stroke-width="1.8" stroke-linecap="round"/>

            <!-- Chibi Body / Uniform -->
            <path d="M 20 44 L 44 44 L 48 64 L 16 64 Z" fill="${agent.suitColor}" stroke="#000000" stroke-width="2.5"/>
            <!-- Inner Tie / Gi Sash -->
            <polygon points="30,44 34,44 33,56 31,56" fill="${agent.color}"/>

            <!-- Hands -->
            <circle cx="15" cy="52" r="4" fill="#fed7aa" stroke="#000000" stroke-width="1.8"/>
            <circle cx="49" cy="52" r="4" fill="#fed7aa" stroke="#000000" stroke-width="1.8"/>

            <!-- Chibi Legs / Boots -->
            <rect x="20" y="64" width="8" height="12" rx="3" fill="#0f172a" stroke="#000000" stroke-width="2"/>
            <rect x="36" y="64" width="8" height="12" rx="3" fill="#0f172a" stroke="#000000" stroke-width="2"/>
            <ellipse cx="23" cy="75" rx="5" ry="2.5" fill="#38bdf8"/>
            <ellipse cx="39" cy="75" rx="5" ry="2.5" fill="#38bdf8"/>
        </svg>
        `;
    }

    /**
     * Build and Inject Engine DOM into #trading-floor-interactive
     */
    function initNroEngine() {
        const floorEl = document.getElementById('trading-floor-interactive');
        if (!floorEl) {
            console.warn('[NRO Engine] Floor element not found');
            return;
        }

        // 1. Insert Control Toolbar before floor
        const toolbarHtml = `
        <div class="nro-toolbar-panel">
            <div class="nro-toolbar-title">
                <span style="font-size: 18px;">🎮</span>
                <span>ASTRA NRO CHIBI GAME FLOOR</span>
                <span class="badge badge-emerald" style="font-size: 10.5px; padding: 2px 8px;">6/6 AGENTS LIVE</span>
            </div>
            <div class="nro-toolbar-actions">
                <button class="nro-btn active" id="nro-btn-work" onclick="window.AstraNRO.setMode('work')">
                    🏢 Về Bàn Làm Việc
                </button>
                <button class="nro-btn" id="nro-btn-roam" onclick="window.AstraNRO.setMode('freeroam')">
                    🚶 Đi Lại Tự Do
                </button>
                <button class="nro-btn" id="nro-btn-debate" onclick="window.AstraNRO.startDebateScenario()">
                    💬 Xem Tranh Luận Lệnh Này
                </button>
                <button class="nro-btn" id="nro-btn-speed" onclick="window.AstraNRO.toggleSpeed()">
                    ⚡ Tốc Độ: 1x
                </button>
            </div>
        </div>
        `;
        floorEl.insertAdjacentHTML('beforebegin', toolbarHtml);

        // 2. Create Overlay Container
        const overlay = document.createElement('div');
        overlay.className = 'nro-game-overlay';
        overlay.id = 'nro-game-overlay';

        // Add Meeting Zone circle
        overlay.innerHTML = `
            <div class="nro-meeting-zone" id="nro-meeting-zone">
                <div class="meeting-zone-label">BÀN HỌP HỘI ĐỒNG AI</div>
            </div>
        `;

        // 3. Render 6 Characters
        Object.values(NRO_AGENTS).forEach(agent => {
            const charEl = document.createElement('div');
            charEl.className = `nro-character nro-char-${agent.state} nro-facing-${agent.facing}`;
            charEl.id = `nro-char-${agent.id}`;
            charEl.style.left = `${agent.home.x}%`;
            charEl.style.top = `${agent.home.y}%`;
            charEl.title = `Nhấp để gọi ${agent.name} (${agent.model})`;

            charEl.innerHTML = `
                <div class="nro-nametag">${agent.name}</div>
                <div class="nro-emote-badge" id="nro-emote-${agent.id}">${agent.accessory}</div>
                <div class="nro-speech-bubble" id="nro-bubble-${agent.id}"></div>
                <div class="nro-sprite-body">
                    ${createChibiAvatarSvg(agent)}
                </div>
                <div class="nro-shadow"></div>
            `;

            charEl.style.cursor = 'pointer';
            charEl.title = `${agent.name} • Model: ${agent.model} (Click: xem hồ sơ & đàm thoại, Double-click: mở Intercom)`;
            charEl.onclick = (e) => {
                e.stopPropagation();
                window.AstraNRO.triggerCharacterTalk(agent.id);
                if (typeof openDeptDetailModal === 'function') {
                    openDeptDetailModal(agent.id);
                }
            };
            charEl.ondblclick = (e) => {
                e.stopPropagation();
                const agentMap = {
                    'lead_pm': 'Astra',
                    'risk_council': 'Rik',
                    'fast_scout': 'Hash',
                    'quant_lab': 'Prof',
                    'execution_oms': 'Meme',
                    'community_affiliate': 'Core'
                };
                const targetAgent = agentMap[agent.id] || 'Astra';
                if (typeof window.openCyberIntercomModal === 'function') {
                    window.openCyberIntercomModal(targetAgent);
                }
            };

            overlay.appendChild(charEl);
        });

        floorEl.appendChild(overlay);
        console.log('[NRO Engine] Initialized 6 Chibi Agents.');

        // 4. Auto-detect URL query for Trade Debate
        checkUrlParamsForTrade();
    }

    /**
     * Check URL Parameters to auto-play debate
     */
    function checkUrlParamsForTrade() {
        const urlParams = new URLSearchParams(window.location.search);
        const tradeId = urlParams.get('trade_id');
        const symbol = urlParams.get('symbol') || 'BTC/USDT';
        const side = urlParams.get('side') || 'BUY';

        if (tradeId && urlParams.get('autoplay') === '1') {
            setTimeout(() => {
                window.AstraNRO.startDebateScenario({
                    order_id: tradeId,
                    symbol: symbol,
                    side: side,
                    price: '81,001.51'
                });
            }, 1000);
        }
    }

    /**
     * Move a character smoothly
     */
    function walkCharacterTo(charId, targetX, targetY, durationSec, onComplete) {
        const charEl = document.getElementById(`nro-char-${charId}`);
        const agent = NRO_AGENTS[charId];
        if (!charEl || !agent) return;

        const curLeft = parseFloat(charEl.style.left) || agent.home.x;
        if (targetX < curLeft) {
            charEl.classList.remove('nro-facing-right');
            charEl.classList.add('nro-facing-left');
        } else if (targetX > curLeft) {
            charEl.classList.remove('nro-facing-left');
            charEl.classList.add('nro-facing-right');
        }

        charEl.classList.remove('nro-char-seated', 'nro-char-idle');
        charEl.classList.add('nro-char-walking');

        const dur = (durationSec || 1.2) / speedMultiplier;
        charEl.style.transition = `left ${dur}s linear, top ${dur}s linear`;
        charEl.style.left = `${targetX}%`;
        charEl.style.top = `${targetY}%`;

        setTimeout(() => {
            charEl.classList.remove('nro-char-walking');
            charEl.classList.add('nro-char-idle');
            if (onComplete) onComplete();
        }, dur * 1000);
    }

    /**
     * Display Speech Bubble & Emote
     */
    function showSpeech(charId, text, emote, durationMs) {
        const bubble = document.getElementById(`nro-bubble-${charId}`);
        const emoteBadge = document.getElementById(`nro-emote-${charId}`);
        if (!bubble || !emoteBadge) return;

        if (emote) {
            emoteBadge.textContent = emote;
            emoteBadge.classList.add('show');
        }

        bubble.textContent = text;
        bubble.classList.add('show');

        const dur = (durationMs || 3500) / speedMultiplier;
        setTimeout(() => {
            bubble.classList.remove('show');
            emoteBadge.classList.remove('show');
        }, dur);
    }

    /**
     * Debate / Meeting Scenario (NRO Style)
     */
    function runDebateScenario(tradeData) {
        setMode('debate');
        const data = tradeData || {
            symbol: 'BTC/USDT',
            side: 'BUY',
            price: '81,001.51'
        };

        const meetingZone = document.getElementById('nro-meeting-zone');
        if (meetingZone) meetingZone.classList.add('active');

        // Step 1: Scout gets alert, runs to Meeting Zone
        showSpeech('fast_scout', `Tín hiệu ${data.side} ${data.symbol}! Đang họp báo cáo!`, '⚡', 3000);
        walkCharacterTo('fast_scout', 56, 38, 1.4, () => {
            // Step 2: PM Lead arrives
            showSpeech('lead_pm', `Tiếp nhận! Triệu tập Hội Đồng Rủi Ro ngay!`, '👑', 3000);
            walkCharacterTo('lead_pm', 48, 36, 1.2, () => {
                // Step 3: CRO Veto and Quant Lab walk in
                walkCharacterTo('risk_council', 42, 42, 1.5, () => {
                    showSpeech('risk_council', `Cấu trúc 1H/4H đồng thuận! Phê duyệt 50% size!`, '🛡️', 3500);
                });

                walkCharacterTo('quant_lab', 44, 46, 1.6, () => {
                    showSpeech('quant_lab', `Đã chốt SL 1.5x ATR, R:R 1:2.4!`, '🔬', 3200);
                });

                // Step 4: Execution OMS rushes in
                setTimeout(() => {
                    walkCharacterTo('execution_oms', 54, 44, 1.3, () => {
                        showSpeech('execution_oms', `BÙM! Đã khớp lệnh LIVE và gài STOP_MARKET Binance!`, '🎯', 3800);

                        // Step 5: Wrap up & return to desks
                        setTimeout(() => {
                            showSpeech('lead_pm', `Cuộc họp kết thúc. Tất cả về vị trí trực chiến!`, '✅', 2500);
                            if (meetingZone) meetingZone.classList.remove('active');

                            setTimeout(() => {
                                setMode('work');
                            }, 2600 / speedMultiplier);
                        }, 4000 / speedMultiplier);
                    });
                }, 2000 / speedMultiplier);
            });
        });
    }

    /**
     * Reset all agents to home desks
     */
    function resetToWorkMode() {
        if (roamInterval) clearInterval(roamInterval);
        const meetingZone = document.getElementById('nro-meeting-zone');
        if (meetingZone) meetingZone.classList.remove('active');

        Object.values(NRO_AGENTS).forEach(agent => {
            const charEl = document.getElementById(`nro-char-${agent.id}`);
            if (!charEl) return;

            walkCharacterTo(agent.id, agent.home.x, agent.home.y, 1.2, () => {
                charEl.classList.remove('nro-char-walking', 'nro-char-idle');
                charEl.classList.add('nro-char-seated');
            });
        });
    }

    /**
     * Free Roam Mode
     */
    function startFreeRoam() {
        if (roamInterval) clearInterval(roamInterval);
        const waypoints = [
            { x: 10, y: 35 }, // Water cooler / Pantry
            { x: 12, y: 45 }, // Printer
            { x: 88, y: 35 }, // Window view
            { x: 50, y: 35 }, // Center aisle
            { x: 30, y: 50 },
            { x: 70, y: 50 }
        ];

        roamInterval = setInterval(() => {
            const agentKeys = Object.keys(NRO_AGENTS);
            const randomAgent = agentKeys[Math.floor(Math.random() * agentKeys.length)];
            const targetPoint = waypoints[Math.floor(Math.random() * waypoints.length)];

            walkCharacterTo(randomAgent, targetPoint.x, targetPoint.y, 1.8, () => {
                showSpeech(randomAgent, 'Đi tuần tra sàn giao dịch...', '🔍', 2000);
                setTimeout(() => {
                    const agent = NRO_AGENTS[randomAgent];
                    walkCharacterTo(randomAgent, agent.home.x, agent.home.y, 1.8);
                }, 3000 / speedMultiplier);
            });
        }, 6000 / speedMultiplier);
    }

    /**
     * Mode Switcher
     */
    function setMode(mode) {
        currentMode = mode;
        document.querySelectorAll('.nro-btn').forEach(b => b.classList.remove('active'));

        const btn = document.getElementById(`nro-btn-${mode}`);
        if (btn) btn.classList.add('active');

        if (mode === 'work') {
            resetToWorkMode();
        } else if (mode === 'freeroam') {
            startFreeRoam();
        }
    }

    function toggleSpeed() {
        speedMultiplier = speedMultiplier === 1.0 ? 2.0 : 1.0;
        const btn = document.getElementById('nro-btn-speed');
        if (btn) {
            btn.textContent = `⚡ Tốc Độ: ${speedMultiplier}x`;
            btn.classList.toggle('active', speedMultiplier === 2.0);
        }
    }

    function triggerCharacterTalk(charId) {
        const phrases = {
            lead_pm: ['Đang điều phối 10 Agents!', 'Kỷ luật tạo ra tự do tài chính.', 'Circuit Breaker luôn sẵn sàng.'],
            risk_council: ['Stop-Loss 1.5x ATR là bất khả xâm phạm.', 'Không đu đỉnh khi RSI > 75.', 'Bảo toàn vốn là số 1!'],
            fast_scout: ['Quét WebSocket Futures liên tục.', 'Phát hiện nến đảo chiều 15m.', 'Không có bẫy thanh khoản!'],
            quant_lab: ['Tính toán ma trận tương quan đa cấp.', 'R:R đạt 1:2.5.', 'Bollinger Bands co thắt sắp nổ volume!'],
            execution_oms: ['Lệnh native STOP_MARKET đã găm sẵn.', 'ReduceOnly=True tuyệt đối.', 'Không trượt giá quá 0.05%.'],
            community_affiliate: ['Khách hàng SaaS đang tăng trưởng.', 'Đồng bộ hoa hồng Binance/OKX.', 'Cập nhật tín hiệu lên Square.']
        };

        const list = phrases[charId] || ['Trực chiến 24/7!'];
        const text = list[Math.floor(Math.random() * list.length)];
        showSpeech(charId, text, '💬', 3000);
    }

    // Public API
    window.AstraNRO = {
        init: initNroEngine,
        setMode: setMode,
        toggleSpeed: toggleSpeed,
        startDebateScenario: runDebateScenario,
        triggerCharacterTalk: triggerCharacterTalk
    };

    // Auto-init when DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNroEngine);
    } else {
        initNroEngine();
    }
})();
