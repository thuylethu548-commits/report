# 12. ẢNH CHỤP TRẠNG THÁI VẬN HÀNH THỜI GIAN THỰC (CURRENT RUNTIME SNAPSHOT)

**Thời điểm trích xuất:** 2026-09-23 20:30:00 (UTC+7)  
**Phương thức trích xuất:** **CHỈ ĐỌC (READ-ONLY)**. Tuyệt đối không can thiệp, không restart tiến trình, không đặt lệnh và không sửa đổi cơ sở dữ liệu.

---

## 1. Trạng Thái Các Tiến Trình Máy Chủ (PM2 Process Health)

| Process ID | Tên Tiến Trình | CPU | Bộ Nhớ RAM | Uptime | Restarts | Trạng Thái | Mô Tả Chức Năng |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **6** | `astra-quant` | 0% | 3.9 MB | 45m+ | 219 | **ONLINE** | Core Trading Bot + FastAPI Dashboard (Port 8386) |
| **0** | `op-web` | 0% | 29.3 MB | 4h+ | 245 | **ONLINE** | Next.js 16 Client Portal & Shop ACB (Port 3005) |
| **1** | `telegram-bot` | 0% | 49.6 MB | 19h+ | 8 | **ONLINE** | Telegram Long-Polling Bot (`@apicodex777_bot`) |
| **2** | `acb-poll` | 0% | 52.8 MB | 20h+ | 2 | **ONLINE** | Worker kiểm tra giao dịch VietQR ngân hàng ACB |
| **8** | `alpha-miner` | 0% | 3.5 MB | 20h+ | 2 | **ONLINE** | Daemon khai thác dữ liệu nến CoT đào tạo AI |
| **9** | `ai-spot-sniper` | 0% | 3.5 MB | 20h+ | 3 | **ONLINE** | Daemon gom hàng Spot DCA tự động |
| **10** | `koc-master` | 0% | 10.7 MB | 20h+ | 1 | **ONLINE** | Tự động hóa truyền thông YouTube / TikTok |
| **11** | `agent-nexus` | 0% | 3.5 MB | 20h+ | 1 | **ONLINE** | Dịch vụ vi mô Agent Nexus (Port 3100) |
| **Node**| `9router` | 0% | ~85 MB | 20h+ | 0 | **ONLINE** | Cổng AI Gateway Proxy cục bộ (Port 20128) |

---

## 2. Trạng Thái Vị Thế & Kết Nối Sàn Binance (Binance Futures State)

* **Chế độ giao dịch (Trading Mode):** **LIVE PRODUCTION** (`BINANCE_USE_TESTNET = False`).
* **Thị trường hoạt động:** Binance USDⓈ-M Futures.
* **Số lượng vị thế đang mở (Open Positions Count):** **ĐÚNG 1 VỊ THẾ DUY NHẤT (COUNT = 1)**.
* **Chi tiết vị thế hiện tại (Trích xuất từ `execution_state`):**
  * **Cặp giao dịch (Symbol):** `ETH/USDT`
  * **Chiều vị thế (Side):** **BÁN (SELL / SHORT)**
  * **Khối lượng (Quantity):** $0.009$ ETH (Tương đương giá trị danh nghĩa $\approx 24.5$ USDT)
  * **Giá vào lệnh trung bình (Entry Price):** $2,722.84 USDT
  * **Cắt lỗ bảo vệ trên sàn (Protected Stop Loss):** $2,771.8511 USDT (Lệnh `STOP_MARKET` ID: `3000002211769186`)
  * **Chốt lời mục tiêu (Take Profit):** $2,641.1548 USDT
  * **Thời gian mở lệnh:** `2026-09-23T12:15:48.383Z`
  * **Trạng thái Trailing Stop:** Đã kích hoạt theo dõi, giá đáy đã ghi nhận: $2,708.27 USDT.
* **Trạng thái chặn lệnh mới (`entries_blocked`):** `False` (Bình thường, không bị nghẽn).
* **Danh sách biểu tượng bất định (`uncertain_symbols`):** `[]` (Không có lệnh treo hoặc không rõ trạng thái).
* **Lệnh chờ xác nhận (`pending`):** `0` lệnh.

---

## 3. Trạng Thái Sức Khỏe Cơ Sở Dữ Liệu (Database Health)

* **Tệp cơ sở dữ liệu chính:** `c:\sunMy\trading_bot\trading_bot.db`.
* **Dung lượng tệp:** $\approx 1.16$ MB.
* **Chế độ Journal:** WAL (Write-Ahead Logging).
* **Tổng số bảng quản lý:** 23 bảng.
* **Số lượng bản ghi trọng yếu:**
  * Lịch sử nến (`candles`): **2,353** bản ghi.
  * Tín hiệu chiến lược (`signals`): **380** bản ghi.
  * Nhật ký tư vấn AI (`ai_advisory_logs`): **94** bản ghi.
  * Nhật ký tiêu hao token AI (`ai_token_usage`): **3,249** bản ghi.
  * Bài học thực chiến đúc kết (`trading_lessons`): **40** bài học.
  * Lệnh giao dịch đã ghi sổ (`trades`): **28** lệnh.
  * Chỉ thị chiến lược vĩ mô (`macro_strategic_directives`): **79** chỉ thị.
  * Điểm chuẩn kiểm thử mô hình (`model_brain_benchmarks`): **9** bản ghi.

---

## 4. Trạng Thái Kết Nối WebSocket & Lịch Trình Đối Soát (Feed & Reconciliation)

* **Binance WebSocket Feed:** **ĐANG KẾT NỐI (CONNECTED)**.
  * Luồng nhận gói tin: `wss://fstream.binance.com/ws`.
  * Cập nhật giá nến gần nhất: Khung thời gian `15m` cho 8 cặp tiền mã hóa chính.
* **Lịch trình đối soát số dư (Periodic Reconciliation Worker):**
  * Tần suất thực thi: Mỗi 20 giây.
  * Trạng thái đối soát gần nhất: **ĐỒNG BỘ HOÀN TOÀN (IN-SYNC)**.
  * Không phát hiện sai lệch vị thế giữa Binance REST API và bộ nhớ trong của bot.

---

## 5. Trạng Thái Sức Khỏe Các Cổng AI (AI Gateways Health)

* **9Router Gateway (`http://localhost:20128/v1`):** **ONLINE** (Phản hồi trong 337ms).
  * Danh mục mô hình sẵn sàng: 46 mô hình (`cx/gpt-6-astra`, `gcli/grok-4.7`, `cx/gpt-5.6-sol`, `gw/grok-4`...).
* **Groq LPU Cloud API (`https://api.groq.com/openai/v1`):** **ONLINE** (Phản hồi siêu tốc 65ms - 80ms).
* **Google Gemini API Pool:** **ONLINE** (Độ trễ trung bình 478ms).
* **Vyce AI Proxy Gateway (`https://vyceai.com/v1`):** **ONLINE** (Độ trễ 2,924ms).
* **Cloudflare Workers AI:** **ONLINE** (Độ trễ 697ms).
