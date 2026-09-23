# 10. ĐÁNH GIÁ NỢ CÔNG NGHỆ & RỦI RO KỸ THUẬT (RISKS & TECH DEBT AUDIT)

Báo cáo kiểm toán kỹ thuật độc lập, phân loại nghiêm ngặt các rủi ro, nợ công nghệ (Tech Debt), code rác và điểm nghẽn kiến trúc theo 4 mức độ: **CRITICAL**, **HIGH**, **MEDIUM**, **LOW**.

---

## 1. Mức Độ Khẩn Nguy (CRITICAL SEVERITY)

### 1.1. Khóa Ghi Đồng Thời Trên Cơ Sở Dữ Liệu SQLite (SQLite Concurrency Write Locks)
* **Vị trí ảnh hưởng:** `data/storage.py`, `trading_bot.db`.
* **Hiện tượng:** Có ít nhất 3 tiến trình PM2 độc lập truy cập vào cùng tệp SQLite `trading_bot.db`:
  1. `astra-quant` (PID 23560): Ghi nhận nến, vị thế, phán quyết AI và cập nhật PnL.
  2. `alpha-miner` (PID 8640): Chạy ngầm 24/7 ghi nhận `ai_token_usage` mỗi 60 giây.
  3. `ai-spot-sniper` (PID 7064): Đọc ghi lịch sử giao dịch Spot.
* **Hậu quả:** Mặc dù đã bật chế độ WAL, khi có xung đột ghi đồng thời ở thời điểm thị trường biến động dữ dội, hệ thống có thể ném ra biệt lệ `sqlite3.OperationalError: database is locked`, dẫn đến việc không thể lưu trạng thái lệnh Stop Loss hoặc bỏ lỡ cập nhật vị thế quan trọng.
* **Khuyến nghị kiến trúc:** Tách bảng ghi log tần suất cao (`ai_token_usage`, `candles`) ra cơ sở dữ liệu riêng, hoặc chuyển đổi Primary DB sang PostgreSQL.

### 1.2. Khóa Cứng Khóa Bí Mật Mặc Định Trong Mã Nguồn (Hardcoded API Keys in Source Code)
* **Vị trí phát hiện:** `ai_advisory/vyce_client.py` (dòng 14, 16, 293, 311, 322).
* **Chi tiết kỹ thuật:**
  * `NINEROUTER_API_KEY`: Chuỗi key mặc định đặt sẵn trong `getattr(settings, "NINEROUTER_API_KEY", "sk-91e75...")`.
  * `ETFBIT_API_KEY`: Chuỗi key đặt sẵn trong `getattr(settings, "ETFBIT_API_KEY", "sk-8bmkh...")`.
  * `OPENROUTER_API_KEY`: Chuỗi key đặt sẵn trong code.
  * `GUROUTER_API_KEY`: Chuỗi key đặt sẵn trong code.
* **Hậu quả:** Rủi ro an ninh mạng nghiêm trọng nếu mã nguồn bị lộ hoặc chia sẻ ra bên ngoài.
* **Khuyến nghị:** Toàn bộ khóa API phải được nạp 100% từ biến môi trường `.env`, xóa bỏ triệt để các chuỗi fallback key cứng trong code.

### 1.3. Nghẽn Thời Gian Thực Khi Cổng Proxy 9Router Cục Bộ Gặp Sự Cố
* **Vị trí:** `ai_advisory/adversarial_debater.py` (dòng 106-126, 171-180).
* **Hiện tượng:** Khi tiến trình Node.js của 9Router (cổng 20128) bị quá tải hoặc phiên đăng nhập hết hạn:
  * Hiệp 2 (Grok 4.7) sẽ treo tối đa **18.0 giây**.
  * Hiệp 3 (GPT-6-Astra) sẽ treo tối đa **13.0 giây**.
  * Tổng thời gian nghẽn có thể lên tới **31 - 35 giây**.
* **Hậu quả:** Trong khung thời gian M15, độ trễ 35 giây là quá lớn; giá thị trường có thể đã chạy mất 0.5% - 1.2%, biến một setup đẹp thành điểm vào lệnh bất lợi.

---

## 2. Mức Độ Cao (HIGH SEVERITY)

### 2.1. Số Liệu Giả Lập / Mock Data Đội Lốt Chỉ Số Live Trên Giao Diện Web
* **Vị trí:** `web/templates/admin/quantum_cockpit.html`.
* **Chi tiết kỹ thuật:**
  * **Sortino & Calmar Ratio:** Thẻ `<span id="qa-val-sortino">3.12</span>` và `<span id="qa-val-calmar">2.84</span>` là giá trị HTML tĩnh (hardcoded), không có bất kỳ hàm JavaScript nào cập nhật động từ database.
  * **Bảng Chuyển Giao Lệnh (Top Flows / Handoff Chord):** Bảng số liệu Prof $\rightarrow$ Astra (342 lần, 0.91, +2.8%) được viết cứng trong mã HTML `<tbody>`.
  * **Thẻ Canvas `chordCanvas`:** Chỉ khai báo thẻ HTML trống, hoàn toàn không có mã nguồn JavaScript vẽ biểu đồ dây (Chord Diagram).
  * **Nút bấm `switchRidgeTf`:** Gắn sự kiện `onclick="switchRidgeTf('1D', this)"` nhưng hàm này **không tồn tại** trong file script, gây lỗi ReferenceError ngầm trong console trình duyệt.
* **Hậu quả:** Gây hiểu lầm nghiêm trọng cho người vận hành về hiệu suất thực tế của hệ thống.

### 2.2. Dung Lượng Tệp Giao Diện & Tuyến API Quá Khổng Lồ (Monolithic Code Bloat)
* **Vị trí:**
  * `web/routes/api_routes.py`: Dung lượng **131,249 bytes** (chứa 88 endpoints trong 1 tệp duy nhất!).
  * `web/templates/admin/pixel_floor.html`: Dung lượng **202,628 bytes** (chứa toàn bộ CSS, HTML và JS inline hơn 3,700 dòng).
  * `web/templates/admin/ai_orchestration.html`: Dung lượng **127,109 bytes**.
  * `web/templates/admin/quantum_cockpit.html`: Dung lượng **120,566 bytes**.
* **Hậu quả:** Vi phạm nghiêm trọng nguyên tắc phân tách trách nhiệm (Separation of Concerns), cực kỳ khó bảo trì, dễ phát sinh xung đột mã và làm chậm tốc độ render.

### 2.3. Nuốt Biệt Lệ Ngầm (Silent Exception Swallowing)
* **Vị trí:** Xuất hiện phổ biến trong `data/storage.py`, `monitoring/department_telemetry.py`, và `execution/binance_executor.py` (`except Exception: pass` hoặc `except Exception as e: logger.debug(...)`).
* **Hậu quả:** Khi một truy vấn database hoặc tính toán PnL bị lỗi, hệ thống âm thầm bỏ qua mà không ném cảnh báo cấp cao (CRITICAL/ERROR), khiến lỗi tích tụ âm thầm mà quản trị viên không hề hay biết.

---

## 3. Mức Độ Trung Bình (MEDIUM SEVERITY)

### 3.1. Các Module Mã Nguồn Rời Rạc Không Được Đấu Nối Vào Vòng Lặp Chính (Dead / Unwired Code)
* **`execution/mission_farmer.py` (181 dòng):** Được viết để cày nhiệm vụ khối lượng giao dịch cho Binance (Zero-Fee Convert, Simple Earn, Volume Farming), nhưng hoàn toàn không được import hay khởi chạy trong `main.py` hay bất kỳ cronjob nào.
* **`core/hyper_simulation_world.py` (TimeWarp Engine):** Mô phỏng 100,000 kịch bản thị trường và tiến hóa tham số tác tử (`_evolve_parameters`), nhưng các tham số này chỉ nằm trong bộ nhớ RAM của lớp `VirtualAgent`, **hoàn toàn không được nạp ngược lại** vào tham số giao dịch thực tế của `RiskManager` hay `strategies`.

### 3.2. Bất Nhất Trong Số Liệu Tính Toán Vốn Cơ Sở (Capital Base Inconsistency)
* Tại `data/storage.py` (hàm `get_trades_analytics`): Số vốn cơ sở được gán cứng là `base_capital = 31.94 USDT`.
* Trong khi tại `config/settings.py` và bảng `system_settings`: Số vốn khởi điểm được cấu hình là `STARTING_BALANCE_USDT = 55.0 USDT` (hoặc 55.43 USDT).
* **Hậu quả:** Biểu đồ tăng trưởng vốn trên Master Chart tính toán tỷ lệ % tăng trưởng bị lệch pha so với số dư thực tế trên sàn.

### 3.3. Trùng Lặp Logic Định Tuyến AI (Duplicated Routing Logic)
* Logic giải mã alias mô hình (`MODEL_ALIASES`) và lựa chọn provider xuất hiện trùng lặp giữa `ai_advisory/vyce_client.py` và các thiết lập trong `ai_advisory/adversarial_debater.py`, gây khó khăn khi cần bổ sung hoặc thay thế một nhà cung cấp LLM mới.

---

## 4. Mức Độ Thấp (LOW SEVERITY)

### 4.1. Tồn Đọng Các Tệp Sao Lưu Rác Trong Mã Nguồn (Backup Clutter)
* Các file `.bak`: `performance.html.bak_tabs` (73KB), `pixel_floor.html.bak_master` (57KB), `settings.html.bak_dual_pages` (106KB), `home.html.bak_audit` (27KB).
* Cần được dọn dẹp và quản lý lịch sử qua Git thay vì lưu trực tiếp trong thư mục templates.

### 4.2. Thư Mục `scratch/` Tràn Ngập Script Tạm Thời
* Có hơn 60 tệp kịch bản kiểm thử, cào dữ liệu TikTok/Facebook và thử nghiệm nằm rải rác trong `c:\sunMy\trading_bot\scratch\`. Cần được phân loại vào thư mục lưu trữ riêng biệt để tránh làm loãng cây thư mục sản xuất.
