/**
 * AGENT RPG REGISTRY & MODAL CONTROLLER (12 AGENTS)
 * Version: 2.0 - Dual-Fleet Architecture (Tactical HFT vs Macro 9Router)
 */

window.currentRpgAgent = 'Astra';

window.AGENT_RPG_REGISTRY = {
    'Astra': {
        name: 'Astra',
        titleVi: 'Tổng Quản Tối Cao & Điều Phối Đa Não',
        deptKey: 'lead_pm',
        wingTag: '⚡ ĐỘI 1 · TRỰC CHIẾN TỐC ĐỘ CAO (< 1.5s)',
        fleetType: 'FLEET_1_TACTICAL',
        fleetBadge: '⚡ BAN TÁC CHIẾN KHỚP LỆNH',
        rpgClass: 'Grand Quantitative Conductor · Tier SS+',
        level: 50,
        expStr: '50,000 / 50,000 EXP (MAX)',
        expPct: 100,
        avatar: '/static/images/sprites/sprite_01_pm.png',
        color: '#38bdf8',
        hpVal: '100% (Drawdown 0.0%)',
        hpPct: 100,
        hpHint: 'Vốn $55.37 USDT an toàn tuyệt đối · Khóa két 450U Vault ngoài sàn Futures',
        mpVal: '99% (Gemini 3.8 / GPT-5.6)',
        mpPct: 99,
        mpHint: 'Context: 1,000,000 Tokens · Latency: ~18ms · Điều phối 7 Provider thông suốt',
        stats: { speed: 92, accuracy: 94, discipline: 98, alpha: 91, defense: 97, vision: 99 },
        skills: [
            {
                name: 'Hợp Âm Đa Não 7 Provider',
                icon: '🎼',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Thường trực',
                desc: 'Chỉ huy dàn hợp xướng 12 Tác Tử kết hợp sức mạnh từ Vyce AI, Groq, 9Router, OpenRouter, Google AI và Binance OMS.'
            },
            {
                name: 'Quyền Trượng Phân Bổ Vốn',
                icon: '⚖️',
                type: 'CHỦ ĐỘNG',
                cooldown: '15 Phút',
                desc: 'Kiểm soát tỷ lệ phân bổ: Thử nghiệm thực chiến 50U và khóa chặt 450U trong két an toàn. Cân bằng Margin Ratio < 2%.'
            },
            {
                name: 'Phán Quyết Sinh Tử 500U',
                icon: '🏛️',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: '7 Ngày Thử Thách',
                desc: 'Giám sát 3 Cổng Rủi Ro (Gate 100U -> 250U -> 500U). Chỉ duyệt tăng vốn khi PnL thực chứng minh bù đủ phí và trượt giá.'
            }
        ],
        quote: 'Kỷ luật định lượng là vũ khí tối thượng. Thà bỏ lỡ cơ hội còn hơn vi phạm nguyên tắc bảo toàn vốn!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'Python Core Engine', desc: 'Khởi tạo khung bot Python, kết nối Binance Futures API, quản lý vị thế đơn luồng.' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'Multi-Agent Conductor', desc: 'Mở rộng điều phối 10 tác tử qua Vyce AI & Groq, thiết lập cơ chế CRO Veto Gatekeeper.' },
            { ver: 'GĐ 3 (22/09/2026)', model: '3D Campus & 9Router', desc: 'Vận hành sàn 3D Cyber Floor, tích hợp 31 tài khoản Codex & Grok-4.7.' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Dual-Fleet Commander', desc: 'Chỉ huy 2 Đội: Tầng Trade Trực Chiến (<1.5s) và Tình Báo Vĩ Mô 9Router, dọn sạch model lỗi.' }
        ],
        primaryModel: 'Gemini-3.8-Flash / DeepSeek-V4.1',
        fallbackModel: 'Groq Llama-3.3-70B',
        strategyRole: 'Executive Lead PM & Capital Governor'
    },
    'Rik': {
        name: 'Rik',
        titleVi: 'Cảnh Sát Rủi Ro & Thẩm Phán Tối Cao (CRO)',
        deptKey: 'risk_council',
        wingTag: '⚡ ĐỘI 1 · TRỰC CHIẾN TỐC ĐỘ CAO (< 1.5s)',
        fleetType: 'FLEET_1_TACTICAL',
        fleetBadge: '⚡ BAN TÁC CHIẾN KHỚP LỆNH',
        rpgClass: 'Supreme Risk Inquisitor · Tier SS+',
        level: 50,
        expStr: '49,800 / 50,000 EXP',
        expPct: 99,
        avatar: '/static/images/sprites/sprite_02_risk.png',
        color: '#ef4444',
        hpVal: '100% (Drawdown 0.0%)',
        hpPct: 100,
        hpHint: 'Drawdown 0.0% · Ngắt mạch Hard Risk Gate thường trực sẵn sàng',
        mpVal: '98% (Claude-Sonnet-4-6)',
        mpPct: 98,
        mpHint: 'Vyce AI Claude-Sonnet-4-6 · Độ trễ 1.1s · Phản biện không khoan nhượng',
        stats: { speed: 95, accuracy: 93, discipline: 100, alpha: 88, defense: 100, vision: 94 },
        skills: [
            {
                name: 'Phủ Quyết Tuyệt Đối Dual-AI Veto',
                icon: '🛑',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Tức thì (0s)',
                desc: 'Phủ quyết dập tắt tức thì bất kỳ tín hiệu nào có tỷ lệ R:R < 1:1.5 hoặc vào ngay sát cản kháng cự/hỗ trợ nguy hiểm.'
            },
            {
                name: 'Khiên Ngắt Mạch Circuit Breaker 2%',
                icon: '🛡️',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Thường trực',
                desc: 'Tự động khóa toàn bộ quyền mở lệnh mới và đóng băng vị thế nếu drawdown tài khoản trong ngày chạm ngưỡng 2.0%.'
            },
            {
                name: 'Truy Vấn Tương Quan Beta Inquisition',
                icon: '🔍',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Theo nhịp nến',
                desc: 'Ngăn chặn mở đồng thời nhiều vị thế có hệ số tương quan Beta > 0.85 với Bitcoin để triệt tiêu rủi ro danh mục.'
            }
        ],
        quote: 'Bảo toàn vốn là số 1! Không có R:R đẹp thì thà cầm tiền đứng ngoài nhìn, tuyệt đối không đánh bạc!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'Hard Stop-Loss 2%', desc: 'Ngắt mạch Circuit Breaker khẩn cấp khi drawdown ngày chạm ngưỡng 2.0% trên Binance.' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'Claude Sonnet CRO Veto', desc: 'Phủ quyết dập tắt tín hiệu không đạt tỷ lệ R:R 1:1.5 hoặc vào ngay sát cản kháng cự/hỗ trợ.' },
            { ver: 'GĐ 3 (22/09/2026)', model: '450U Vault Shield', desc: 'Thiết lập ranh giới thử thách 50U và khóa chặt 450U vốn dự trữ an toàn ngoài sàn Futures.' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Dual-Gatekeeper (Vyce AI)', desc: 'Giám sát chéo cả Đội Tác Chiến lẫn Chỉ Thị Vĩ Mô từ Đội Tình Báo 9Router, bảo toàn vốn tuyệt đối.' }
        ],
        primaryModel: 'Claude-Sonnet-4-6 (Vyce AI)',
        fallbackModel: 'DeepSeek-V4.1 (Vyce AI)',
        strategyRole: 'Chief Risk Officer & AI Veto Gatekeeper'
    },
    'Palermo': {
        name: 'Palermo',
        titleVi: 'Trưởng Ban Xu Hướng & Định Lượng (Quant Lab)',
        deptKey: 'quant_lab',
        wingTag: '⚡ ĐỘI 1 · TRỰC CHIẾN TỐC ĐỘ CAO (< 1.5s)',
        fleetType: 'FLEET_1_TACTICAL',
        fleetBadge: '⚡ BAN TÁC CHIẾN KHỚP LỆNH',
        rpgClass: 'Quantitative Trend Sage · Tier S+',
        level: 48,
        expStr: '44,500 / 48,000 EXP',
        expPct: 93,
        avatar: '/static/images/sprites/sprite_04_quant.png',
        color: '#a855f7',
        hpVal: '100% (An Toàn)',
        hpPct: 100,
        hpHint: 'Kỷ luật bám xu hướng · Không bắt đỉnh đáy vô căn cứ',
        mpVal: '95% (DeepSeek-V4.1)',
        mpPct: 95,
        mpHint: 'DeepSeek-V4.1 Vyce AI · Khử nhiễu vi cấu trúc đa khung thời gian',
        stats: { speed: 86, accuracy: 91, discipline: 94, alpha: 95, defense: 89, vision: 93 },
        skills: [
            {
                name: 'Sóng Kép EMA 20/50 Đa Khung',
                icon: '📈',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Theo nến 15m',
                desc: 'Định vị hợp lưu xu hướng trên khung M15/H1/H4. Chỉ kích hoạt lệnh khi cả 3 khung thời gian đồng thuận một hướng.'
            },
            {
                name: 'Bộ Lọc Kalman Khử Nhiễu Thanh Khoản',
                icon: '🔬',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Liên tục',
                desc: 'Tách tín hiệu sóng thật khỏi các râu nến quét thanh khoản (liquidity hunt wicks) của sàn giao dịch.'
            },
            {
                name: 'Bẫy Nén Bollinger Compression',
                icon: '⚡',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Khi dải nén < 1.2%',
                desc: 'Bắt trọn điểm bung nén dải Bollinger Bandwidth để đón đầu các đợt mở rộng biến động mạnh nhất.'
            }
        ],
        quote: 'Xu hướng là bạn, kỷ luật là thầy. Đi cùng dòng chảy của dòng tiền thông minh là cách duy nhất có lãi bền vững.',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'EMA 20/50 & RSI-14', desc: 'Thuật toán bắt xu hướng động lượng đa khung thời gian M15/H1/H4 trên Binance Futures.' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'Kalman Filter Vi Cấu Trúc', desc: 'Lọc nhiễu quét râu thanh khoản của sàn giao dịch, phân biệt bẫy giá và xu hướng thực.' },
            { ver: 'GĐ 3 (22/09/2026)', model: 'DeepSeek-V4.1 (Vyce AI)', desc: 'Mô hình DeepSeek qua Vyce AI phân tích cấu trúc nén đa chiều siêu chính xác.' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Đội Trưởng Săn Kèo Tầng Trade', desc: 'Cung cấp tín hiệu bám trend tốc độ cao cho Đội Tác Chiến Khớp Lệnh (< 1.5s).' }
        ],
        primaryModel: 'DeepSeek-V4.1 (Vyce AI)',
        fallbackModel: 'Groq Llama-3.3-70B',
        strategyRole: 'Trend Following & Alpha Factor Architect'
    },
    'Tory': {
        name: 'Tory',
        titleVi: 'Đội Trưởng Săn Sóng Đột Phá (Breakout Hunter)',
        deptKey: 'breakout_hunter',
        wingTag: '⚡ ĐỘI 1 · TRỰC CHIẾN TỐC ĐỘ CAO (< 1.5s)',
        fleetType: 'FLEET_1_TACTICAL',
        fleetBadge: '⚡ BAN TÁC CHIẾN KHỚP LỆNH',
        rpgClass: 'Breakout Momentum Vanguard · Tier S+',
        level: 46,
        expStr: '39,200 / 44,000 EXP',
        expPct: 89,
        avatar: '/static/images/sprites/sprite_05_execution.png',
        color: '#f59e0b',
        hpVal: '100% (An Toàn)',
        hpPct: 100,
        hpHint: 'Tỷ lệ thắng 30 ngày: 74.2% · Khóa lãi bằng Trailing Stop',
        mpVal: '99% (DeepSeek-V4.1 / Agnes-3.0)',
        mpPct: 99,
        mpHint: 'DeepSeek-V4.1 (1,022ms) & Agnes-3.0-Flash (512k context) · Quét toàn bộ lịch sử volume đa sàn',
        stats: { speed: 90, accuracy: 86, discipline: 92, alpha: 96, defense: 87, vision: 90 },
        skills: [
            {
                name: 'Khai Phá Kênh Donchian 20 Nến',
                icon: '🎯',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Theo nến 15m',
                desc: 'Bắt điểm phá vỡ đỉnh/đáy 20 chu kỳ nến kết hợp volume đột biến gấp 1.8 lần đường trung bình 20 ngày.'
            },
            {
                name: 'Xung Kích Khối Lượng 1M Context',
                icon: '💥',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Khi có Volume Spike',
                desc: 'Phân tích 1,000,000 tokens dữ liệu lệnh quá khứ để xác thực xem đây là đột phá thật hay cú lừa của cá mập.'
            },
            {
                name: 'Khóa Lợi Nhuận ATR Dynamic Trail',
                icon: '🏹',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Tự động',
                desc: 'Kéo Stop-Loss bám sát sau lưng giá theo hệ số 1.5x ATR, đảm bảo đã có lãi là không bao giờ biến thành lỗ.'
            }
        ],
        quote: 'Năng lượng tích lũy càng lâu, cú nổ càng dữ dội. Bắt đúng sóng đột phá là chìa khóa nhân đôi tài khoản!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'Donchian Channel 20 Nến', desc: 'Bắt nhịp phá vỡ đỉnh/đáy 20 chu kỳ nén Donchian kết hợp trailing stop bảo toàn lãi.' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'Volume Surge Validator', desc: 'Kiểm tra khối lượng giao dịch đột biến gấp 1.8x đường trung bình trước khi kích hoạt.' },
            { ver: 'GĐ 3 (22/09/2026)', model: 'Qwen-3.8-Flash Quét Volume', desc: 'Đưa mô hình vào kiểm định thể tích (đã chạm ngưỡng quota giới hạn 200/200 của Vyce).' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'DeepSeek-V4.1 / Agnes-3.0', desc: 'Chuyển sang DeepSeek-V4.1 (1,022ms) & Agnes-3.0-Flash (512k context), dứt điểm lỗi quota.' }
        ],
        primaryModel: 'DeepSeek-V4.1 (Vyce AI)',
        fallbackModel: 'Agnes-3.0-Flash (Vyce AI)',
        strategyRole: 'Donchian Momentum & Volume Surge Hunter'
    },
    'Volt': {
        name: 'Volt',
        titleVi: 'Chuyên Gia Đo Lường Biến Động & Chế Độ Thị Trường',
        deptKey: 'volatility_lab',
        wingTag: '06 · BIẾN ĐỘNG & REGIME',
        rpgClass: 'Volatility & Regime Modeler · Tier S',
        level: 45,
        expStr: '37,800 / 42,000 EXP',
        expPct: 90,
        avatar: '/static/images/sprites/sprite_04_quant.png',
        color: '#eab308',
        hpVal: '100% (An Toàn)',
        hpPct: 100,
        hpHint: 'Bảo vệ tài khoản trước các đợt quét râu bão táp',
        mpVal: '96% (Groq Llama-3.3-70B)',
        mpPct: 96,
        mpHint: 'Groq Llama-3.3-70B siêu tốc · Tính toán GARCH trong 15ms',
        stats: { speed: 93, accuracy: 89, discipline: 95, alpha: 87, defense: 94, vision: 92 },
        skills: [
            {
                name: 'Phân Phối Chuẩn Gaussian & GARCH',
                icon: '🌊',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Liên tục',
                desc: 'Đo lường độ lệch chuẩn dao động giá σ, dự phóng khoảng biến động tối đa trong 4 giờ tiếp theo.'
            },
            {
                name: 'Cảm Biến Chế Độ Thị Trường ADX Regime',
                icon: '📡',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Thường trực',
                desc: 'Phân định dứt khoát trạng thái Trending (ADX > 25) hay Ranging (ADX < 20) để kích hoạt chiến lược phù hợp.'
            },
            {
                name: 'Bóp Nghẹt Đòn Bẩy Khi Có Bão',
                icon: '⚡',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Khi ATR tăng vọt > 2.5x',
                desc: 'Tự động hạ kích thước lệnh và nới rộng khoảng đệm SL khi nhận diện siêu bão tin tức sắp càn quét.'
            }
        ],
        quote: 'Biến động không phải là kẻ thù, biến động là nguồn sống của trader định lượng nếu biết quản trị độ lệch chuẩn!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'ATR 14 Chu Kỳ', desc: 'Đo lường biên độ dao động giá cơ bản của Bitcoin và Altcoins để ước lượng stop-loss.' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'Bộ Lọc Chế Độ ADX Regime', desc: 'Phân loại trạng thái Trending (ADX > 25) vs Sideway Ranging (ADX < 20) để kích hoạt chiến lược.' },
            { ver: 'GĐ 3 (22/09/2026)', model: 'Groq Llama-3.3-70B Cực Nhanh', desc: 'Mô phỏng GARCH volatility thời gian thực dưới 15ms qua Groq Cloud HFT.' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Cảm Biến Bão Biến Động Đội 1', desc: 'Tự động bóp nghẹt đòn bẩy và nới khoảng đệm SL tức thì khi nhận diện siêu bão tin tức.' }
        ],
        primaryModel: 'Groq Llama-3.3-70B',
        fallbackModel: 'Claude-Sonnet-4-6 (Vyce AI)',
        strategyRole: 'Macro Regime & Volatility Dynamic Sizer'
    },
    'Meme': {
        name: 'Meme',
        titleVi: 'Đội Trưởng Khớp Lệnh & Trailing Guardian (OMS)',
        deptKey: 'execution_oms',
        wingTag: '⚡ ĐỘI 1 · TRỰC CHIẾN TỐC ĐỘ CAO (< 1.5s)',
        fleetType: 'FLEET_1_TACTICAL',
        fleetBadge: '⚡ BAN TÁC CHIẾN KHỚP LỆNH',
        rpgClass: 'High-Frequency Order Router · Tier SS',
        level: 49,
        expStr: '48,100 / 50,000 EXP',
        expPct: 96,
        avatar: '/static/images/sprites/sprite_05_execution.png',
        color: '#ec4899',
        hpVal: '100% (An Toàn)',
        hpPct: 100,
        hpHint: 'Khớp lệnh thực chiến: 0 lệnh lỗi · Đã dọn sạch algo orders mồ côi',
        mpVal: '98% (Groq Llama-3.3-70B)',
        mpPct: 98,
        mpHint: 'Độ trễ khớp lệnh < 22ms · Kết nối trực tiếp Binance Futures VIP API',
        stats: { speed: 99, accuracy: 96, discipline: 98, alpha: 92, defense: 96, vision: 88 },
        skills: [
            {
                name: 'Khớp Lệnh Siêu Tốc Sub-22ms',
                icon: '⚡',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Ngay lập tức',
                desc: 'Định tuyến lệnh Binance Futures tốc độ ánh sáng, tối ưu hóa TWAP và Limit để lấy vị thế đẹp nhất.'
            },
            {
                name: 'Giáp Bù Trượt Giá Smart Slippage Guard',
                icon: '🛡️',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Thường trực',
                desc: 'Kiểm tra độ sâu Orderbook 20 bậc trước khi bắn lệnh. Từ chối thực thi nếu trượt giá vượt quá 0.05%.'
            },
            {
                name: 'Vệ Binh Trailing Guardian Dời SL Tự Động',
                icon: '⚔️',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Bám từng tick giá',
                desc: 'Như chiến công SOL vừa qua: Khi lệnh có lãi, tự động dời SL bám đỉnh nến ATR, biến lệnh thắng thành pháo đài bất khả xâm phạm.'
            }
        ],
        quote: 'Ý tưởng triệu đô mà khớp lệnh trượt giá thì cũng thành rác. Tốc độ và kỷ luật khớp lệnh là ranh giới giữa thắng và thua!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'CCXT Binance Order Router', desc: 'Khớp lệnh thị trường và quản lý vị thế thực tế trên Binance Futures qua API.' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'Dọn Dẹp Lệnh Mồ Côi', desc: 'Tự động quét và hủy các lệnh algo stop-loss mồ côi tồn đọng trên sàn sau khi đóng lệnh.' },
            { ver: 'GĐ 3 (22/09/2026)', model: 'Trailing Guardian Bám ATR', desc: 'Tự động dời SL theo đỉnh nến để bảo toàn lãi (chiến công chốt lãi lệnh SOL thực chiến).' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Smart Router Sub-25ms', desc: 'Định tuyến khớp lệnh siêu tốc với Groq Llama-3.3-70B cho Đội 1, triệt tiêu trượt giá.' }
        ],
        primaryModel: 'Groq Llama-3.3-70B',
        fallbackModel: 'DeepSeek-V4-Flash (Vyce AI)',
        strategyRole: 'Execution OMS & Slippage Optimizer'
    },
    'Sniper': {
        name: 'Sniper',
        titleVi: 'Bắn Tỉa Spot DCA & Quản Trị Két Sắt 500U',
        deptKey: 'spot_dca',
        wingTag: '🌐 ĐỘI 2 · BỘ CHỈ HUY TÌNH BÁO 9ROUTER',
        fleetType: 'FLEET_2_INTELLIGENCE',
        fleetBadge: '🌐 BỘ CHỈ HUY TÌNH BÁO 9ROUTER',
        rpgClass: 'Patient Asset Accumulator · Tier S+',
        level: 47,
        expStr: '41,500 / 46,000 EXP',
        expPct: 90,
        avatar: '/static/images/sprites/sprite_06_community.png',
        color: '#14b8a6',
        hpVal: '100% (An Toàn Tuyệt Đối)',
        hpPct: 100,
        hpHint: 'Két sắt 450U Vault được khóa an toàn ngoài sàn Futures',
        mpVal: '96% (Claude-Sonnet-4-6)',
        mpPct: 96,
        mpHint: 'Claude-Sonnet-4-6 Vyce AI · Tính toán điểm chiết khấu On-chain',
        stats: { speed: 85, accuracy: 94, discipline: 99, alpha: 93, defense: 98, vision: 95 },
        skills: [
            {
                name: 'Bắn Tỉa Spot DCA 500U Điểm Chiết Khấu Sâu',
                icon: '💎',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Khi giá giảm sâu',
                desc: 'Tích lũy coin nền tảng (BTC, ETH, SOL) tại các vùng hỗ trợ On-chain $80k–$83k mà không lo áp lực cháy tài khoản.'
            },
            {
                name: 'Quản Trị Két Sắt 450U Vault Bất Khả Xâm Phạm',
                icon: '🏦',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Thường trực',
                desc: 'Khóa chặt 450U vốn dự trữ ngoài sàn phái sinh, chỉ cho phép bot chạy thực chiến với đúng 50U để kiểm chứng độ bền.'
            },
            {
                name: 'Chiến Thuật Mua 3 Phần Tối Ưu Giá Vốn',
                icon: '🎯',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Theo chu kỳ tuần',
                desc: 'Chia vốn làm 3 phần mua rải theo mô hình tính toán của ChatGPT/Astra, tối ưu phí giao dịch BNB 0.075% và trượt giá.'
            }
        ],
        quote: 'Futures để đánh du kích kiếm tiền chợ, Spot DCA mới là chân ái để xây dựng gia tài dài hạn cho Boss!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'Chiến Lược Tích Lũy Spot', desc: 'Tách bạch danh mục Spot tích lũy dài hạn và Futures lướt sóng ngắn hạn.' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'Cơ Chế Khóa Két 450U Vault', desc: 'Khóa chặt 450U vốn dự trữ ngoài sàn phái sinh, chỉ cho bot chạy thực chiến với đúng 50U.' },
            { ver: 'GĐ 3 (22/09/2026)', model: '9Router Codex (GPT-5.5)', desc: 'Phân tích điểm chiết khấu On-chain sâu cho BTC/ETH/SOL tại các vùng hỗ trợ cứng.' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Trinh Sát Đáy Đội Tình Báo', desc: 'Tiếp nhận chỉ thị vĩ mô từ Hash để kích hoạt mua rải Spot 3 phần tối ưu giá vốn.' }
        ],
        primaryModel: 'cx/gpt-5.5 (9Router Codex)',
        fallbackModel: 'cx/gpt-5.6-terra',
        strategyRole: 'Spot Accumulation & 450U Vault Strategy'
    },
    'Deck': {
        name: 'Deck',
        titleVi: 'Trọng Tài Phân Thù Arbitrage & Funding Rate',
        deptKey: 'arbitrage_desk',
        wingTag: '🌐 ĐỘI 2 · BỘ CHỈ HUY TÌNH BÁO 9ROUTER',
        fleetType: 'FLEET_2_INTELLIGENCE',
        fleetBadge: '🌐 BỘ CHỈ HUY TÌNH BÁO 9ROUTER',
        rpgClass: 'Cross-Venue Spread Arbiter · Tier S',
        level: 44,
        expStr: '35,600 / 40,000 EXP',
        expPct: 89,
        avatar: '/static/images/sprites/sprite_04_quant.png',
        color: '#8b5cf6',
        hpVal: '100% (Delta-Neutral)',
        hpPct: 100,
        hpHint: 'Vị thế trung lập phi rủi ro giá biến động',
        mpVal: '94% (GPT-5.6-Terra)',
        mpPct: 94,
        mpHint: 'GPT-5.6-Terra 9Router · Quét chênh lệch spread & funding đa sàn',
        stats: { speed: 96, accuracy: 90, discipline: 96, alpha: 89, defense: 97, vision: 89 },
        skills: [
            {
                name: 'Trọng Tài Phân Thù Spread Arbitrage',
                icon: '⚖️',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Theo chu kỳ 10s',
                desc: 'Quét chênh lệch giá giữa các cặp giao dịch trên CCXT, bắt cơ hội phân thù giá khi có sai lệch thị trường.'
            },
            {
                name: 'Bào Phí Funding Rate Đa Sàn',
                icon: '💸',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Mỗi 8 Giờ',
                desc: 'Thu lợi nhuận thụ động từ phí Funding Rate khi thị trường quá hưng phấn Long hoặc quá hoảng loạn Short.'
            },
            {
                name: 'Khóa Spread Delta-Neutral Tuyệt Đối',
                icon: '🔒',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Khi Spread > 0.25%',
                desc: 'Mở đồng thời vị thế Long Spot và Short Futures tương ứng để khóa trọn lợi nhuận mà không chịu rủi ro giá sập.'
            }
        ],
        quote: 'Thị trường có thể điên cuồng, nhưng toán học thì không bao giờ nói dối. Lợi nhuận phi rủi ro là thứ tinh túy nhất của Quant!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'Quét Funding Rate 8H', desc: 'Đọc tỷ lệ funding rate trên Binance Futures để phát hiện cơ hội ăn phí chênh lệch.' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'Bắt Squeeze Funding Sàn', desc: 'Phát hiện tình trạng funding quá âm hoặc quá dương để cảnh báo các đợt ép phe.' },
            { ver: 'GĐ 3 (22/09/2026)', model: 'Mô Hình Phân Thù Đa Sàn', desc: 'Kết hợp 9Router Codex phân tích chênh lệch spread delta-neutral giữa các cặp coin.' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Tình Báo Phân Thù Đội 2', desc: 'Cảnh báo áp lực thanh lý và cơ hội bào funding cho toàn bộ hội đồng giao dịch.' }
        ],
        primaryModel: 'cx/gpt-5.6-terra (9Router Codex)',
        fallbackModel: 'gcli/grok-4.7',
        strategyRole: 'Cross-Venue Spread & Funding Arbiter'
    },
    'Hash': {
        name: 'Hash',
        titleVi: 'Trinh Sát Tin Tức & NLP On-Chain Sentiment',
        deptKey: 'news_scout',
        wingTag: '🌐 ĐỘI 2 · BỘ CHỈ HUY TÌNH BÁO 9ROUTER',
        fleetType: 'FLEET_2_INTELLIGENCE',
        fleetBadge: '🌐 BỘ CHỈ HUY TÌNH BÁO 9ROUTER',
        rpgClass: 'Macro Sentiment Oracle · Tier S+',
        level: 47,
        expStr: '42,900 / 46,000 EXP',
        expPct: 93,
        avatar: '/static/images/sprites/sprite_03_scout.png',
        color: '#06b6d4',
        hpVal: '100% (An Toàn)',
        hpPct: 100,
        hpHint: 'Cảnh báo sớm tin tức Mỹ điều tra Binance & FedWatch 28/10',
        mpVal: '97% (GPT-5.6-Terra)',
        mpPct: 97,
        mpHint: 'GPT-5.6-Terra 9Router · Quét tin vĩ mô và dòng tiền cá voi 24/7',
        stats: { speed: 91, accuracy: 93, discipline: 92, alpha: 90, defense: 92, vision: 100 },
        skills: [
            {
                name: 'Thiên Lý Nhãn Macro 9Router Sentinel',
                icon: '📡',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Liên tục 24/7',
                desc: 'Quét tin tức nóng từ Bloomberg, Reuters, CME FedWatch và Bộ Tư Pháp Mỹ (DOJ), phát hiện sự kiện thiên nga đen.'
            },
            {
                name: 'Truy Tìm Dòng Tiền Ví Cá Voi On-Chain',
                icon: '🐋',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Theo khối block',
                desc: 'Phát hiện các giao dịch chuyển tiền trên 1,000 BTC ra vào các ví sàn để cảnh báo phe xả hoặc phe gom hàng.'
            },
            {
                name: 'Giải Mã Tâm Lý FUD/FOMO Định Lượng',
                icon: '🧠',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Khi có biến động tin tức',
                desc: 'Định lượng mức độ cực đoan của thị trường qua NLP, ngăn không cho bot fomo vào đỉnh hoặc bán tháo ở đáy.'
            }
        ],
        quote: 'Tin đồn mua vào, tin thật bán ra. Nhưng người có dữ liệu On-chain và NLP chuẩn xác thì luôn đi trước đám đông 3 bước!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'Radar Tin Tức Crypto', desc: 'Thu thập dữ liệu tin nóng và chỉ số Tham Lam / Sợ Hãi (Fear & Greed Index).' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'Cảnh Báo Tin Vĩ Mô & Whale', desc: 'Quét các giao dịch lớn của cá voi on-chain và tin tức từ DOJ, SEC, CME FedWatch.' },
            { ver: 'GĐ 3 (22/09/2026)', model: '9Router Grok-4.7 Tình Báo', desc: 'Tích hợp Grok-4.7 CLI và GPT-5.6-Terra qua 9Router phân tích tâm lý vĩ mô chuyên sâu.' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Chỉ Huy Tình Báo Vĩ Mô Đội 2', desc: 'Phát trực tiếp Chỉ Thị Vĩ Mô (Macro Directive) sang Đội Tác Chiến Tầng Trade và Telegram.' }
        ],
        primaryModel: 'gcli/grok-4.7 (9Router Grok CLI)',
        fallbackModel: 'cx/gpt-5.6-terra (9Router Codex)',
        strategyRole: 'Macro Sentiment & On-Chain Reconnaissance'
    },
    'Core': {
        name: 'Core',
        titleVi: 'Kiểm Toán Trưởng & Kỹ Sư Đúc Kết Bài Học Post-Mortem',
        deptKey: 'accounting_pm',
        wingTag: '10 · KẾ TOÁN & BÀI HỌC',
        rpgClass: 'Archival Chrono-Analyst · Tier S+',
        level: 48,
        expStr: '45,300 / 48,000 EXP',
        expPct: 94,
        avatar: '/static/images/sprites/sprite_01_pm.png',
        color: '#10b981',
        hpVal: '100% (An Toàn)',
        hpPct: 100,
        hpHint: 'Đã lưu trữ 37 Bài Học Xương Máu · Đối soát PnL từng xu',
        mpVal: '98% (DeepSeek-V4-Flash)',
        mpPct: 98,
        mpHint: 'DeepSeek-V4-Flash Vyce AI · Tự động sinh biên bản sau mỗi lệnh đóng',
        stats: { speed: 89, accuracy: 97, discipline: 99, alpha: 88, defense: 98, vision: 92 },
        skills: [
            {
                name: 'Kiểm Toán Sổ Cái High-Water Mark',
                icon: '📑',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Mỗi lệnh đóng',
                desc: 'Đối soát chi tiết PnL gộp, phí hoa hồng BNB 0.075%, funding rate và trượt giá, tính toán chính xác PnL ròng.'
            },
            {
                name: 'Giải Phẫu Bài Học Post-Mortem Tức Thì',
                icon: '🔬',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Tự động',
                desc: 'Phân tích nguyên nhân lệnh thắng/thua, tự động đúc rút bài học và ghi vào kho tri thức SQLite trading_bot.db.'
            },
            {
                name: 'Định Lượng Tỷ Lệ Sharpe & Sức Bền Danh Mục',
                icon: '📊',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Cuối ngày 22h',
                desc: 'Đo lường hệ số Sharpe, Sortino và Calmar Ratio để đánh giá xem chiến lược đang ăn may hay thực sự có edge thị trường.'
            }
        ],
        quote: 'Không rút kinh nghiệm sau mỗi lệnh thua thì bao nhiêu vốn cũng sẽ cháy. Kế toán chuẩn chỉ là nền móng của công ty!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'Nhật Ký Lệnh SQLite', desc: 'Lưu trữ chi tiết mọi lệnh mở/đóng vào cơ sở dữ liệu SQLite cục bộ trading_bot.db.' },
            { ver: 'GĐ 2 (20/09/2026)', model: '37 Bài Học Xương Máu', desc: 'Đúc kết kinh nghiệm sau mỗi lệnh, gắn mã lỗi và đối soát PnL ròng trừ phí BNB 0.075%.' },
            { ver: 'GĐ 3 (22/09/2026)', model: 'Phân Tích Đa Não Post-Mortem', desc: 'Sử dụng DeepSeek-V4-Flash qua Vyce AI phân tích nguyên nhân thắng thua tự động.' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Kiểm Toán Hai Đội Tác Chiến', desc: 'Đối soát hiệu suất khớp lệnh Đội 1 và độ chính xác dự báo vĩ mô từ Đội 2.' }
        ],
        primaryModel: 'DeepSeek-V4-Flash (Vyce AI)',
        fallbackModel: 'Gemini-3.8-Flash (Google)',
        strategyRole: 'Post-Mortem Auditor & Sharpe Ratio Analyst'
    },
    'Prof': {
        name: 'Prof',
        titleVi: 'Giáo Sư Kiểm Soát Ký Quỹ & CVaR Sentinel',
        deptKey: 'cvar_stress',
        wingTag: '12 · KIỂM SOÁT KÝ QUỸ',
        rpgClass: 'Extreme Risk Mathematician · Tier SS',
        level: 49,
        expStr: '47,800 / 50,000 EXP',
        expPct: 96,
        avatar: '/static/images/sprites/sprite_02_risk.png',
        color: '#f43f5e',
        hpVal: '100% (Zero Liquidation Risk)',
        hpPct: 100,
        hpHint: 'Khoảng cách thanh lý: Vô cực · Đòn bẩy an toàn kiểm soát',
        mpVal: '96% (GPT-OSS-120B)',
        mpPct: 96,
        mpHint: 'Groq GPT-OSS-120B · Mô phỏng 10,000 kịch bản Monte Carlo',
        stats: { speed: 94, accuracy: 96, discipline: 100, alpha: 86, defense: 100, vision: 95 },
        skills: [
            {
                name: 'Tường Lửa CVaR 99% Tail Risk Shield',
                icon: '🗄️',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Liên tục',
                desc: 'Tính toán Conditional Value at Risk độ tin cậy 99%, triệt tiêu 100% rủi ro cháy tài khoản trong các cú flash-crash.'
            },
            {
                name: 'Mô Phỏng 10,000 Kịch Bản Monte Carlo',
                icon: '🎲',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Khi mở vị thế mới',
                desc: 'Chạy 10,000 kịch bản biến động ngẫu nhiên để thử tải xem tài khoản 50U có chịu nổi cú sập 20% của Bitcoin hay không.'
            },
            {
                name: 'Cắt Giảm Đòn Bẩy Khẩn Cấp Liquidation Guard',
                icon: '🛡️',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Thường trực',
                desc: 'Can thiệp hạ đòn bẩy hoặc ép đóng vị thế nếu khoảng cách đến giá thanh lý thu hẹp dưới 35% khoảng đệm an toàn.'
            }
        ],
        quote: 'Trong thị trường tài chính, những gì có thể sai thì chắc chắn sẽ sai vào lúc ta bất cẩn nhất. Đề phòng thiên nga đen là sự sống còn!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'Giám Sát Tỷ Lệ Ký Quỹ', desc: 'Đảm bảo Margin Ratio tài khoản Binance Futures luôn duy trì dưới 2% an toàn tuyệt đối.' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'CVaR 99% Tail Risk Shield', desc: 'Tính toán Conditional Value at Risk 99%, triệt tiêu 100% rủi ro cháy tài khoản khi có flash-crash.' },
            { ver: 'GĐ 3 (22/09/2026)', model: 'Mô Phỏng Monte Carlo 10,000', desc: 'Chạy 10,000 kịch bản biến động ngẫu nhiên để thử tải tài khoản 50U trước các cú sập 20%.' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Lá Chắn Lượng Tử Đội 2', desc: 'Cùng 9Router tính toán rủi ro vĩ mô trước khi cho phép Astra nâng quy mô vị thế.' }
        ],
        primaryModel: 'cx/gpt-5.6-terra (9Router Codex)',
        fallbackModel: 'deepseek-v4.1 (Vyce AI)',
        strategyRole: 'CVaR Sentinel & Liquidation Risk Eliminator'
    },
    'Square': {
        name: 'Square',
        titleVi: 'Giám Đốc Quan Hệ Cộng Đồng & Binance Square',
        deptKey: 'community_affiliate',
        wingTag: '11 · KHÁCH HÀNG & SQUARE',
        rpgClass: 'Community Signal Broadcast Master · Tier S',
        level: 43,
        expStr: '33,200 / 40,000 EXP',
        expPct: 83,
        avatar: '/static/images/sprites/sprite_06_community.png',
        color: '#3b82f6',
        hpVal: '100% (Uy Tín Cao)',
        hpPct: 100,
        hpHint: 'Kênh truyền thông minh bạch · Bảo vệ uy tín thương hiệu Astra',
        mpVal: '95% (GPT-5.6-Luna)',
        mpPct: 95,
        mpHint: 'GPT-5.6-Luna 9Router · Tự động biên tập nội dung chuyên nghiệp',
        stats: { speed: 92, accuracy: 88, discipline: 93, alpha: 87, defense: 90, vision: 96 },
        skills: [
            {
                name: 'Truyền Tin Tốc Hành Binance Square Pro',
                icon: '📱',
                type: 'CHỦ ĐỘNG',
                cooldown: 'Theo sự kiện lệnh',
                desc: 'Phát sóng tín hiệu lệnh, kết quả khớp lệnh và phân tích kỹ thuật minh bạch lên nền tảng Binance Square.'
            },
            {
                name: 'Tổng Hợp Sentiment Đám Đông Retail',
                icon: '👥',
                type: 'BỊ ĐỘNG PASSIVE',
                cooldown: 'Liên tục',
                desc: 'Lắng nghe phản ứng của nhà đầu tư nhỏ lẻ để giúp Ban Chiến Lược nhận biết các bẫy tâm lý đám đông.'
            },
            {
                name: 'Báo Động Telegram Khẩn Cấp Cho Boss',
                icon: '🔔',
                type: 'TUYỆT KỸ ULTIMATE',
                cooldown: 'Tức thì (< 1s)',
                desc: 'Bắn tin nhắn Telegram tức thì khi có lệnh khớp, Trailing Stop kích hoạt, chốt lời hoặc có quyết định Veto quan trọng.'
            }
        ],
        quote: 'Minh bạch là đỉnh cao của sự chuyên nghiệp. Một quỹ định lượng uy tín phải công khai hiệu suất và tôn trọng cộng đồng!',
        lineage: [
            { ver: 'GĐ 1 (19/09/2026)', model: 'Telegram Alert Bot', desc: 'Bắn thông báo khớp lệnh và biến động tài khoản tức thì vào kênh chat Telegram cho Thượng Đế.' },
            { ver: 'GĐ 2 (20/09/2026)', model: 'Card Báo Cáo Chuyên Nghiệp', desc: 'Định dạng tin nhắn trực quan với emoji, PnL, điểm vào lệnh, giá thanh lý và SL/TP.' },
            { ver: 'GĐ 3 (22/09/2026)', model: 'Tích Hợp GPT-5.6-Luna (9Router)', desc: 'Chuẩn bị nội dung phân tích định lượng chuyên môn cao để tương tác Binance Square.' },
            { ver: 'GĐ 4 (Hiện tại)', model: 'Phát Ngôn Viên Hai Đội', desc: 'Báo cáo Chỉ Thị Vĩ Mô từ Đội 2 và cập nhật diễn biến khớp lệnh Tầng Trade cho Thượng Đế.' }
        ],
        primaryModel: 'cx/gpt-5.6-luna (9Router Codex)',
        fallbackModel: 'cx/gpt-5.6-terra',
        strategyRole: 'Community Relations & Binance Square Broadcaster'
    }
};

window.openAgentRpgSheet = function(agentIdentifier = 'Astra') {
    // Unconditionally hide department modal if open
    const deptModal = document.getElementById('pixelDeptModal');
    if (deptModal) deptModal.style.display = 'none';

    // Resolve agent name
    let agName = agentIdentifier;
    if (!window.AGENT_RPG_REGISTRY[agName]) {
        for (let k in window.AGENT_RPG_REGISTRY) {
            if (window.AGENT_RPG_REGISTRY[k].deptKey === agentIdentifier || k.toLowerCase() === String(agentIdentifier).toLowerCase()) {
                agName = k;
                break;
            }
        }
    }
    const agent = window.AGENT_RPG_REGISTRY[agName] || window.AGENT_RPG_REGISTRY['Astra'];
    window.currentRpgAgent = agent.name;

    const modal = document.getElementById('agentRpgStatModal');
    if (!modal) {
        console.error('[RPG] agentRpgStatModal not found in DOM');
        return;
    }

    if (document.pointerLockElement) {
        try { document.exitPointerLock(); } catch (_) {}
    }

    // Populate Header
    const avatarImg = document.getElementById('rpgAgentAvatar');
    if (avatarImg) avatarImg.src = agent.avatar;

    const levelBadge = document.getElementById('rpgAgentLevelBadge');
    if (levelBadge) {
        levelBadge.textContent = `LV.${agent.level}`;
        levelBadge.style.boxShadow = `0 0 10px ${agent.color}`;
    }

    const avatarBox = document.getElementById('rpgAgentAvatarBox');
    if (avatarBox) {
        avatarBox.style.borderColor = agent.color;
        avatarBox.style.boxShadow = `0 0 22px ${agent.color}55`;
    }

    const wingTag = document.getElementById('rpgAgentWingTag');
    if (wingTag) {
        wingTag.textContent = agent.wingTag;
        wingTag.style.color = agent.color;
    }

    const nameEl = document.getElementById('rpgAgentName');
    if (nameEl) nameEl.textContent = agent.name;

    const titleSubEl = document.getElementById('rpgAgentTitleSub');
    if (titleSubEl) titleSubEl.textContent = `— ${agent.titleVi}`;

    const classEl = document.getElementById('rpgAgentClass');
    if (classEl) classEl.textContent = agent.rpgClass;

    // Vitality Bars
    const hpVal = document.getElementById('rpgHpVal');
    const hpFill = document.getElementById('rpgHpFill');
    const hpHint = document.getElementById('rpgHpHint');
    if (hpVal) hpVal.textContent = agent.hpVal;
    if (hpFill) hpFill.style.width = `${agent.hpPct}%`;
    if (hpHint) hpHint.textContent = agent.hpHint;

    const mpVal = document.getElementById('rpgMpVal');
    const mpFill = document.getElementById('rpgMpFill');
    const mpHint = document.getElementById('rpgMpHint');
    if (mpVal) mpVal.textContent = agent.mpVal;
    if (mpFill) mpFill.style.width = `${agent.mpPct}%`;
    if (mpHint) mpHint.textContent = agent.mpHint;

    const expVal = document.getElementById('rpgExpVal');
    const expFill = document.getElementById('rpgExpFill');
    const expHint = document.getElementById('rpgExpHint');
    if (expVal) expVal.textContent = agent.expStr;
    if (expFill) expFill.style.width = `${agent.expPct}%`;
    if (expHint) expHint.textContent = `Bậc 4 Hội Đồng Tối Tân · ${agent.strategyRole}`;

    // Render Hexagon Radar Chart & Stat Badges
    try {
        renderHexagonRadar(agent.stats, agent.color);
    } catch (e) {
        console.warn('[RPG] Radar render warn:', e);
    }

    const badgesGrid = document.getElementById('rpgStatBadgesGrid');
    if (badgesGrid) {
        const labels = [
            { k: 'speed', n: 'TỐC ĐỘ' },
            { k: 'accuracy', n: 'CHÍNH XÁC' },
            { k: 'discipline', n: 'KỶ LUẬT' },
            { k: 'alpha', n: 'ALPHA PNL' },
            { k: 'defense', n: 'PHÒNG THỦ' },
            { k: 'vision', n: 'TẦM NHÌN' }
        ];
        badgesGrid.innerHTML = labels.map(l => `
            <div class="rpg-stat-chip">
                <div class="rpg-stat-chip-name">${l.n}</div>
                <div class="rpg-stat-chip-val" style="color: ${agent.color};">${agent.stats[l.k]} / 100</div>
            </div>
        `).join('');
    }

    // Render 3 Active Skills
    const skillsList = document.getElementById('rpgSkillsList');
    if (skillsList) {
        skillsList.innerHTML = agent.skills.map((s, idx) => `
            <div class="rpg-skill-card" style="border-left-color: ${agent.color};">
                <div class="rpg-skill-header">
                    <span class="rpg-skill-title">
                        <span>${s.icon}</span> <span>${s.name}</span>
                    </span>
                    <div class="rpg-skill-tags">
                        <span class="rpg-skill-type" style="color:${agent.color}; border-color:${agent.color}55; background:${agent.color}15;">${s.type}</span>
                        <span class="rpg-skill-type" style="color:#94a3b8; border-color:#94a3b833; background:#1e293b55;">${s.cooldown}</span>
                    </div>
                </div>
                <div class="rpg-skill-desc">${s.desc}</div>
            </div>
        `).join('');
    }

    // Quote
    const quoteText = document.getElementById('rpgQuoteText');
    if (quoteText) quoteText.textContent = agent.quote;

    // Timeline Evolution (V1 -> V4)
    const timelineEl = document.getElementById('rpgLineageTimeline');
    if (timelineEl) {
        timelineEl.innerHTML = agent.lineage.map((step, idx) => `
            <div class="rpg-timeline-step ${idx === 3 ? 'active' : ''}">
                <div class="rpg-step-version">${step.ver}</div>
                <div class="rpg-step-model">${step.model}</div>
                <div class="rpg-step-desc">${step.desc}</div>
            </div>
        `).join('');
    }

    // Models Bar
    const priModel = document.getElementById('rpgPrimaryModel');
    if (priModel) priModel.textContent = agent.primaryModel;

    const fbkModel = document.getElementById('rpgFallbackModel');
    if (fbkModel) fbkModel.textContent = agent.fallbackModel;

    const stRole = document.getElementById('rpgStrategyRole');
    if (stRole) stRole.textContent = agent.strategyRole;

    modal.style.display = 'flex';
};

window.closeAgentRpgSheet = function() {
    const modal = document.getElementById('agentRpgStatModal');
    if (modal) modal.style.display = 'none';
};

function renderHexagonRadar(stats, accentColor = '#38bdf8') {
    const svg = document.getElementById('rpgHexagonSvg');
    if (!svg) return;

    const cx = 140;
    const cy = 120;
    const maxR = 85;
    const axesKeys = ['speed', 'accuracy', 'discipline', 'alpha', 'defense', 'vision'];
    const axesLabels = ['Tốc Độ', 'Chính Xác', 'Kỷ Luật', 'Alpha PnL', 'Phòng Thủ', 'Tầm Nhìn'];
    const angles = [0, 60, 120, 180, 240, 300].map(deg => (deg - 90) * (Math.PI / 180));

    // Helper: calculate point
    const getPoint = (val, angle) => {
        const r = (val / 100) * maxR;
        return {
            x: cx + r * Math.cos(angle),
            y: cy + r * Math.sin(angle)
        };
    };

    // Build 3 concentric reference web polygons (33%, 66%, 100%)
    let gridPolygons = [0.33, 0.66, 1.0].map(pct => {
        const pts = angles.map(a => `${cx + (maxR * pct) * Math.cos(a)},${cy + (maxR * pct) * Math.sin(a)}`).join(' ');
        return `<polygon points="${pts}" fill="none" stroke="rgba(56, 189, 248, 0.18)" stroke-width="1" />`;
    }).join('');

    // Radial spokes
    let spokes = angles.map(a => {
        const x2 = cx + maxR * Math.cos(a);
        const y2 = cy + maxR * Math.sin(a);
        return `<line x1="${cx}" y1="${cy}" x2="${x2}" y2="${y2}" stroke="rgba(56, 189, 248, 0.15)" stroke-width="1" stroke-dasharray="2,3" />`;
    }).join('');

    // Axis Labels
    let labels = angles.map((a, i) => {
        const lx = cx + (maxR + 18) * Math.cos(a);
        const ly = cy + (maxR + 18) * Math.sin(a) + 3;
        return `<text x="${lx}" y="${ly}" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="9" font-weight="700" fill="#94a3b8">${axesLabels[i]}</text>`;
    }).join('');

    // Value Polygon
    const valPoints = angles.map((a, i) => {
        const val = stats[axesKeys[i]] || 80;
        const pt = getPoint(val, a);
        return `${pt.x},${pt.y}`;
    }).join(' ');

    // Value Vertex Dots
    const dots = angles.map((a, i) => {
        const val = stats[axesKeys[i]] || 80;
        const pt = getPoint(val, a);
        return `<circle cx="${pt.x}" cy="${pt.y}" r="3.5" fill="${accentColor}" stroke="#ffffff" stroke-width="1.5" />`;
    }).join('');

    svg.innerHTML = `
        <defs>
            <radialGradient id="rpgRadarGrad" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stop-color="${accentColor}" stop-opacity="0.5" />
                <stop offset="100%" stop-color="${accentColor}" stop-opacity="0.1" />
            </radialGradient>
        </defs>
        ${gridPolygons}
        ${spokes}
        <polygon points="${valPoints}" fill="url(#rpgRadarGrad)" stroke="${accentColor}" stroke-width="2.5" />
        ${dots}
        ${labels}
    `;
}

window.openIntercomFromRpg = function() {
    const agent = window.currentRpgAgent || 'Astra';
    closeAgentRpgSheet();
    if (typeof window.openCyberIntercomModal === 'function') {
        window.openCyberIntercomModal(agent);
    }
};

window.focusCameraFromRpg = function() {
    const agent = window.currentRpgAgent || 'Astra';
    closeAgentRpgSheet();
    if (window.worldEngine && typeof window.worldEngine.setCameraMode === 'function') {
        window.worldEngine.setCameraMode('FOCUS', agent);
    } else if (window.officeEngine && typeof window.officeEngine.teleportToDept === 'function') {
        const meta = window.AGENT_RPG_REGISTRY[agent];
        if (meta && meta.deptKey) window.officeEngine.teleportToDept(meta.deptKey);
    }
};

window.openTelemetryFromRpg = function() {
    const agent = window.currentRpgAgent || 'Astra';
    const meta = window.AGENT_RPG_REGISTRY[agent];
    closeAgentRpgSheet();
    if (meta && meta.deptKey && typeof openDeptDetailModal === 'function') {
        openDeptDetailModal(meta.deptKey);
    }
};

window.openRpgFromDeptModal = function(evt) {
    if (evt) {
        try { evt.preventDefault(); evt.stopPropagation(); } catch (_) {}
    }
    const deptKey = window.currentModalDeptKey || window.activeModalDept || 'lead_pm';
    const deptModal = document.getElementById('pixelDeptModal');
    if (deptModal) {
        deptModal.style.display = 'none';
    }
    if (typeof window.openAgentRpgSheet === 'function') {
        window.openAgentRpgSheet(deptKey);
    } else {
        console.error('[RPG] openAgentRpgSheet not found!');
    }
};

// Global escape key listener to close RPG sheet
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const modal = document.getElementById('agentRpgStatModal');
        if (modal && modal.style.display === 'flex') {
            window.closeAgentRpgSheet();
        }
    }
});
