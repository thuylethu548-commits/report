# 08. TRIỂN KHAI & HẠ TẦNG VẬN HÀNH (DEPLOYMENT & INFRASTRUCTURE)

Tài liệu này đặc tả chi tiết môi trường máy chủ, cấu hình bộ quản lý tiến trình PM2, quy hoạch cổng mạng, danh mục biến môi trường (chỉ liệt kê tên biến, không tiết lộ giá trị), và chính sách sao lưu phục hồi.

---

## 1. Môi Trường Máy Chủ & Runtime (Runtime Environment)

* **Hệ điều hành:** Windows Server (NT 10.0; Win64; x64).
* **Phiên bản Python:**
  * System Global: Python 3.10.0 (32-bit Intel).
  * Project Virtualenv: Python 3.12 (đặt tại `c:\sunMy\trading_bot\.venv`).
* **Phiên bản Node.js:** v24.13.1.
* **Bộ quản lý tiến trình (Process Manager):** PM2 v5.4.3 (Node.js Global CLI).
* **Thư mục dự án chính:** `c:\sunMy\trading_bot`.
* **Thư mục ứng dụng phụ trợ:**
  * OpenPlatform Next.js Web: `C:\Users\Administrator\Desktop\op`.
  * Agent Nexus Microservice: `C:\sunMy\agent_nexus`.
  * Media KOC Master: `C:\Users\Administrator\Desktop\ytb`.

---

## 2. Danh Mục Các Tiến Trình PM2 Đang Vận Hành (PM2 Processes)

Trích xuất trực tiếp từ lệnh kiểm tra `pm2 jlist` trên máy chủ:

| ID | Tên Tiến Trình (Name) | Phiên Bản | Chế Độ | PID | Thời Gian Chạy (Uptime) | Số Lần Restart | Trạng Thái | Đường Dẫn Thực Thi (Exec Path) | Thư Mục Làm Việc (Cwd) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **6** | `astra-quant` | N/A | Fork | 23560 | 45m+ | 219 | **ONLINE** | `C:\sunMy\trading_bot\main.py` | `C:\sunMy\trading_bot` |
| **0** | `op-web` | 16.3.0 | Fork | 15380 | 4h+ | 245 | **ONLINE** | `...\Desktop\op\node_modules\next\dist\bin\next` (args: `dev -p 3005 -H 0.0.0.0`) | `C:\Users\Administrator\Desktop\op` |
| **1** | `telegram-bot` | 0.1.0 | Fork | 23016 | 19h+ | 8 | **ONLINE** | `C:\Users\Administrator\Desktop\op\scripts\start_bot.mjs` | `C:\Users\Administrator\Desktop\op` |
| **2** | `acb-poll` | 0.1.0 | Fork | 12448 | 20h+ | 2 | **ONLINE** | `C:\Users\Administrator\Desktop\op\scripts\acb_poll_worker.mjs` | `C:\Users\Administrator\Desktop\op` |
| **8** | `alpha-miner` | N/A | Fork | 8640 | 20h+ | 2 | **ONLINE** | `C:\sunMy\trading_bot\scripts\miner_daemon.py` | `C:\sunMy\trading_bot` |
| **9** | `ai-spot-sniper` | N/A | Fork | 7064 | 20h+ | 3 | **ONLINE** | `c:\sunMy\trading_bot\scripts\ai_spot_sniper.py` | `C:\sunMy\trading_bot` |
| **10** | `koc-master` | N/A | Fork | 20680 | 20h+ | 1 | **ONLINE** | `C:\Users\Administrator\Desktop\ytb\scripts\full_day_autonomous_master.py` | `C:\Users\Administrator\Desktop\ytb` |
| **11** | `agent-nexus` | N/A | Fork | 20044 | 20h+ | 1 | **ONLINE** | `C:\sunMy\agent_nexus\run.py` | `C:\sunMy\agent_nexus` |
| **Svc** | `9router` | N/A | Node | 23060 | 20h+ | 0 | **ONLINE** | `C:\Program Files\nodejs\node_modules\9router\app\custom-server.js` | `C:\Program Files\nodejs` |

---

## 3. Bản Đồ Cổng Dịch Vụ Mạng (Port Allocation)

```text
Port 8386 (0.0.0.0:8386) ──> [astra-quant] FastAPI Web Dashboard, REST API & WebSockets
Port 3005 (0.0.0.0:3005) ──> [op-web] Next.js 16 Client Portal & Shop ACB Payment
Port 20128 (0.0.0.0:20128) ─> [9router] Local AI Gateway Proxy (OpenAI Codex, Grok, Claude)
Port 3100 (0.0.0.0:3100) ──> [agent-nexus] Uvicorn Agent Nexus Microservice
```

* **Domain & Reverse Proxy:**
  * Tên miền nội bộ / đại diện: `trader.hoanvi.com`.
  * Quản trị SSL & DNS: Định tuyến trực tiếp hoặc qua Cloudflare Tunnel / Nginx reverse proxy trỏ về cổng 8386 và 3005.

---

## 4. Danh Mục Biến Môi Trường (Environment Variable Names ONLY)

> [!IMPORTANT]
> Toàn bộ giá trị nhạy cảm (API Keys, Passwords, Secrets, Tokens) đã bị loại bỏ theo tiêu chuẩn an toàn thông tin ISO/IEC 27001. Dưới đây chỉ kê khai **TÊN BIẾN** phục vụ cấu hình môi trường mới:

```text
# VẬN HÀNH & CHẾ ĐỘ GIAO DỊCH
TRADING_MODE
MARKET_TYPE
BINANCE_USE_TESTNET
SYMBOL
SYMBOLS
TIMEFRAME
STARTING_BALANCE_USDT
SPOT_STARTING_BALANCE_USDT
ENABLE_SPOT_ENGINE
LIVE_MAX_USDT_PER_ORDER
MAX_POSITION_PERCENT
DAILY_MAX_DRAWDOWN_PERCENT
MAX_DAILY_LOSS_USD
TARGET_DAILY_PROFIT_USD
HOUSE_MONEY_MODE_ENABLED
STOP_LOSS_PERCENT
TAKE_PROFIT_PERCENT
MAX_OPEN_POSITIONS
FUTURES_LEVERAGE
LIVE_SAFETY_RELEASE_APPROVED

# KẾT NỐI SÀN BINANCE
BINANCE_API_KEY
BINANCE_API_SECRET

# HỘI ĐỒNG AI & GATEWAYS
ENABLE_AI_ADVISORY
AI_COUNCIL_MODE
AI_TIMEOUT_SECONDS
AI_FAST_TIMEOUT_SECONDS
AI_PRIMARY_MODEL
VYCE_API_KEY
VYCE_BASE_URL
VYCE_MODEL
VYCE_FAST_MODEL
ETFBIT_API_KEY
ETFBIT_BASE_URL
ETFBIT_MODEL_SUPREME
ETFBIT_MODEL_SENTIMENT
ETFBIT_MODEL_FAST
GEMINI_API_KEY
GEMINI_API_KEYS
GEMINI_PROJECT_NAME
GEMINI_PROJECT_NUMBER
GEMINI_MODEL
CLOUDFLARE_AI_TOKEN
CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_MODEL
GROQ_API_KEY
GROQ_API_KEYS
GROQ_BASE_URL
GROQ_MODEL
NINEROUTER_API_KEY
NINEROUTER_BASE_URL
OPENROUTER_API_KEY
OPENROUTER_BASE_URL
OPENROUTER_MODEL
DEEPSEEK_API_KEY
CEREBRAS_API_KEY
SAMBANOVA_API_KEY

# THÔNG BÁO & CẢNH BÁO TELEGRAM
ENABLE_TELEGRAM
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID

# CỔNG WEB DASHBOARD
DASHBOARD_HOST
DASHBOARD_PORT
ADMIN_PASSWORD

# SUPABASE CLOUD SYNC
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_PUBLISHABLE_KEY
SUPABASE_SECRET_KEY
SUPABASE_PAT
SUPABASE_DB_HOST
SUPABASE_DB_PORT
SUPABASE_DB_USER
SUPABASE_DB_PASSWORD
SUPABASE_DB_NAME
SUPABASE_DATABASE_URL

# XÁC THỰC GOOGLE OAUTH & EMAIL SMTP
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASSWORD
```

---

## 5. Quy Trình Sao Lưu Dữ Liệu & Phục Hồi Thảm Họa (Backup & Recovery)

### 5.1. Cơ Chế Sao Lưu Trực Tuyến Nguyên Tử (Atomic SQLite Online Backup)
* **Kịch bản thực thi:** `scripts/backup_to_telegram.py` và phương thức `TelegramNotifier.backup_database_to_telegram()`.
* **Cơ chế kỹ thuật:** Sử dụng API `sqlite3.connect.backup()` của chuẩn SQLite. Phương thức này tạo snapshot bộ nhớ nhất quán ngay cả khi hệ thống đang ghi nhận lệnh giao dịch đồng thời (Zero-Lock Write).
* **Đóng gói & Nén:** File snapshot `.db` được nén chặt qua thuật toán Gzip (`.db.gz`), đặt tên theo định dạng chuẩn ISO: `trading_bot_YYYYMMDD_HHMMSS.db.gz`.
* **Kênh lưu trữ phân tán:**
  1. Thư mục cục bộ an toàn: `data/backups/`.
  2. Kênh Telegram riêng tư của Admin qua API `sendDocument`.
  3. Bảng tính Google Drive CSV qua `gdrive_sheets_sync.py`.

### 5.2. Chính Sách Tự Động Khởi Động Lại (Restart Policy)
* Tất cả tiến trình chạy dưới PM2 được cấu hình cờ tự phục hồi (Automatic Crash Recovery). Khi gặp sự cố sập nguồn hoặc lỗi biệt lệ không bắt được, PM2 tự động khởi chạy lại tiến trình trong vòng 1,000ms.
* Khi `astra-quant` khởi động lại:
  1. `BinanceExecutor._restore()` đọc ngay bản ghi tại bảng `execution_state`.
  2. Tái tạo danh sách vị thế đang mở và lệnh Stop Loss bảo vệ.
  3. Khởi động worker `sync_open_positions()` gọi trực tiếp Binance REST API để xác nhận số dư thực tế trước khi chấp thuận bất kỳ tín hiệu mới nào.
