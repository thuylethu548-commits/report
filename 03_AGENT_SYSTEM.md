# 03. HỆ THỐNG TÁC TỬ & ĐỒNG THUẬN AI (AGENT SYSTEM & AI CONSENSUS)

Tài liệu này giải phẫu chi tiết toàn bộ các tác tử AI, bóc tách sự thật kỹ thuật (Technical Truth) giữa hình ảnh hiển thị trên UI và luồng thực thi mã nguồn thực tế (Code Trace).

---

## 1. Xác Minh Sự Thật Kỹ Thuật (Forensic Model Verification)

Trích xuất trực tiếp từ mã nguồn `ai_advisory/vyce_client.py`, `ai_advisory/adversarial_debater.py`, và `core/fleet_manager.py`:

### 1.1. SuperGrok 4.7 (`gcli/grok-4.7`) đang làm gì THỰC SỰ?
* **Mã nguồn định tuyến:** `ai_advisory/vyce_client.py` (dòng 259-271).
* **Bản chất kỹ thuật:** Model `gcli/grok-4.7` được chuyển tiếp qua cổng proxy cục bộ **9Router** (`http://localhost:20128/v1/chat/completions`) đang chạy trên VPS (PID 23060). 9Router kết nối trực tiếp với phiên làm việc Grok Web/CLI.
* **Nhiệm vụ thực tế trong code:**
  1. **Hiệp 2 trong Hội đồng Tranh biện Đối kháng (`AdversarialDebater.ROUND2_BEAR_PROMPT`):** Đóng vai *Chief Skeptic & Devil's Advocate Risk Officer*. Grok 4.7 nhận tín hiệu kỹ thuật và quét tìm bẫy thanh khoản (liquidity hunt wicks), phân kỳ đỉnh đáy, bẫy tăng giá/giảm giá (bull/bear trap), và rủi ro Funding Rate. Trả về JSON: `{"bear_counter_thesis": str, "trap_risk_score": 1-5}`.
  2. **Trinh sát Tình báo Vĩ mô (`Hash` - `MacroIntelligenceBridge`):** Quét tin tức và dữ liệu on-chain, tạo ra các chỉ thị vĩ mô lưu vào bảng `macro_strategic_directives`.
* **Fallback:** Nếu Grok 4.7 gặp lỗi timeout hoặc không phản hồi sau 18 giây, hệ thống fallback sang `qwen/qwen3.8-27b` (Groq LPU).

### 1.2. GPT-6-Astra (`cx/gpt-6-astra`) đang làm gì THỰC SỰ?
* **Mã nguồn định tuyến:** `ai_advisory/vyce_client.py` (dòng 259-271).
* **Bản chất kỹ thuật:** Model `cx/gpt-6-astra` (bí danh nội bộ của mô hình OpenAI Codex Plus cao cấp nhất được tích hợp trên 9Router) chuyển tiếp qua cổng proxy `http://localhost:20128/v1`.
* **Nhiệm vụ thực tế trong code:**
  1. **Hiệp 3 Trọng Tài VAR Tối Cao (`AdversarialDebater.ROUND3_ARBITER_PROMPT`):** Đóng vai *Supreme Quantitative Risk Arbiter*. Nhận toàn văn luận điểm của Phe Bò (Hiệp 1) và Phe Gấu (Hiệp 2). Ra phán quyết ràng buộc cuối cùng: Duyệt (`approved: true`) hoặc Phủ quyết (`approved: false`), xác định `risk_score` (1-5), `size_multiplier` (0.2-1.0) và giải trình `ruling_rationale`.
  2. **Tổng Chỉ Huy Tác Chiến (`Astra`):** Là bộ não tối cao trong hội đồng, tổng hợp tín hiệu từ các ban kỹ thuật và đưa ra khuyến nghị phân bổ vốn.
* **Fallback:** Nếu `cx/gpt-6-astra` không phản hồi trong 13 giây, hệ thống chuyển sang đồng trọng tài `gcli/grok-4.7`, và nếu tiếp tục trễ sẽ chuyển sang `claude-sonnet-4-6`.

### 1.3. Claude (`claude-sonnet-4-6`) đang làm gì THỰC SỰ?
* **Mã nguồn định tuyến:** `ai_advisory/vyce_client.py` (dòng 333).
* **Bản chất kỹ thuật:** Kết nối qua cổng Vyce AI Proxy Gateway (`https://vyceai.com/v1/chat/completions`) với API Key của Vyce.
* **Nhiệm vụ thực tế trong code:**
  1. **Cố Vấn Rủi Ro Tối Cao Cổ Điển (`VyceClient.evaluate_signal_veto`):** Trước khi nâng cấp sang chế độ Adversarial Debate, Claude là mô hình thẩm định đơn lẻ chính của hệ thống.
  2. **Trọng Tài Dự Phòng Khẩn Cấp (Arbiter Emergency Fallback):** Trong chế độ Adversarial Debate, nếu cả GPT-6-Astra và Grok 4.7 đều không khả dụng, Claude-Sonnet-4-6 được kích hoạt để đưa ra phán quyết cuối cùng với độ ổn định cao nhất.
  3. **Pháp Y Thất Bại Lệnh (`generate_post_mortem`):** Phân tích nguyên nhân khi một lệnh giao dịch chạm Stop Loss và đúc kết bài học vào bảng `trading_lessons`.

### 1.4. DeepSeek (`deepseek-v4.1` & `deepseek-v4-flash`) đang làm gì THỰC SỰ?
* **Mã nguồn định tuyến:** `ai_advisory/vyce_client.py`. `deepseek-r1` và `deepseek-v4` được map sang `deepseek-v4.1` qua Vyce AI Gateway.
* **Nhiệm vụ thực tế trong code:**
  1. **Phân Loại Chế Độ Thị Trường Tốc Độ Cao (`MarketRegimeClassifier`):** Phân tích mẫu hình nến và xác định regime thị trường với độ trễ thấp.
  2. **Trợ Lý Tư Vấn Trực Tiếp Trên Canvas (`canvas_routes.py`):** Phục vụ giao diện chat tương tác với lập trình viên trên Antigravity Canvas.

### 1.5. Groq Models (`openai/gpt-oss-120b` & `qwen/qwen3.8-27b`) đang làm gì THỰC SỰ?
* **Mã nguồn định tuyến:** `ai_advisory/vyce_client.py` (dòng 282-291) qua Groq LPU Cloud API (`https://api.groq.com/openai/v1`). Quản lý bể xoay tua key qua `GroqKeyPool` (`ai_advisory/groq_pool.py`).
* **Nhiệm vụ thực tế trong code:**
  1. **Hiệp 1 Phe Bò (`openai/gpt-oss-120b`):** Đóng vai *Lead Bullish Momentum Strategist*. Nhờ phần cứng chip LPU của Groq, mô hình xử lý xong luận điểm đà giá chỉ trong 80ms - 150ms.
  2. **Phản Biện Dự Phòng (`qwen/qwen3.8-27b`):** Thay thế Grok 4.7 bóc tách bẫy giá nếu kết nối 9Router bị nghẽn.
  3. **Đo Lường Biến Động (`Volt`):** Xử lý nhanh các chỉ số ADX và độ mở dải Bollinger.

---

## 2. Bảng Danh Bạ 12 Tác Tử Hệ Thống (Full Agent Specification)

```text
Danh bạ trích xuất từ: core.fleet_manager.AutonomousFleetCoordinator
```

### 1. Palermo
* **ID:** `Palermo`
* **Display Name:** Trưởng Ban Xu Hướng (Trend & MeanRev Gate)
* **Role:** Dự báo Xu hướng qua EMA & RSI
* **Model:** `openai/gpt-oss-120b` (Groq LPU)
* **Provider:** Groq Cloud API
* **Fallback Model:** `cx/gpt-5.6-sol`
* **Trigger:** Khi có nến mới 15m hoặc biến động giá vượt ngưỡng
* **Input:** Chuỗi nến OHLCV, EMA-20/50, RSI-14
* **Output:** Khuyến nghị hướng xu hướng (BULLISH/BEARISH/FLAT)
* **Prompt Location:** `strategies/ema_trend.py` (Code logic) & `ai_advisory/adversarial_debater.py` (Round 1)
* **Memory:** 10 nến gần nhất trong SQLite
* **Tools:** Chỉ báo kỹ thuật toán học nội bộ
* **Can delegate:** NO
* **Can veto:** NO (Chỉ đề xuất)
* **Can alter strategy:** NO
* **Can alter risk:** NO
* **Can submit order:** NO
* **Called by:** `EventBus` qua `MarketEvent`
* **Calls:** `Groq LPU API`
* **Current status:** ONLINE (Đội 1 · Trực Chiến Khớp Lệnh)

### 2. Rik
* **ID:** `Rik`
* **Display Name:** Cảnh Sát Rủi Ro (Circuit Breaker & Tail Risk Guard)
* **Role:** Ngắt mạch Rủi ro & Thẩm định Veto An Toàn Vốn
* **Model:** `Claude-Sonnet-4-6` (Vyce AI) / `cx/gpt-6-astra`
* **Provider:** Vyce AI / 9Router
* **Fallback Model:** `quantitative-fallback` (Quy tắc toán tiền định)
* **Trigger:** Khi có bất kỳ `SignalEvent` nào phát sinh từ chiến lược
* **Input:** Tín hiệu vào lệnh, Drawdown ngày, khoảng cách SL, Ký quỹ
* **Output:** Quyết định DUYỆT (Approve) hoặc BÁC BỎ (Veto)
* **Prompt Location:** `ai_advisory/vyce_client.py` (`VETO_SYSTEM_PROMPT`)
* **Memory:** Nhật ký lệnh và sụt giảm vốn trong ngày
* **Tools:** Bảng kiểm tra tiền định 8 bước (`RiskManager`)
* **Can delegate:** NO
* **Can veto:** **YES (Quyền Veto Tuyệt Đối)**
* **Can alter strategy:** NO
* **Can alter risk:** **YES (Có thể hạ size_multiplier xuống 0.2x)**
* **Can submit order:** NO (Chỉ duyệt hoặc chặn)
* **Called by:** `RiskManager.handle_signal()`
* **Calls:** `CircuitBreaker`, `FundingSentinel`, `TimeWindowRiskGuard`
* **Current status:** ONLINE (Đội 1 · Trực Chiến Khớp Lệnh)

### 3. Tory
* **ID:** `Tory`
* **Display Name:** Săn Hàng Đột Phá (Donchian Surge & Breakout)
* **Role:** Bắt nhịp Đột phá kênh Donchian-20
* **Model:** `Gemini-3.7-Flash` / `cx/gpt-5.6-terra`
* **Provider:** Google AI Studio / 9Router
* **Fallback Model:** `qwen/qwen3.8-27b`
* **Trigger:** Khi giá phá vỡ đỉnh/đáy 20 nến kèm Volume tăng vọt
* **Input:** Kênh giá Donchian, Volume trung bình 20 kỳ
* **Output:** Tín hiệu Breakout Surge BUY/SELL
* **Prompt Location:** `core/spatial_agent_brain.py`
* **Memory:** Lịch sử biến động khối lượng
* **Tools:** Indicator Donchian nội bộ
* **Can delegate:** NO
* **Can veto:** NO
* **Can alter strategy:** NO
* **Can alter risk:** NO
* **Can submit order:** NO
* **Called by:** `EventBus`
* **Calls:** Google Gemini API
* **Current status:** ONLINE (Đội 1 · Trực Chiến Khớp Lệnh)

### 4. Hash
* **ID:** `Hash`
* **Display Name:** Trinh Sát Tin Tức (Macro Reconnaissance Commander)
* **Role:** Đội Trưởng Tình Báo Vĩ Mô & Dữ Liệu On-Chain
* **Model:** `gcli/grok-4.7` (SuperGrok CLI)
* **Provider:** 9Router Gateway
* **Fallback Model:** `gemini-3.7-flash` / `qwen/qwen3.8-27b`
* **Trigger:** Quét định kỳ mỗi 30 phút hoặc khi có tin tức khẩn cấp
* **Input:** RSS feeds, CryptoCompare Macro News, On-chain data
* **Output:** Chỉ Thị Chiến Lược Vĩ Mô (`MacroStrategicDirectiveEvent`)
* **Prompt Location:** `core/macro_intelligence_bridge.py`
* **Memory:** Lưu trữ trong bảng `macro_strategic_directives` (79 directives)
* **Tools:** `MacroNewsScanner`, HTTP News Client
* **Can delegate:** **YES (Phát chỉ thị vĩ mô sang Astra)**
* **Can veto:** **YES (Có thể phát cảnh báo rủi ro vĩ mô yêu cầu hạ tỷ trọng)**
* **Can alter strategy:** NO
* **Can alter risk:** **YES (Đề xuất hệ số rủi ro vĩ mô)**
* **Can submit order:** NO
* **Called by:** PM2 `miner_daemon` / `main.py` background tasks
* **Calls:** `vyce_client.chat_completion(model="gcli/grok-4.7")`
* **Current status:** ONLINE (Đội 2 · Tình Báo Vĩ Mô)

### 5. Deck
* **ID:** `Deck`
* **Display Name:** Săn Chênh Lệch Giá (Cross-Pair Spreads & Funding Arb)
* **Role:** Giám sát tỷ lệ Funding Rate và chênh lệch Basis
* **Model:** `cx/gpt-5.6-terra`
* **Provider:** 9Router Free Pool
* **Fallback Model:** `openai/gpt-oss-120b`
* **Trigger:** Mỗi 8 giờ (kỳ Funding sàn Binance) hoặc quét 15m
* **Input:** Funding rates từ CCXT, Lãi suất vay Margin
* **Output:** Báo cáo cơ hội chênh lệch giá và cảnh báo Funding Squeeze
* **Prompt Location:** `risk_engine/funding_sentinel.py`
* **Memory:** Lịch sử Funding Rate các cặp
* **Tools:** CCXT Funding Rate Fetcher
* **Can delegate:** NO
* **Can veto:** **YES (Thông qua Funding Sentinel chặn lệnh nếu funding âm/dương cực đoan)**
* **Can alter strategy:** NO
* **Can alter risk:** NO
* **Can submit order:** NO
* **Called by:** `FundingSentinel`
* **Calls:** 9Router API
* **Current status:** ONLINE (Đội 2 · Tình Báo Vĩ Mô)

### 6. Prof
* **ID:** `Prof`
* **Display Name:** Gác Cổng Thanh Lý (CVaR Sentinel & Liquidation Guard)
* **Role:** Kiểm soát Ký Quỹ, Đòn bẩy & Khoảng cách Giá Thanh Lý
* **Model:** `cx/gpt-5.6-sol` (OpenAI Codex Plus)
* **Provider:** 9Router / GuRouter
* **Fallback Model:** `openai/gpt-oss-120b`
* **Trigger:** Khi chuẩn bị tính toán kích thước vị thế (Position Sizing)
* **Input:** Đòn bẩy hiện tại, Tỷ lệ ký quỹ (Margin Ratio), Mark Price
* **Output:** Khoảng cách thanh lý an toàn (Liquidation Distance Buffer %)
* **Prompt Location:** `core/quantum_5d_engine.py` (D5 Risk Dimension)
* **Memory:** Thông số tài khoản Binance Futures
* **Tools:** Mô hình toán CVaR & Gaussian VaR
* **Can delegate:** NO
* **Can veto:** **YES (Veto nếu đòn bẩy khiến khoảng cách thanh lý < 8%)**
* **Can alter strategy:** NO
* **Can alter risk:** **YES (Áp trần quy mô lệnh)**
* **Can submit order:** NO
* **Called by:** `RiskManager`
* **Calls:** 9Router API
* **Current status:** ONLINE (Đội 2 · Tình Báo Vĩ Mô)

### 7. Meme
* **ID:** `Meme`
* **Display Name:** Đội Khớp Lệnh (Execution OMS & Slippage Optimizer)
* **Role:** Tối ưu hóa khớp lệnh tốc độ cao & Kích hoạt Trailing Stop
* **Model:** `@cf/meta/llama-3.3-70b-instruct-fp8-fast`
* **Provider:** Cloudflare Workers AI
* **Fallback Model:** Logic thuật toán Python thuần túy
* **Trigger:** Khi có `OrderEvent` đã được duyệt
* **Input:** Chi tiết lệnh, độ trễ mạng, độ sâu sổ lệnh Orderbook
* **Output:** Lệnh Market gửi lên Binance và đăng ký Trailing Stop
* **Prompt Location:** `execution/binance_executor.py`
* **Memory:** Bảng `execution_state`
* **Tools:** CCXT create_order, cancel_order
* **Can delegate:** NO
* **Can veto:** **YES (Chặn lệnh nếu độ trượt giá hoặc giới hạn sàn không hợp lệ)**
* **Can alter strategy:** NO
* **Can alter risk:** NO
* **Can submit order:** **YES (Là thực thể duy nhất gửi lệnh lên sàn Binance)**
* **Called by:** `BinanceExecutor.handle_order()`
* **Calls:** Binance Futures REST API
* **Current status:** ONLINE (Đội 1 · Trực Chiến Khớp Lệnh)

### 8. Volt
* **ID:** `Volt`
* **Display Name:** Đo Lường Biến Động (Macro Regime & Volatility Detector)
* **Role:** Phân loại Chế độ Thị trường (ADX / ATR / Bollinger Width)
* **Model:** `qwen/qwen3.8-27b` (Groq LPU)
* **Provider:** Groq API
* **Fallback Model:** `gemini-3.7-flash`
* **Trigger:** Mỗi khi nến 15m đóng cửa
* **Input:** Chỉ số ADX-14, ATR-14, Độ lệch chuẩn giá
* **Output:** Chế độ thị trường: `BULL_TREND`, `BEAR_TREND`, `RANGING`, `EXTREME_VOLATILITY`
* **Prompt Location:** `ai_advisory/regime_classifier.py`
* **Memory:** Lịch sử chế độ thị trường trong SQLite
* **Tools:** Chỉ báo biến động nội bộ
* **Can delegate:** NO
* **Can veto:** **YES (Veto toàn bộ lệnh nếu thị trường rơi vào EXTREME_VOLATILITY)**
* **Can alter strategy:** NO
* **Can alter risk:** **YES (Điều chỉnh ATR Multiplier cho Stop Loss)**
* **Can submit order:** NO
* **Called by:** `MarketRegimeClassifier`
* **Calls:** Groq API
* **Current status:** ONLINE (Đội 1 · Trực Chiến Khớp Lệnh)

### 9. Core
* **ID:** `Core`
* **Display Name:** Kế Toán & Bài Học (Backtest, Sharpe & Post-Mortem)
* **Role:** Pháp y Lịch sử Giao dịch & Đúc kết Bài học Kinh nghiệm
* **Model:** `cx/gpt-5.6-terra` (9Router Free Pool)
* **Provider:** 9Router Gateway
* **Fallback Model:** `claude-sonnet-4-6` (Vyce AI)
* **Trigger:** Ngay sau khi một vị thế đóng (`FillEvent` với `reduce_only=True`)
* **Input:** Lịch sử lệnh, PnL thực nhận, Lý do vào lệnh ban đầu
* **Output:** Bản phân tích bài học (Post-Mortem Analysis) ghi vào `trading_lessons`
* **Prompt Location:** `ai_advisory/vyce_client.py` (`generate_post_mortem`)
* **Memory:** Bảng `trading_lessons` (hiện có 40 bài học thực tế)
* **Tools:** Phân tích toán thống kê Sharpe, Drawdown
* **Can delegate:** NO
* **Can veto:** NO
* **Can alter strategy:** NO
* **Can alter risk:** NO
* **Can submit order:** NO
* **Called by:** `BinanceExecutor.sync_open_positions()` khi phát hiện lệnh đóng
* **Calls:** 9Router / Vyce AI
* **Current status:** ONLINE (Đội 2 · Tình Báo Vĩ Mô)

### 10. Sniper
* **ID:** `Sniper`
* **Display Name:** Tích Sản Spot DCA (Spot Accumulation & 450U Vault Strategy)
* **Role:** Quản lý danh mục tích sản Spot BTC, ETH, SOL & Két vốn 450U
* **Model:** `cx/gpt-5.6-sol` (OpenAI Codex Plus)
* **Provider:** 9Router Gateway
* **Fallback Model:** `claude-sonnet-4-6`
* **Trigger:** Khi thị trường điều chỉnh sâu (RSI < 30 trên khung ngày)
* **Input:** Giá Spot các đồng coin nền tảng, số dư USDT Spot
* **Output:** Lệnh tích sản Spot Smart DCA (3 tầng: Hold, Scalp, Breakout)
* **Prompt Location:** `scripts/ai_spot_sniper.py`
* **Memory:** Bảng `client_trades`, số dư ví Spot
* **Tools:** CCXT Binance Spot Client
* **Can delegate:** NO
* **Can veto:** NO
* **Can alter strategy:** NO
* **Can alter risk:** NO
* **Can submit order:** **YES (Chỉ trên thị trường Spot không đòn bẩy qua daemon `ai_spot_sniper.py`)**
* **Called by:** PM2 `ai-spot-sniper`
* **Calls:** Binance Spot API
* **Current status:** ONLINE (Đội 2 · Tình Báo Vĩ Mô)

### 11. Square
* **ID:** `Square`
* **Display Name:** Truyền Thông & CRM (Community & Binance Square Growth)
* **Role:** Tự động hóa nội dung định lượng trên Binance Square & Thu hút Ref
* **Model:** `cx/gpt-5.6-luna` (9Router Free Pool)
* **Provider:** 9Router Gateway
* **Fallback Model:** `openai/gpt-oss-120b`
* **Trigger:** Định kỳ hằng ngày hoặc sau các nhịp sóng biến động lớn
* **Input:** PnL thực tế của bot, bài học định lượng, mã Ref `GRO_28502_O41DR`
* **Output:** Bản thảo bài viết Markdown chuẩn phong cách Binance Square
* **Prompt Location:** `monitoring/binance_square_publisher.py`
* **Memory:** Bảng `affiliate_events`
* **Tools:** Markdown Generator & Square Publisher Client
* **Can delegate:** NO
* **Can veto:** NO
* **Can alter strategy:** NO
* **Can alter risk:** NO
* **Can submit order:** NO
* **Called by:** API `/api/v1/square/generate`
* **Calls:** 9Router API
* **Current status:** ONLINE (Đội 2 · Tình Báo Vĩ Mô)

### 12. Astra
* **ID:** `Astra`
* **Display Name:** Tổng Quản Tối Cao (Consensus Orchestrator & Tactical Commander)
* **Role:** Chỉ Huy Trưởng Hội Đồng Tác Chiến & Trọng Tài Tối Cao
* **Model:** `cx/gpt-6-astra` (OpenAI Codex Plus) / `Claude-Sonnet-4-6`
* **Provider:** 9Router / Vyce AI
* **Fallback Model:** `claude-sonnet-4-6`
* **Trigger:** Khi Hội đồng Đối kháng hoàn thành Hiệp 1 và Hiệp 2
* **Input:** Toàn bộ tín hiệu kỹ thuật, Luận điểm Phe Bò, Phản biện Phe Gấu
* **Output:** Phán quyết Chung Khảo tối hậu: `APPROVED_LONG / APPROVED_SHORT / VETOED`
* **Prompt Location:** `ai_advisory/adversarial_debater.py` (`ROUND3_ARBITER_PROMPT`)
* **Memory:** Toàn bộ lịch sử tranh biện và bài học của hệ thống
* **Tools:** Bộ quy tắc Alpha Generation Doctrine
* **Can delegate:** **YES (Điều phối các ban)**
* **Can veto:** **YES (Quyền Veto Tối Cao)**
* **Can alter strategy:** NO (Chiến lược do toán định hình)
* **Can alter risk:** **YES (Quyết định hệ số phân bổ vốn `size_multiplier`)**
* **Can submit order:** NO (Chỉ chuyển phán quyết sang `RiskManager`)
* **Called by:** `AdversarialDebater.debate_signal()`
* **Calls:** 9Router / Vyce AI API
* **Current status:** ONLINE (Đội 1 · Trực Chiến Khớp Lệnh)

---

## 3. Sơ Đồ Luồng Thực Tế Từ Thị Trường Đến Sàn Binance

```text
                     Thị Trường (Binance Futures)
                                  │
                                  ▼
                     BinanceWebSocketFeed (100ms)
                                  │
                                  ▼
                 EMATrendStrategy / RSIBollingerStrategy
                                  │ (SignalEvent: BUY/SELL, SL, TP)
                                  ▼
                      RiskManager.handle_signal()
                                  │
         ┌────────────────────────┴────────────────────────┐
         │ BƯỚC 1: HARD DETERMINISTIC GATES (0ms)          │
         │ - Circuit Breaker Tripped? (Loss > -$3.50)      │ ──[YES]──> REJECT & LOG
         │ - Max Positions >= 2?                           │ ──[YES]──> REJECT & LOG
         │ - Duplicate Symbol Exists?                      │ ──[YES]──> REJECT & LOG
         │ - Invalid SL Bounds?                            │ ──[YES]──> REJECT & LOG
         │ - Reverse MTF Trend?                            │ ──[YES]──> REJECT & LOG
         │ - Funding Squeeze Risk?                         │ ──[YES]──> REJECT & LOG
         └────────────────────────┬────────────────────────┘
                                  │ Passed Hard Gates
                                  ▼
        ┌──────────────────────────────────────────────────┐
        │ BƯỚC 2: ADVERSARIAL DEBATER (VAR 3 HIỆP)         │
        │ Hiệp 1: Phe Bò (Groq LPU 120B)                   │
        │ Hiệp 2: Phe Gấu (9Router SuperGrok 4.7)          │
        │ Hiệp 3: Trọng Tài (9Router cx/gpt-6-astra)       │
        └─────────────────────────┬────────────────────────┘
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
             [VETO / TIMEOUT]              [APPROVED]
                     │                         │
                     ▼                         ▼
            REJECT SIGNAL &           RiskManager Phase 3:
             TELEGRAM ALERT            Position Sizing Calc
                                               │
                                               ▼
                                      OrderEvent Emitted
                                               │
                                               ▼
                                  BinanceExecutor.handle_order()
                                               │
                                  ┌────────────┴────────────┐
                                  ▼                         ▼
                           Market Order Entry       Protective STOP_MARKET
                                  │                         │
                                  └────────────┬────────────┘
                                               │
                                               ▼
                                      Binance Futures API
```
