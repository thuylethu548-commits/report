# 00. TỔNG QUAN HỆ THỐNG (EXECUTIVE SUMMARY)
**Dự án:** ASTRA QUANT DESK & THIÊN CƠ CÁC  
**Phiên bản hiện tại:** 3.0.0 (GPTHeist Autonomous Multi-Agent Protocol)  
**Ngày trích xuất:** 2026-09-23  
**Mục đích tài liệu:** Bàn giao kỹ thuật toàn diện (Technical Project Handoff Bundle) phục vụ Independent AI Architect Audit.  
**Nguyên tắc tài liệu:** Tuyệt đối không marketing, không tô hồng hệ thống, chỉ mô tả sự thật kỹ thuật (Technical Truth).

---

## 1. Mục Đích & Bản Chất Hệ Thống
ASTRA QUANT là một hệ thống giao dịch thuật toán định lượng (Quantitative Algorithmic Trading Desk) kết hợp mô hình đồng thuận đa tác tử trí tuệ nhân tạo (Multi-Agent LLM Consensus Council) và cổng kiểm soát rủi ro tiền định (Deterministic Risk Gatekeeper).

Hệ thống được thiết kế theo triết lý:
$$\text{Market Data} \longrightarrow \text{Quantitative Strategies} \longrightarrow \text{Multi-Agent VAR Debate} \longrightarrow \text{Deterministic Risk Gate} \longrightarrow \text{Exchange Execution (OMS)}$$

Hệ thống vận hành song song 2 cơ chế tài khoản:
1. **Futures Trading Desk (Vốn thử nghiệm 50.0 USDT):** Giao dịch hợp đồng tương lai vĩnh cửu (USDT-M Perpetual Futures) trên Binance với đòn bẩy $6x$, tìm kiếm lợi nhuận ngắn hạn theo các nhịp sóng M15.
2. **Spot Accumulation Engine (Vốn tích sản 500.0 USDT cấu hình, két vốn 450.0 USDT bảo vệ):** Gom các đồng coin nền tảng (BTC, ETH, SOL) theo phương pháp Smart DCA khi thị trường điều chỉnh sâu.

---

## 2. Tech Stack & Hạ Tầng Runtime
* **Hệ điều hành Máy chủ:** Windows Server VPS (x64).
* **Ngôn ngữ & Runtime Backend:**
  * Python 3.10.0 (32-bit root) / Python 3.12 (`.venv`).
  * Framework API: FastAPI 0.115+, Uvicorn (chạy bất đồng bộ qua asyncio event loop).
  * Thư viện kết nối sàn: CCXT (Async Support), Httpx, Aiofiles, Websockets.
  * Thư viện tính toán định lượng: Pandas, NumPy, SciPy, PyArrow (Apache Arrow Parquet), DuckDB.
* **Frontend:**
  * **Admin Desk / Cockpit Chính (Port 8386):** Render từ server qua Jinja2 Templates, Vanilla HTML5, Vanilla CSS3 (Dark Mode / Glassmorphism), Vanilla JavaScript ES6+, WebSockets song công và HTML5 Canvas.
  * **OpenPlatform / Portal Khách hàng (`C:\Users\Administrator\Desktop\op`, Port 3005):** Next.js 16.3.0, React 19, TypeScript, TailwindCSS.
* **Cơ sở dữ liệu (Database):**
  * **Primary Authoritative Source of Truth:** SQLite 3 (`trading_bot.db`), chế độ WAL (Write-Ahead Logging), quản lý toàn bộ vị thế, lệnh, số dư, bài học, và nhật ký AI.
  * **Data Lake Analytical Storage:** Apache Arrow Parquet partitioned files (`data/lake/parquet/`) và DuckDB phục vụ phân tích dữ liệu lớn.
  * **Cloud Sync Mirror:** Supabase PostgreSQL (`https://ldtaziouuvmcwssqmggn.supabase.co`).
* **Tiến trình nền (PM2 Process Management):**
  * `astra-quant` (PID 23560): Core Trading Bot + FastAPI Web Dashboard (port 8386).
  * `op-web` (PID 15380): Next.js Portal (port 3005).
  * `telegram-bot` (PID 23016): Long-polling Telegram Bot cho OpenPlatform (`@apicodex777_bot`).
  * `acb-poll` (PID 12448): Worker kiểm tra biến động số dư ngân hàng ACB qua VietQR.
  * `alpha-miner` (PID 8640): Worker chạy ngầm tổng hợp dữ liệu nến và khai thác CoT dataset.
  * `ai-spot-sniper` (PID 7064): Worker thực thi tích sản Spot tự động.
  * `koc-master` (PID 20680): Tự động hóa nội dung truyền thông.
  * `agent-nexus` (PID 20044): Microservice Agent Nexus (port 3100).
  * `9router` (PID 23060 - Node.js): Cổng AI Gateway Proxy cục bộ lắng nghe tại `http://localhost:20128/v1`.

---

## 3. Môi Trường Giao Dịch & Sàn Kết Nối
* **Môi trường Binance:** **LIVE PRODUCTION** (`BINANCE_USE_TESTNET = False`).
* **Thị trường giao dịch chính:** Binance USDT-Margined Futures (`fapiPrivate` / `fapiPublic`).
* **Thị trường phụ:** Binance Spot (`apiPrivate` / `apiPublic`).
* **Danh sách tài sản theo dõi:** `BTC/USDT`, `ETH/USDT`, `SOL/USDT`, `BNB/USDT`, `DOGE/USDT`, `1000PEPE/USDT`, `NEAR/USDT`, `SUI/USDT`.
* **Khung thời gian phân tích chính (Primary Timeframe):** 15 phút (`15m`), kết hợp bộ lọc đa khung thời gian MTF (`1h`, `4h`).
* **Số lượng vị thế mở tối đa:** 2 vị thế (`MAX_OPEN_POSITIONS = 2`).
* **Trạng thái vị thế hiện tại:** Đang có **1 vị thế LIVE** duy nhất: `ETH/USDT` vị thế BÁN (SHORT), Khối lượng 0.009 ETH, Giá vào lệnh: $2,722.84, Stop Loss: $2,771.85, Take Profit: $2,641.15.

---

## 4. Hội Đồng Tác Tử AI & Định Tuyến Mô Hình (Model Routing)
Hệ thống cấu hình 12 tác tử trong danh bạ `AutonomousFleetCoordinator`, phân thành 2 đội hình tác chiến:
1. **Đội 1 · Trực Chiến Khớp Lệnh (< 1.5s):**
   * **Palermo:** Trưởng Ban Xu Hướng (EMA-20/50, RSI-14). Model: `openai/gpt-oss-120b` (Groq LPU).
   * **Rik:** Cảnh Sát Rủi Ro (Circuit Breaker & Veto Gatekeeper). Model: `Claude-Sonnet-4-6` (Vyce AI) / `cx/gpt-6-astra`.
   * **Tory:** Săn Hàng Đột Phá (Donchian-20 Breakout). Model: `Gemini-3.7-Flash` / `cx/gpt-5.6-terra`.
   * **Meme:** Đội Khớp Lệnh & Tối ưu Trượt Giá. Model: `@cf/meta/llama-3.3-70b-instruct-fp8-fast` (Cloudflare).
   * **Volt:** Đo Lường Biến Động (ADX & Market Regime). Model: `qwen/qwen3.8-27b` (Groq).
   * **Astra:** Tổng Quản Tối Cao (Trọng Tài Chung Khảo). Model: `cx/gpt-6-astra` / `Claude-Sonnet-4-6`.
2. **Đội 2 · Tình Báo Vĩ Mô & Nghiên Cứu (9Router Pool):**
   * **Hash:** Trinh Sát Tin Tức & Tình Báo Vĩ Mô. Model: `gcli/grok-4.7` (SuperGrok CLI qua 9Router).
   * **Deck:** Săn Chênh Lệch Giá & Funding Arbitrage. Model: `cx/gpt-5.6-terra`.
   * **Prof:** Gác Cổng Thanh Lý & Quản Lý Ký Quỹ CVaR. Model: `cx/gpt-5.6-sol`.
   * **Core:** Pháp Y Lịch Sử, Tính Sharpe & Bài Học Post-Mortem. Model: `cx/gpt-5.6-terra`.
   * **Sniper:** Tích Sản Spot DCA & Két Vốn 450U. Model: `cx/gpt-5.6-sol`.
   * **Square:** Truyền Thông, Binance Square & Tăng Trưởng Ref. Model: `cx/gpt-5.6-luna`.

**Cơ chế Tranh Biện Đối Kháng VAR 3 Hiệp (`AdversarialDebater`):**
Mọi tín hiệu kỹ thuật trước khi khớp lệnh đều trải qua 3 hiệp tranh biện thực chất qua API LLM:
* **Hiệp 1 (Phe Bò Momentum):** `openai/gpt-oss-120b` (Groq LPU ~80ms) lập luận bảo vệ lệnh vào.
* **Hiệp 2 (Phe Gấu Devil's Advocate):** `gcli/grok-4.7` (SuperGrok) phản biện bóc tách bẫy thanh khoản và rủi ro đảo chiều.
* **Hiệp 3 (Trọng Tài VAR Tối Cao):** `cx/gpt-6-astra` (hoặc co-arbiter `gcli/grok-4.7`, fallback `Claude-Sonnet-4-6`) ra phán quyết tối hậu (`APPROVED` hoặc `VETOED`).

---

## 5. Dữ Liệu Thời Gian Thực & Lưu Trữ Đám Mây
* **Dữ liệu nến & tick:** Binance WebSocket Feed (`wss://fstream.binance.com/ws`) cập nhật giá 100ms - 1s, kết hợp REST API CCXT tự động nạp klines và độ sâu Orderbook.
* **Telegram Alerts & Database Backup:**
  * Thông báo tức thời khi mở/đóng lệnh, dời trailing stop, kích hoạt circuit breaker hoặc AI Veto.
  * Tự động sao lưu database SQLite online (`sqlite3.backup()`), nén gzip và gửi file `trading_bot_TIMESTAMP.db.gz` về Telegram Chat của Quản trị viên.
  * Lắng nghe lệnh tương tác thời gian thực từ Admin (`/status`, `/help`, câu hỏi tư vấn).
* **Google Drive / Google Sheets Live Sync:**
  * Duy trì các tệp bảng tính CSV (UTF-8 BOM) tại `G:/My Drive/Astra_Quant_Sheets/` (hoặc fallback `data/gdrive_sheets/`), ghi nhận trực tiếp các phiên tranh luận AI, lịch sử giao dịch và chỉ thị vĩ mô để hiển thị trên Excel/Google Sheets.

---

## 6. Phân Định: Thành Phần LIVE vs Thực Nghiệm (Experimental)
* **Thành phần ĐANG LIVE 100%:**
  * Sàn Binance Futures Live (`BinanceExecutor` với bảo vệ SL cứng, đòn bẩy $6x$, đồng bộ hóa vị thế định kỳ 20s).
  * Bộ máy kiểm soát rủi ro cứng (`RiskManager`, `CircuitBreaker` ngắt lệnh khi lỗ ngày quá -$3.50 hoặc sụt giảm 7%).
  * Chiến lược định lượng kỹ thuật: EMA Trend Continuation (`EMATrendStrategy`) và RSI Bollinger Mean Reversion (`RSIBollingerStrategy`).
  * Hội đồng tranh biện VAR 3 hiệp đối kháng thời gian thực (`AdversarialDebater`).
  * Hệ thống WebSocket kết nối sàn và Web Dashboard Cockpit.
* **Thành phần MOCK / PLACEHOLDER / THỰC NGHIỆM:**
  * **Handoff Chord & Tail Probability Ridge:** Đồ họa trên giao diện `quantum_cockpit.html` hiện tại chứa bảng số liệu tĩnh (hardcoded table) và canvas chưa liên kết hàm vẽ động.
  * **Chỉ số Sharpe/Sortino/Calmar trên Cockpit:** Hiện hiển thị các giá trị placeholder tĩnh (ví dụ: Sharpe 2.45, Sortino 3.12, Calmar 2.84), trong khi hệ thống tính toán thực thụ nằm ở API `/analytics/trades_overview` và hàm `get_agent_performance_scorecard()`.
  * **TimeWarp World Simulation (10,000x Speed):** Chạy giải thuật mô phỏng Monte Carlo trong bộ nhớ RAM, ghi nhận log vào Parquet Data Lake, **KHÔNG** tác động trực tiếp vào tham số giao dịch của tài khoản Live.
  * **5D Quantum Tensor Engine:** Mô hình tính điểm heuristic tổng hợp 5 chiều toán học, hiện đóng vai trò phân tích dữ liệu mở rộng, không nắm quyền bypass Risk Gate.
