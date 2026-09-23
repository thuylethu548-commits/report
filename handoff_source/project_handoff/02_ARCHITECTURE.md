# 02. KIẾN TRÚC BACKEND CHI TIẾT (BACKEND ARCHITECTURE)

Tài liệu này hệ thống hóa toàn bộ các phân hệ của ASTRA QUANT, chỉ định chính xác tệp nguồn (File), lớp (Class), hàm (Function), luồng dữ liệu (Inputs / Outputs) và quyền hạn can thiệp vào lệnh giao dịch.

---

## 1. Bản Đồ Tổng Thể Kiến Trúc (Architecture Topology)

Hệ thống được thiết kế theo kiến trúc **Hướng sự kiện phi đồng bộ (Asynchronous Event-Driven Architecture)**, sử dụng `core.event_bus.EventBus` làm trục giao tiếp trung tâm:

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           1. INGESTION & MARKET FEEDS                           │
│  - BinanceWebSocketFeed (wss://fstream.binance.com) -> MarketEvent              │
│  - MacroNewsScanner (CryptoCompare/RSS)             -> MacroEvent               │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ (Asyncio EventBus)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      2. ANALYTICAL & STRATEGY SIGNAL ENGINE                     │
│  - EMATrendStrategy       -> SignalEvent (BUY/SELL)                             │
│  - RSIBollingerStrategy   -> SignalEvent (BUY/SELL)                             │
│  - SpotDCAStrategy        -> SignalEvent (BUY)                                  │
│  - MultiTimeframeFilter   -> Confluence Validation                              │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ (SignalEvent)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      3. DETERMINISTIC RISK ENGINE (PHASE 1)                     │
│  - RiskManager.handle_signal()                                                  │
│    ├── CircuitBreaker.is_tripped           (Daily Loss > -$3.50 or Drawdown > 7%)│
│    ├── Position Cap Gate                   (Count >= MAX_OPEN_POSITIONS)        │
│    ├── Single Symbol Duplicate Gate        (1 position per symbol)              │
│    ├── Hard Stop-Loss Boundary Guard       (SL must be within 1.8%)             │
│    ├── FundingSentinel.evaluate_squeeze()  (Funding rate extremes)              │
│    └── MTFFilter.check_confluence()        (Multi-timeframe trend alignment)    │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Approved by Hard Gates
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 4. AI ADVISORY & ADVERSARIAL VAR COUNCIL (PHASE 2)              │
│  - AdversarialDebater.debate_signal()                                           │
│    ├── Round 1 (Bull Momentum):      Groq LPU (openai/gpt-oss-120b)             │
│    ├── Round 2 (Bear Skeptic):       9Router SuperGrok (gcli/grok-4.7)          │
│    └── Round 3 (Supreme Arbiter):    9Router OpenAI Codex Plus (cx/gpt-6-astra) │
│                                      Fallback: Claude-Sonnet-4-6 via Vyce AI    │
│    └── Output: {"approved": bool, "risk_score": 1-5, "size_multiplier": 0.2-1.0}│
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ AI APPROVE (or Timeout Safety Fallback)
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                 5. POSITION SIZING & ALLOCATION ENGINE (PHASE 3)                │
│  - Allocated USDT = (Current Equity * MAX_POSITION_PERCENT) * AI_Multiplier    │
│  - House Money Cap: If daily profit >= +$10.0, Size Multiplier <= 0.20x         │
│  - Hard Sizing Cap: min(Quantity, LIVE_MAX_USDT_PER_ORDER / Price)              │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Emits OrderEvent
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         6. EXECUTION & OMS (PHASE 4)                            │
│  - BinanceExecutor.handle_order()                                               │
│    ├── Idempotency Check (_submitted_ids deduplication)                         │
│    ├── Exchange Filter Alignment (ex.amount_to_precision, min_amount, min_cost) │
│    ├── Market Order Execution -> Binance Futures REST API                       │
│    ├── Protective Stop Order -> STOP_MARKET reduceOnly (Immediate)             │
│    └── TrailingStopManager -> Real-time Trailing SL & Break-Even Adjustment    │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Emits FillEvent
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   7. PERSISTENCE, MONITORING & TELEMETRY                        │
│  - SQLite 3 (trading_bot.db): trades, signals, ai_advisory_logs, execution_state │
│  - TelegramNotifier: Real-time Fill & Veto alerts, Online DB Backup             │
│  - DataLakeManager: Apache Arrow Parquet partitioned archive                    │
│  - SupabaseSyncService: Asynchronous PostgreSQL cloud mirror                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Bảng Phân Công Module Trách Nhiệm Chi Tiết

| Thành Phần | Tệp Nguồn (File) | Lớp (Class) / Hàm (Function) | Gọi Bởi (Called by) | Đầu Vào (Inputs) | Đầu Ra (Outputs) | Chặn Lệnh Được? (Can Block?) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **System Entrypoint** | `main.py` | `main()` | PM2 / CLI `python main.py` | CLI args, `.env`, SQLite settings | Vòng lặp asyncio vĩnh cửu | **YES** (Khởi tạo/Dừng bot) |
| **Event Dispatcher** | `core/event_bus.py` | `EventBus` | Toàn bộ các subsystem | Các đối tượng sự kiện kế thừa `Event` | Chuyển phát sự kiện tới các subscriber | **NO** (Trung chuyển thông điệp) |
| **WebSocket Feed** | `data/websocket_feed.py` | `BinanceWebSocketFeed` | `main.py` | WebSocket ticks từ Binance | Phát `MarketEvent` vào EventBus | **NO** (Thu thập dữ liệu) |
| **REST Exchange Client** | `data/binance_client.py` | `BinanceClient` | `BinanceExecutor`, `RiskManager` | CCXT request params | CCXT market responses, balances, orders | **NO** (Giao tiếp HTTP/REST) |
| **Strategy: EMA Trend** | `strategies/ema_trend.py` | `EMATrendStrategy.on_market()` | EventBus (`MarketEvent`) | `MarketEvent` (giá, nến 15m) | Phát `SignalEvent` (BUY/SELL) | **NO** (Sinh tín hiệu) |
| **Strategy: RSI Bollinger** | `strategies/rsi_bollinger.py` | `RSIBollingerStrategy.on_market()` | EventBus (`MarketEvent`) | `MarketEvent` (giá, nến 15m) | Phát `SignalEvent` (BUY/SELL) | **NO** (Sinh tín hiệu) |
| **Multi-Timeframe Filter** | `strategies/multi_timeframe.py` | `MultiTimeframeFilter.check_confluence()` | `RiskManager.handle_signal()` | Symbol, Price, Side, Klines H1/H4 | `{"approved": bool, "reason": str}` | **YES** (Veto nếu ngược trend lớn) |
| **Circuit Breaker** | `risk_engine/circuit_breaker.py` | `CircuitBreaker.check_drawdown()` | `RiskManager`, `main.py` | Realized PnL ngày, Current Equity | `is_tripped: bool`, `trip_reason` | **YES** (Khóa chặt mọi lệnh mới) |
| **Funding Sentinel** | `risk_engine/funding_sentinel.py` | `FundingSentinel.evaluate_squeeze_risk()` | `RiskManager.handle_signal()` | Symbol, Side | `{"safe": bool, "reason": str}` | **YES** (Veto nếu dính squeeze) |
| **Deterministic Risk Gate** | `risk_engine/risk_manager.py` | `RiskManager.handle_signal()` | EventBus (`SignalEvent`) | `SignalEvent`, Market Context | Phát `OrderEvent` hoặc Reject Log | **YES** (Cổng kiểm soát sinh tử) |
| **AI Smart Router** | `ai_advisory/vyce_client.py` | `VyceClient.chat_completion()` | `AdversarialDebater`, `RiskManager` | Prompt, Model Alias, Timeout | Chuỗi JSON phản hồi từ LLM | **NO** (Cung cấp suy luận) |
| **VAR Council Debate** | `ai_advisory/adversarial_debater.py` | `AdversarialDebater.debate_signal()` | `RiskManager.handle_signal()` | `SignalEvent`, Technical Context | `{"approved": bool, "risk_score": int...}` | **YES** (Trọng tài có quyền Veto) |
| **Market Regime Detector** | `ai_advisory/regime_classifier.py` | `MarketRegimeClassifier.classify()` | EventBus (`MarketEvent`) | Chuỗi nến OHLCV gần nhất | Cập nhật MarketRegime trong DB | **YES** (Veto nếu Extreme Volatility) |
| **Execution OMS** | `execution/binance_executor.py` | `BinanceExecutor.handle_order()` | EventBus (`OrderEvent`) | `OrderEvent` (Approved Order) | Lệnh Market + Protective Stop Loss | **YES** (Chặn nếu vi phạm sàn/lệch SL) |
| **Trailing Stop & BE** | `execution/trailing_stop.py` | `TrailingStopManager.update()` | EventBus (`MarketEvent`) | Market Price, Active Positions | Cập nhật Stop Loss bám đỉnh lãi | **NO** (Bảo vệ lợi nhuận) |
| **State Reconciliation** | `execution/binance_executor.py` | `BinanceExecutor.sync_open_positions()` | Worker định kỳ (20s) | Binance REST `/fapi/v2/positionRisk` | Đồng bộ hóa `self.open_positions` & DB | **YES** (Khóa lệnh nếu phát hiện lệch) |
| **Database Persistence** | `data/storage.py` | `Database` (SQLite3 Async) | Toàn bộ các subsystem | SQL Queries, Dataclass instances | Lưu trữ ACID, truy vấn thống kê | **NO** (Lưu trữ trạng thái) |
| **Telegram Alert & Backup** | `monitoring/telegram_bot.py` | `TelegramNotifier` | EventBus, API Routes, Schedulers | Events, `trading_bot.db` path | Tin nhắn Telegram, tệp nén `.db.gz` | **NO** (Cảnh báo & Sao lưu) |
| **FastAPI Web Server** | `web/app.py` | `create_web_app()` | `main.py` (`uvicorn.Server`) | HTTP Requests, WebSocket connections | Giao diện HTML, REST JSON responses | **YES** (Nút dừng khẩn cấp Kill-Switch) |
| **Data Lake Big Data** | `data/data_lake_manager.py` | `DataLakeManager` | APIs, TimeWarp, Scripts | DataFrames, Tabular records | Tệp Parquet Snappy nén phân vùng | **NO** (Lưu trữ phân tích) |
| **Supabase Cloud Sync** | `data/supabase_sync.py` | `SupabaseSyncService` | Worker định kỳ / API trigger | SQLite table rows | REST API Sync lên Supabase PG | **NO** (Đồng bộ đám mây) |
| **TimeWarp Simulation** | `core/hyper_simulation_world.py` | `TimeWarpEngine.run_simulation()` | API `/simulation/run`, Scripts | Scenario branches, Regime weights | Báo cáo thống kê Monte Carlo RAM | **NO** (Mô phỏng độc lập) |
| **5D Tensor Engine** | `core/quantum_5d_engine.py` | `Quantum5DTensorEngine.evaluate()`| API `/quantum/5d_tensor/evaluate` | 5 chiều vector thị trường | Điểm Tensor Confluence 0-100 | **NO** (Phân tích chỉ số hỗ trợ) |

---

## 3. Phân Tích Kỹ Thuật Các Subsystem Trọng Yếu

### 3.1. RiskGate (Cổng Kiểm Soát Rủi Ro Tiền Định)
* **File:** `risk_engine/risk_manager.py`
* **Class:** `RiskManager`
* **Called by:** `core.event_bus.EventBus` khi có `SignalEvent`.
* **Inputs:** Đối tượng `SignalEvent` (symbol, side, price, stop_loss, take_profit, strategy_name), nến gần nhất từ database, nhật ký bài học `trading_lessons`.
* **Outputs:** Nếu duyệt: phát `OrderEvent` với khối lượng đã tính toán. Nếu từ chối: ghi nhận lý do vào bảng `signals` (`approved = 0`, `rejection_reason = ...`) và phát cảnh báo Telegram.
* **Can block order?:** **YES (Tuyệt đối)**.
* **Các chốt chặn kiểm tra tiền định (0ms execution):**
  1. *Master Switch Check:* Kiểm tra cờ `settings.AUTO_TRADE_ENABLED`. Nếu tắt, lập tức hủy lệnh.
  2. *Funding Sentinel Check:* Kiểm tra tỷ lệ funding rate trên sàn Binance. Nếu funding âm/dương quá ngưỡng có nguy cơ Funding Squeeze, chặn lệnh ngay.
  3. *Circuit Breaker Check:* Kiểm tra trạng thái sụt giảm vốn trong ngày. Nếu đã chạm ngưỡng lỗ -$3.50 hoặc sụt giảm 7%, lập tức ngắt mạch.
  4. *Daily Profit Lock & House Money:* Nếu đã đạt mục tiêu +$10.00/ngày, hệ thống chuyển sang chế độ House Money (giảm tỷ trọng lệnh xuống tối đa 0.20x vốn).
  5. *Max Open Positions Check:* Nếu số vị thế đang mở $\ge$ `settings.MAX_OPEN_POSITIONS` (hiện tại = 2), từ chối vào thêm vị thế mới.
  6. *Single Position Per Symbol Gate:* Khóa cứng 1 vị thế duy nhất trên 1 đồng coin (`MAX_POSITIONS_PER_SYMBOL = 1`). Không cho phép nhồi lệnh cùng chiều hay mở lệnh đối ứng tạo rủi ro chéo.
  7. *Mandatory Stop Loss Check:* Lệnh BUY bắt buộc phải có $0 < \text{SL} < \text{Price}$. Lệnh SELL bắt buộc phải có $\text{SL} > \text{Price}$.
  8. *Multi-Timeframe Trend Confluence:* Kiểm tra EMA-20/50 trên khung 1h và 4h. Nếu tín hiệu M15 đánh ngược xu hướng chủ đạo của khung lớn, lệnh bị Veto.

### 3.2. Order Management System (OMS) & Binance Executor
* **File:** `execution/binance_executor.py`
* **Class:** `BinanceExecutor`
* **Called by:** `core.event_bus.EventBus` khi nhận `OrderEvent` từ `RiskManager`.
* **Inputs:** `OrderEvent` (order_id, symbol, side, order_type, quantity, price, stop_loss, take_profit).
* **Outputs:** 
  1. Lệnh Market Entry gửi lên Binance Futures.
  2. Lệnh `STOP_MARKET` bảo vệ vị thế với tham số `{"reduceOnly": True, "workingType": "MARK_PRICE"}`.
  3. Phát `FillEvent` cập nhật trạng thái hệ thống.
* **Can block order?:** **YES**.
* **Các cơ chế an toàn cấp khớp lệnh:**
  * *Idempotency Protection:* Quản lý tập hợp `_submitted_ids`. Nếu order_id đã từng được gửi, từ chối xử lý lại để loại trừ 100% rủi ro Double Execution do mạng lag.
  * *Uncertain Symbols Barrier:* Nếu một yêu cầu đặt lệnh bị timeout hoặc mất kết nối HTTP giữa chừng, biểu tượng đó lập tức bị đưa vào danh sách `_uncertain_symbols` và kích hoạt `entries_blocked = True`. Toàn bộ các lệnh vào mới bị đình chỉ cho đến khi tiến trình đối soát (Reconciliation) xác nhận trạng thái thực tế trên sàn.
  * *Exchange Precision Alignment:* Gọi hàm `exchange.amount_to_precision()` và kiểm tra giới hạn `limits.amount.min`, `limits.cost.min` của sàn Binance trước khi gửi lệnh. Tuyệt đối không tự động làm tròn lên vượt quá hạn mức rủi ro.

### 3.3. Circuit Breaker (Bộ Ngắt Mạch Khẩn Cấp)
* **File:** `risk_engine/circuit_breaker.py`
* **Class:** `CircuitBreaker`
* **Called by:** `RiskManager.handle_signal()`, `BinanceExecutor`, và API endpoints.
* **Inputs:** PnL thực nhận từ các lệnh đã đóng (`add_realized_pnl`), số dư ký quỹ thời gian thực.
* **Outputs:** Trạng thái `is_tripped (True/False)`, `trip_reason (str)`, `daily_realized_pnl (float)`.
* **Can block order?:** **YES**.
* **Nguyên tắc ngắt mạch:**
  * Ngưỡng lỗ tối đa ngày: `MAX_DAILY_LOSS_USD = 3.50 USDT`.
  * Ngưỡng sụt giảm tỷ lệ tối đa: `DAILY_MAX_DRAWDOWN_PERCENT = 0.07` (7% vốn bắt đầu ngày).
  * Khi chạm một trong hai ngưỡng trên, mạch ngắt lập tức kích hoạt, cấm mở bất kỳ vị thế mới nào cho đến khi qua ngày mới (00:00 UTC) hoặc có sự can thiệp thủ công từ Quản trị viên (`POST /api/v1/reset_circuit`).
