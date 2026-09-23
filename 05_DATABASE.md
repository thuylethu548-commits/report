# 05. CƠ SỞ DỮ LIỆU & QUẢN TRỊ TRẠNG THÁI (DATABASE ARCHITECTURE)

## 1. Nguồn Chân Lý Dữ Liệu (Source of Truth Determination)

* **Cơ sở dữ liệu chính (Primary Source of Truth):** **SQLite 3** (`c:\\sunMy\\trading_bot\\trading_bot.db`).
  * SQLite chịu trách nhiệm toàn bộ các giao dịch tài chính ACID (Atomicity, Consistency, Isolation, Durability) cấp nano-second.
  * Toàn bộ trạng thái vị thế sống còn (`execution_state`), lịch sử khớp lệnh (`trades`), tín hiệu kỹ thuật (`signals`), và bài học (`trading_lessons`) đều được lưu trữ trực tiếp trên SQLite cục bộ.
* **Hồ Dữ Liệu Định Lượng (Analytical Data Lake):** **Apache Arrow Parquet** (`data/lake/parquet/`) + **DuckDB**.
  * Dùng để lưu trữ chuỗi thời gian lớn (hàng triệu ticks), dữ liệu kịch bản mô phỏng Monte Carlo (100k+ branches) mà không làm phình to file SQLite.
* **Bản Sao Lưu Đám Mây (Cloud Telemetry Mirror):** **Supabase PostgreSQL** (`https://ldtaziouuvmcwssqmggn.supabase.co`).
  * Đóng vai trò bản sao lưu bất đồng bộ (Read-Only Mirror), giúp theo dõi từ xa qua mobile/web mà không tác động trực tiếp vào cơ sở dữ liệu giao dịch chính.

---

## 2. Bảng Thống Kê Tổng Quan Schema (23 Bảng)

| Tên Bảng | Số Cột | Khóa Chính (PK) | Số Bản Ghi Thực Tế | Mục Đích Kỹ Thuật |
| :--- | :---: | :--- | :---: | :--- |
| `affiliate_events` | 12 | `id` | 0 | Theo dõi sự kiện tiếp thị liên kết, lượt click và đăng ký qua mã giới thiệu Binance |
| `ai_advisory_logs` | 9 | `id` | 94 | Nhật ký tư vấn và phán quyết của Hội đồng AI (Regime, Risk Score, Size Multiplier, Rationale) |
| `ai_token_usage` | 8 | `id` | 3,250 | Theo dõi chi tiết số lượng token, chi phí ước tính USD và số request của từng mô hình LLM |
| `candles` | 8 | `id` | 2,353 | Lưu trữ nến lịch sử OHLCV theo từng khung thời gian phục vụ tính toán chỉ báo và backtest |
| `client_trades` | 14 | `id` | 6 | Lịch sử giao dịch sao chép (copy-trade) của từng khách hàng riêng biệt |
| `equity_snapshots` | 6 | `id` | 0 | Ảnh chụp số dư tài khoản theo chu kỳ phục vụ vẽ biểu đồ tăng trưởng vốn |
| `execution_state` | 2 | `id` | 1 | Bảng lưu trữ nguyên tử trạng thái khớp lệnh, vị thế đang mở và lệnh bảo vệ (Crash Recovery) |
| `macro_strategic_directives` | 10 | `id` | 79 | Lưu trữ 79 chỉ thị chiến lược vĩ mô do tác tử Hash ban hành sang cho Astra |
| `model_brain_benchmarks` | 10 | `model_name` | 9 | Đo lường độ trễ mạng (latency ms) và tỷ lệ thành công của từng mô hình AI |
| `project_workflows` | 13 | `id` | 10 | Quản lý tiến độ và danh sách công việc tự động của dự án |
| `research_experiments` | 13 | `id` | 2 | Các thử nghiệm nghiên cứu định lượng của Continuous Improvement Loop |
| `research_memory` | 6 | `id` | 2 | Bộ nhớ tri thức dài hạn của phòng thí nghiệm nghiên cứu AI |
| `seven_day_sprint` | 10 | `day_number` | 7 | Kế hoạch tác chiến và mục tiêu chiến dịch 7 ngày |
| `signals` | 11 | `id` | 380 | Nhật ký toàn bộ các tín hiệu kỹ thuật do chiến lược sinh ra kèm trạng thái Duyệt/Veto và lý do từ chối |
| `system_settings` | 5 | `key` | 35 | Lưu trữ các tham số vận hành có thể cấu hình linh hoạt qua giao diện Admin |
| `trade_cohort_benchmarks` | 12 | `cohort_id` | 2 | Chuẩn đối sánh hiệu suất giao dịch theo từng nhóm chiến lược |
| `trade_golden_audits` | 17 | `id` | 23 | Hồ sơ kiểm toán vàng cho các lệnh giao dịch tiêu biểu phục vụ đào tạo tác tử |
| `trades` | 14 | `order_id` | 28 | Sổ cái ghi nhận toàn bộ các lệnh giao dịch thực tế trên sàn (OPEN, CLOSED, PnL, Phí) |
| `trading_lessons` | 8 | `id` | 40 | Kho tri thức 40 bài học pháp y đúc kết từ các lệnh thắng/thua thực tế để RAG cho AI |
| `trial_positions` | 17 | `id` | 2 | Quản lý các vị thế giao dịch thử nghiệm hoặc tài khoản quỹ |
| `user_api_credentials` | 11 | `id` | 3 | Lưu trữ thông tin API key của khách hàng (được mã hóa/bảo mật) |
| `users` | 15 | `id` | 3 | Bảng tài khoản người dùng đăng nhập hệ thống Portal và phân quyền |

---

## 3. Chi Tiết Schema Các Bảng Cốt Lõi (Core Tables Specification)

### 3.1. Bảng `trades`
**Mục đích:** Sổ cái ghi nhận toàn bộ các lệnh giao dịch thực tế trên sàn (OPEN, CLOSED, PnL, Phí)  
**Số bản ghi hiện tại:** 28 rows  
**Chỉ mục (Indexes):** sqlite_autoindex_trades_1  

| CID | Tên Cột (Column) | Kiểu Dữ Liệu (Type) | Not Null | Giá Trị Mặc Định | Khóa Chính |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 0 | `order_id` | TEXT | NO | `-` | PK |
| 1 | `strategy_name` | TEXT | YES | `-` | - |
| 2 | `symbol` | TEXT | YES | `-` | - |
| 3 | `side` | TEXT | YES | `-` | - |
| 4 | `entry_price` | REAL | YES | `-` | - |
| 5 | `exit_price` | REAL | NO | `-` | - |
| 6 | `quantity` | REAL | YES | `-` | - |
| 7 | `fee` | REAL | YES | `-` | - |
| 8 | `entry_time` | TEXT | YES | `-` | - |
| 9 | `exit_time` | TEXT | NO | `-` | - |
| 10 | `pnl_usdt` | REAL | NO | `-` | - |
| 11 | `pnl_percent` | REAL | NO | `-` | - |
| 12 | `is_paper` | INTEGER | YES | `-` | - |
| 13 | `status` | TEXT | YES | `-` | - |

### 3.2. Bảng `execution_state`
**Mục đích:** Bảng lưu trữ nguyên tử trạng thái khớp lệnh, vị thế đang mở và lệnh bảo vệ (Crash Recovery)  
**Số bản ghi hiện tại:** 1 rows  
**Chỉ mục (Indexes):** Mặc định theo Primary Key  

| CID | Tên Cột (Column) | Kiểu Dữ Liệu (Type) | Not Null | Giá Trị Mặc Định | Khóa Chính |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 0 | `id` | INTEGER | NO | `-` | PK |
| 1 | `payload` | TEXT | YES | `-` | - |

### 3.3. Bảng `signals`
**Mục đích:** Nhật ký toàn bộ các tín hiệu kỹ thuật do chiến lược sinh ra kèm trạng thái Duyệt/Veto và lý do từ chối  
**Số bản ghi hiện tại:** 380 rows  
**Chỉ mục (Indexes):** Mặc định theo Primary Key  

| CID | Tên Cột (Column) | Kiểu Dữ Liệu (Type) | Not Null | Giá Trị Mặc Định | Khóa Chính |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 0 | `id` | INTEGER | NO | `-` | PK |
| 1 | `strategy_name` | TEXT | YES | `-` | - |
| 2 | `symbol` | TEXT | YES | `-` | - |
| 3 | `side` | TEXT | YES | `-` | - |
| 4 | `price` | REAL | YES | `-` | - |
| 5 | `stop_loss` | REAL | YES | `-` | - |
| 6 | `take_profit` | REAL | YES | `-` | - |
| 7 | `confidence` | REAL | YES | `-` | - |
| 8 | `timestamp` | TEXT | YES | `-` | - |
| 9 | `approved` | INTEGER | YES | `-` | - |
| 10 | `rejection_reason` | TEXT | NO | `-` | - |

### 3.4. Bảng `ai_advisory_logs`
**Mục đích:** Nhật ký tư vấn và phán quyết của Hội đồng AI (Regime, Risk Score, Size Multiplier, Rationale)  
**Số bản ghi hiện tại:** 94 rows  
**Chỉ mục (Indexes):** Mặc định theo Primary Key  

| CID | Tên Cột (Column) | Kiểu Dữ Liệu (Type) | Not Null | Giá Trị Mặc Định | Khóa Chính |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 0 | `id` | INTEGER | NO | `-` | PK |
| 1 | `symbol` | TEXT | YES | `-` | - |
| 2 | `regime` | TEXT | YES | `-` | - |
| 3 | `risk_score` | INTEGER | YES | `-` | - |
| 4 | `trade_allowed` | INTEGER | YES | `-` | - |
| 5 | `size_multiplier` | REAL | YES | `-` | - |
| 6 | `reasoning` | TEXT | NO | `-` | - |
| 7 | `timestamp` | TEXT | YES | `-` | - |
| 8 | `confidence` | REAL | NO | `1.0` | - |

### 3.5. Bảng `trading_lessons`
**Mục đích:** Kho tri thức 40 bài học pháp y đúc kết từ các lệnh thắng/thua thực tế để RAG cho AI  
**Số bản ghi hiện tại:** 40 rows  
**Chỉ mục (Indexes):** Mặc định theo Primary Key  

| CID | Tên Cột (Column) | Kiểu Dữ Liệu (Type) | Not Null | Giá Trị Mặc Định | Khóa Chính |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 0 | `id` | INTEGER | NO | `-` | PK |
| 1 | `timestamp` | TEXT | YES | `-` | - |
| 2 | `category` | TEXT | YES | `-` | - |
| 3 | `title` | TEXT | YES | `-` | - |
| 4 | `details` | TEXT | YES | `-` | - |
| 5 | `capital_impact` | REAL | NO | `-` | - |
| 6 | `lesson_learned` | TEXT | YES | `-` | - |
| 7 | `operator` | TEXT | NO | `'Astra-Supervisor'` | - |

### 3.6. Bảng `ai_token_usage`
**Mục đích:** Theo dõi chi tiết số lượng token, chi phí ước tính USD và số request của từng mô hình LLM  
**Số bản ghi hiện tại:** 3,250 rows  
**Chỉ mục (Indexes):** Mặc định theo Primary Key  

| CID | Tên Cột (Column) | Kiểu Dữ Liệu (Type) | Not Null | Giá Trị Mặc Định | Khóa Chính |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 0 | `id` | INTEGER | NO | `-` | PK |
| 1 | `timestamp` | TEXT | YES | `-` | - |
| 2 | `model` | TEXT | YES | `-` | - |
| 3 | `action` | TEXT | YES | `-` | - |
| 4 | `prompt_tokens` | INTEGER | YES | `-` | - |
| 5 | `completion_tokens` | INTEGER | YES | `-` | - |
| 6 | `total_tokens` | INTEGER | YES | `-` | - |
| 7 | `estimated_cost_usd` | REAL | YES | `-` | - |

### 3.7. Bảng `model_brain_benchmarks`
**Mục đích:** Đo lường độ trễ mạng (latency ms) và tỷ lệ thành công của từng mô hình AI  
**Số bản ghi hiện tại:** 9 rows  
**Chỉ mục (Indexes):** sqlite_autoindex_model_brain_benchmarks_1  

| CID | Tên Cột (Column) | Kiểu Dữ Liệu (Type) | Not Null | Giá Trị Mặc Định | Khóa Chính |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 0 | `model_name` | TEXT | NO | `-` | PK |
| 1 | `agent_name` | TEXT | YES | `-` | - |
| 2 | `fleet` | TEXT | YES | `-` | - |
| 3 | `total_calls` | INTEGER | NO | `0` | - |
| 4 | `success_calls` | INTEGER | NO | `0` | - |
| 5 | `error_count` | INTEGER | NO | `0` | - |
| 6 | `avg_latency_ms` | REAL | NO | `0.0` | - |
| 7 | `last_error` | TEXT | NO | `-` | - |
| 8 | `status` | TEXT | NO | `'HEALTHY'` | - |
| 9 | `updated_at` | TEXT | YES | `-` | - |

### 3.8. Bảng `macro_strategic_directives`
**Mục đích:** Lưu trữ 79 chỉ thị chiến lược vĩ mô do tác tử Hash ban hành sang cho Astra  
**Số bản ghi hiện tại:** 79 rows  
**Chỉ mục (Indexes):** sqlite_autoindex_macro_strategic_directives_1  

| CID | Tên Cột (Column) | Kiểu Dữ Liệu (Type) | Not Null | Giá Trị Mặc Định | Khóa Chính |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 0 | `id` | INTEGER | NO | `-` | PK |
| 1 | `directive_id` | TEXT | YES | `-` | - |
| 2 | `issuer` | TEXT | YES | `-` | - |
| 3 | `regime` | TEXT | YES | `-` | - |
| 4 | `venue_mandate` | TEXT | YES | `-` | - |
| 5 | `boss_capital_verdict` | TEXT | YES | `-` | - |
| 6 | `confidence` | REAL | YES | `-` | - |
| 7 | `summary_vi` | TEXT | YES | `-` | - |
| 8 | `payload` | TEXT | YES | `-` | - |
| 9 | `created_at` | TEXT | YES | `-` | - |

### 3.9. Bảng `system_settings`
**Mục đích:** Lưu trữ các tham số vận hành có thể cấu hình linh hoạt qua giao diện Admin  
**Số bản ghi hiện tại:** 35 rows  
**Chỉ mục (Indexes):** sqlite_autoindex_system_settings_1  

| CID | Tên Cột (Column) | Kiểu Dữ Liệu (Type) | Not Null | Giá Trị Mặc Định | Khóa Chính |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 0 | `key` | TEXT | NO | `-` | PK |
| 1 | `value` | TEXT | YES | `-` | - |
| 2 | `data_type` | TEXT | YES | `-` | - |
| 3 | `description` | TEXT | NO | `-` | - |
| 4 | `updated_at` | TEXT | YES | `-` | - |

### 3.10. Bảng `users`
**Mục đích:** Bảng tài khoản người dùng đăng nhập hệ thống Portal và phân quyền  
**Số bản ghi hiện tại:** 3 rows  
**Chỉ mục (Indexes):** sqlite_autoindex_users_1  

| CID | Tên Cột (Column) | Kiểu Dữ Liệu (Type) | Not Null | Giá Trị Mặc Định | Khóa Chính |
| :---: | :--- | :--- | :---: | :---: | :---: |
| 0 | `id` | INTEGER | NO | `-` | PK |
| 1 | `username` | TEXT | YES | `-` | - |
| 2 | `hashed_password` | TEXT | YES | `-` | - |
| 3 | `full_name` | TEXT | NO | `-` | - |
| 4 | `email` | TEXT | NO | `-` | - |
| 5 | `role` | TEXT | YES | `'client'` | - |
| 6 | `created_at` | TEXT | YES | `-` | - |
| 7 | `google_id` | TEXT | NO | `-` | - |
| 8 | `picture` | TEXT | NO | `-` | - |
| 9 | `registration_ip` | TEXT | NO | `'113.161.72.18'` | - |
| 10 | `last_login_ip` | TEXT | NO | `'113.161.72.18'` | - |
| 11 | `last_active_at` | TEXT | NO | `-` | - |
| 12 | `device_info` | TEXT | NO | `'Chrome 128 / Windows 11'` | - |
| 13 | `risk_flag` | TEXT | NO | `'NORMAL'` | - |
| 14 | `notes` | TEXT | NO | `-` | - |
