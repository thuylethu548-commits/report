# 06. DANH MỤC API & TÍCH HỢP HỆ THỐNG (API & INTEGRATIONS)

Tài liệu này hệ thống hóa toàn bộ các điểm kết nối tích hợp bên ngoài (External Integrations), bảng định tuyến mô hình AI (Model Router Table), và danh mục các REST API nội bộ.

---

## 1. Bảng Định Tuyến Mô Hình AI (Model Router Table)

Trích xuất trực tiếp từ mã nguồn thực tế tại `ai_advisory/vyce_client.py` và bảng SQLite `model_brain_benchmarks`:

| Nhà Cung Cấp (Provider) | Tên Mô Hình / Bí Danh (Model / Alias) | Mục Đích Thực Tế Trong Code (Purpose) | Loại Endpoint (Endpoint Type) | Timeout | Cơ Chế Thử Lại (Retry) | Mô Hình Dự Phòng (Fallback) | Độ Trễ Thực Tế (Avg Latency) | Số Token / Requests Đã Gọi | Nguồn Tính Chi Phí (Cost Calculation) | Trạng Thái Sức Khỏe (Health State) |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :---: | :---: | :--- | :---: |
| **9Router (Local Gateway)** | `cx/gpt-6-astra`<br>*(Alias: gpt-6, codex-astra)* | **Trọng Tài VAR Tối Cao (Hiệp 3)** & Tổng chỉ huy tác chiến | OpenAI Compatible REST (`http://localhost:20128/v1/chat/completions`) | 13.0s | Không thử lại cùng model | `gcli/grok-4.7` $\rightarrow$ `claude-sonnet-4-6` | 420ms - 1,450ms | 1,420 calls / 412k tokens | $0.00 / Free Pool (VPS Session Key) | **HEALTHY** (Online) |
| **9Router (Local Gateway)** | `gcli/grok-4.7`<br>*(Alias: grok, grok-4)* | **Phe Gấu Phản Biện (Hiệp 2)** & Trinh sát vĩ mô Hash | OpenAI Compatible REST (`http://localhost:20128/v1/chat/completions`) | 18.0s | 1 lần sang fallback | `qwen/qwen3.8-27b` | 650ms - 2,100ms | 980 calls / 285k tokens | $0.00 / Free Pool (Web Session Key) | **HEALTHY** (Online) |
| **9Router (Local Gateway)** | `cx/gpt-5.6-sol` / `cx/gpt-5.6-terra` | CVaR Sentinel, Funding Arbitrage & Post-Mortem | OpenAI Compatible REST (`http://localhost:20128/v1/chat/completions`) | 15.0s | Không | `openai/gpt-oss-120b` | 330ms - 890ms | 450 calls / 120k tokens | $0.00 / Free Pool | **HEALTHY** (Online) |
| **Groq LPU Cloud** | `openai/gpt-oss-120b`<br>*(Alias: groq)* | **Phe Bò Lập Luận (Hiệp 1)** & Phân tích động lượng siêu tốc | OpenAI Compatible REST (`https://api.groq.com/openai/v1/chat/completions`) | 13.0s | Xoay tua API Key pool | `cx/gpt-5.6-sol` | **78ms - 145ms** | 1,850 calls / 340k tokens | $0.15 / 1M prompt, $0.60 / 1M comp | **HEALTHY** (Online) |
| **Groq LPU Cloud** | `qwen/qwen3.8-27b`<br>*(Alias: groq-fast)* | Phản biện dự phòng cho Hiệp 2 & Đo lường biến động Volt | OpenAI Compatible REST (`https://api.groq.com/openai/v1/chat/completions`) | 5.0s | Xoay tua API Key pool | Logic toán tiền định | 65ms - 110ms | 310 calls / 65k tokens | $0.10 / 1M prompt, $0.30 / 1M comp | **HEALTHY** (Online) |
| **Vyce AI Gateway** | `claude-sonnet-4-6`<br>*(Alias: claude-3-5-sonnet)* | Cố vấn rủi ro cổ điển, Trọng tài dự phòng cấp 2 & Post-mortem | OpenAI Compatible REST (`https://vyceai.com/v1/chat/completions`) | 10.0s | Không | `deepseek-v4.1` $\rightarrow$ `quantitative-fallback` | 2,800ms - 3,400ms | 680 calls / 185k tokens | $3.00 / 1M prompt, $15.00 / 1M comp | **HEALTHY** (Online) |
| **Vyce AI Gateway** | `deepseek-v4.1` / `deepseek-v4-flash` | Phân loại Regime nhanh & Chat tương tác trên Antigravity Canvas | OpenAI Compatible REST (`https://vyceai.com/v1/chat/completions`) | 8.0s | Không | Heuristic Regime Rules | 850ms - 1,200ms | 420 calls / 95k tokens | $0.14 / 1M prompt, $0.28 / 1M comp | **HEALTHY** (Online) |
| **Google AI Studio** | `gemini-3.7-flash` / `gemini-3.8-flash` | Dự phòng trinh sát Tory & Quét tin tức vĩ mô | OpenAI Compatible REST (`https://generativelanguage.googleapis.com/v1beta/openai`) | 12.0s | Xoay tua Key Pool | `qwen/qwen3.8-27b` | 450ms - 720ms | 520 calls / 140k tokens | Miễn phí theo quota Google Key Pool | **HEALTHY** (Online) |
| **Cloudflare Workers AI** | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | Tác tử khớp lệnh Meme & Tối ưu hóa trượt giá | Cloudflare AI REST (`https://api.cloudflare.com/client/v4/accounts/.../ai/v1`) | 8.0s | Không | Python OMS Rules | 680ms - 950ms | 210 calls / 45k tokens | $0.00 / Cloudflare Free Tier | **HEALTHY** (Online) |
| **OpenRouter** | `nvidia/nemotron-3.5-lightning:free` | Dự phòng khẩn cấp tầng cuối cùng | OpenAI Compatible REST (`https://openrouter.ai/api/v1/chat/completions`) | 15.0s | Không | `quantitative-fallback` | 1,200ms - 1,800ms | 45 calls / 12k tokens | $0.00 / OpenRouter Free Tier | **HEALTHY** (Online) |

---

## 2. Các Tích Hợp Dịch Vụ Bên Ngoài (External Integrations)

### 2.1. Binance Futures & Spot (CCXT Async)
* **Loại kết nối:** REST API v2/v3 + WebSocket.
* **Quyền hạn API Key:** Đọc thông tin (Read), Giao dịch Futures (Futures Trading), Giao dịch Spot (Spot Trading). **Tuyệt đối KHÔNG cấp quyền rút tiền (Withdrawal Disabled).**
* **Xác thực:** HMAC-SHA256 qua API Key & Secret.

### 2.2. Telegram Bot API
* **Loại kết nối:** HTTPS REST API (`https://api.telegram.org/bot<TOKEN>/...`).
* **Phương thức gọi:**
  * `sendMessage`: Gửi cảnh báo lệnh, Veto, và báo cáo tuần tra định kỳ.
  * `sendDocument`: Tải trực tiếp file sao lưu nén SQLite (`trading_bot_TIMESTAMP.db.gz`).
  * `getUpdates`: Lắng nghe lệnh tương tác điều khiển từ Admin (`/status`, `/help`, câu hỏi tư vấn).

### 2.3. Google Drive / Google Sheets Live Sync
* **Cơ chế:** Đồng bộ cục bộ và ổ đĩa đám mây mount tại `G:/My Drive/Astra_Quant_Sheets/`.
* **Định dạng:** CSV sử dụng mã hóa UTF-8 BOM (`utf-8-sig`) giúp Excel và Google Drive hiển thị trọn vẹn dấu tiếng Việt.

### 2.4. Supabase Cloud Hybrid Database
* **Loại kết nối:** HTTPS PostgREST API (`https://ldtaziouuvmcwssqmggn.supabase.co/rest/v1/...`).
* **Chức năng:** Bản sao lưu viễn thám không đồng bộ của các bảng: `trades`, `signals`, `ai_advisory_logs`, `trading_lessons`, `macro_strategic_directives`.

---

## 3. Tổng Hợp 88 Điểm Cuối REST API Nội Bộ (Internal Endpoints)

Hệ thống FastAPI trên cổng 8386 cung cấp các nhóm API chính:

### 3.1. Nhóm Điều Khiển Vận Hành & Khẩn Cấp (System & Control)
* `GET  /api/v1/status`: Trạng thái tổng quan, chế độ giao dịch (LIVE/PAPER), PnL, vị thế mở.
* `POST /api/v1/kill`: **Kill-Switch khẩn cấp** - Hủy toàn bộ tiến trình, dừng nhận lệnh mới.
* `POST /api/v1/reset_circuit`: Đặt lại mạch ngắt Circuit Breaker sau khi Admin kiểm tra an toàn.
* `POST /api/v1/system/auto_trade`: Bật/Tắt công tắc giao dịch tự động Master Auto-Trade.
* `POST /api/v1/live/close_position`: Đóng cưỡng bức một vị thế Live theo `symbol`.
* `POST /api/v1/live/close_all`: Đóng toàn bộ các vị thế đang mở trên sàn Binance Futures.
* `POST /api/v1/live/unblock`: Gỡ bỏ trạng thái khóa lệnh `entries_blocked`.

### 3.2. Nhóm Dữ Liệu Thị Trường & Chiến Lược (Market & Data)
* `GET  /api/v1/candles`: Lấy chuỗi nến OHLCV thời gian thực từ Binance hoặc SQLite.
* `GET  /api/v1/market/depth`: Độ sâu sổ lệnh Orderbook (Bids/Asks) phục vụ tính toán trượt giá.
* `GET  /api/v1/signals`: Lịch sử các tín hiệu chiến lược kèm trạng thái Duyệt hoặc Veto.
* `GET  /api/v1/funding-rates`: Danh sách tỷ lệ Funding Rate thời gian thực của các cặp coin.

### 3.3. Nhóm Tác Tử AI & Đồng Thuận (Agent & Orchestration)
* `GET  /api/v1/fleet`: Báo cáo chỉ số và trạng thái hoạt động của hạm đội tác tử.
* `GET  /api/v1/fleets/dual_status`: Báo cáo phân tách 2 đội (Trực chiến HFT vs Tình báo 9Router).
* `GET  /api/v1/models/benchmark`: Bảng xếp hạng độ trễ và tỷ lệ thành công của các mô hình AI.
* `POST /api/v1/ai/debate/evaluate`: Kích hoạt phiên tranh luận đối kháng VAR 3 hiệp thử nghiệm.
* `GET  /api/v1/ai/quota`: Thống kê số lượng token tiêu thụ và chi phí ước tính của từng mô hình.
* `GET  /api/v1/orchestration/overview`: Tổng quan ma trận trọng số và quy tắc điều phối AI.

### 3.4. Nhóm Phân Tích & Báo Cáo Tài Chính (Analytics & Telemetry)
* `GET  /api/v1/analytics/trades_overview`: Đường cong tăng trưởng vốn (Equity Curve) và khối lượng.
* `GET  /api/v1/telemetry/pixel-floor`: Dữ liệu hoạt động và lời thoại tư duy cho Tầng Trade.
* `GET  /api/v1/telemetry/performance`: Bảng điểm hiệu năng, số vốn AI Veto bảo vệ được.
* `GET  /api/v1/trades/export/json`: Xuất toàn bộ dữ liệu lịch sử giao dịch ra file JSON.
* `GET  /api/v1/trades/export/csv`: Xuất toàn bộ dữ liệu lịch sử giao dịch ra file CSV.
* `GET  /api/v1/lessons`: Danh sách 40 bài học pháp y thị trường đúc kết trong cơ sở dữ liệu.

### 3.5. Nhóm Nghiên Cứu, Mô Phỏng & Sao Lưu (Simulation, Research & Backup)
* `POST /api/v1/simulation/run`: Kích hoạt vòng mô phỏng Monte Carlo gia tốc qua TimeWarp.
* `GET  /api/v1/simulation/oracle`: Dự phóng vĩ mô dài hạn từ Viện Tiên Tri Thị Trường.
* `POST /api/v1/admin/backup-telegram`: Kích hoạt tức thì quy trình tạo snapshot SQLite gửi về Telegram.
* `GET  /api/v1/data-lake/summary`: Thống kê dung lượng và danh mục phân vùng trong Parquet Data Lake.
* `GET  /api/v1/research/experiments`: Lịch sử các thực nghiệm định lượng trong Continuous Loop.
