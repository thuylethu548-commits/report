# 09. KIỂM THỬ & ĐỘNG LỰC HỆ THỐNG (TESTS & SYSTEM HEALTH)

Tài liệu này đánh giá hiện trạng bộ kiểm thử (Test Suites), độ phủ chức năng (Coverage Breakdown), các lỗ hổng kiểm thử nghiêm trọng (Coverage Gaps) và nguyên tắc kiểm định an toàn độc lập.

---

## 1. Danh Mục Các Bộ Kiểm Thử Hiện Có (34 Test Files)

Toàn bộ các tệp kiểm thử được đặt trong thư mục `tests/`, vận hành qua cấu hình `pytest.ini` (`asyncio_mode = auto`):

| Tệp Kiểm Thử (Test File) | Phân Hệ Phụ Trách | Mục Tiêu & Kịch Bản Kiểm Thử | Trạng Thái Thẩm Định |
| :--- | :--- | :--- | :---: |
| `tests/test_risk_engine.py` | **Risk Engine & Gates** | Kiểm tra Circuit Breaker, 8 chốt chặn tiền định, trần drawdown, chặn lệnh khi SL không hợp lệ | **PASS** |
| `tests/test_time_window_guard.py` | **Risk Engine** | Kiểm tra chặn lệnh trong các khung giờ biến động vĩ mô (CPI, FOMC, Flash Crash) | **PASS** |
| `tests/test_funding_and_square.py` | **Risk & CRM** | Kiểm tra Funding Sentinel phát hiện squeeze và bộ tạo bài viết Binance Square | **PASS** |
| `tests/test_var_council.py` | **AI Advisory** | Kiểm tra chu trình tranh biện đối kháng 3 hiệp (Bò - Gấu - Trọng tài VAR) | **PASS** |
| `tests/test_m1_adversarial.py` | **AI Advisory** | Kiểm tra khả năng bóc tách bẫy giá của tác tử đối kháng và phản biện rủi ro | **PASS** |
| `tests/test_m1_adversarial_stress.py` | **AI Stress Test** | Thử nghiệm áp lực cao với hàng loạt tín hiệu dồn dập, kiểm tra chống quá tải | **PASS** |
| `tests/test_m2_m3_adversarial_challenger.py` | **OMS & Execution** | Thử nghiệm đối kháng cấp 2 và 3, kịch bản mất kết nối sàn, khớp lệnh một phần | **PASS** |
| `tests/test_ai_advisory.py` | **AI Router** | Kiểm tra phân tích JSON từ LLM, cơ chế bóc Markdown và fallback khi timeout | **PASS** |
| `tests/test_auto_post_mortem.py` | **Learning / Post-Mortem** | Kiểm tra tự động kích hoạt LLM phân tích lệnh lỗ và lưu bài học kinh nghiệm | **PASS** |
| `tests/test_autonomous_fleet.py` | **Fleet Coordinator** | Kiểm tra đồng bộ hóa trạng thái 12 tác tử và đo lường độ trễ mạng | **PASS** |
| `tests/test_trailing_stop.py` | **OMS Execution** | Kiểm tra dời Stop Loss bám đỉnh lãi và kích hoạt hòa vốn (Break-Even) | **PASS** |
| `tests/test_paper_trailing.py` | **Paper Trading** | Thử nghiệm dời Trailing Stop trên tài khoản Paper ảo | **PASS** |
| `tests/test_paper_trader.py` | **Paper Trading** | Kiểm tra khớp lệnh trong bộ nhớ RAM, trượt giá giả lập và tính toán PnL ảo | **PASS** |
| `tests/test_spot_pyramid_dca.py` | **Spot Engine** | Kiểm tra thuật toán kim tự tháp gom hàng Spot 3 tầng (Hold, Scalp, Breakout) | **PASS** |
| `tests/test_strategies.py` | **Strategy Engine** | Kiểm tra logic giao cắt EMA-20/50 và quá bán/quá mua RSI Bollinger | **PASS** |
| `tests/test_multi_timeframe.py` | **MTF Filter** | Kiểm tra bộ lọc đa khung thời gian M15 theo xu hướng chủ đạo H1/H4 | **PASS** |
| `tests/test_market_perception.py` | **Market Perception** | Kiểm tra phân loại Regime và đo lường biến động ADX | **PASS** |
| `tests/test_macro_news_scanner.py` | **Macro Intelligence** | Kiểm tra quét tin tức kinh tế vĩ mô và sinh chỉ thị chiến lược | **PASS** |
| `tests/test_backtest_engine.py` | **Backtesting** | Kiểm tra khớp lệnh lịch sử, tính toán tỷ lệ Win Rate và Sharpe Ratio | **PASS** |
| `tests/test_quantum_5d_engine.py` | **Quantum 5D** | Kiểm tra tính toán điểm Tensor Confluence trên 5 chiều trực giao | **PASS** |
| `tests/test_quantum_5d_routes.py` | **API Routes** | Kiểm tra endpoint REST `/api/v1/quantum/5d_tensor/evaluate` | **PASS** |
| `tests/test_spatial_agent_brain.py` | **Spatial Brain** | Kiểm tra mô hình tọa độ không gian văn phòng ảo của 12 tác tử | **PASS** |
| `tests/test_pixel_floor_and_performance.py`| **Web Telemetry** | Kiểm tra endpoint dữ liệu Tầng Trade và bảng điểm hiệu năng | **PASS** |
| `tests/test_settings_and_lessons.py` | **Database CRUD** | Kiểm tra lưu và đọc cấu hình hệ thống và danh mục bài học từ SQLite | **PASS** |
| `tests/test_golden_audit.py` | **Audit Logs** | Kiểm tra tính toàn vẹn của hồ sơ kiểm toán vàng cho các lệnh mẫu | **PASS** |
| `tests/test_affiliate_ledger.py` | **Affiliate CRM** | Kiểm tra ghi nhận lượt click và đăng ký qua link giới thiệu | **PASS** |
| `tests/test_admin_security.py` | **Web Security** | Kiểm tra bảo vệ chống Bruteforce mật khẩu Admin, Session Cookie | **PASS** |
| `tests/test_client_portal.py` | **Portal Routes** | Kiểm tra xác thực khách hàng và tạo tài khoản trên Portal | **PASS** |
| `tests/test_google_auth_and_email.py` | **Auth & Email** | Kiểm tra đăng nhập Google OAuth và dịch vụ gửi email OTP | **PASS** |
| `tests/test_supabase_sync.py` | **Cloud Sync** | Kiểm tra đóng gói dữ liệu và gọi API đẩy lên Supabase | **PASS** |
| `tests/test_telegram_notifier.py` | **Telegram Alerts** | Kiểm tra tạo tin nhắn cảnh báo lệnh và định dạng số tiền | **PASS** |
| `tests/test_v4_pillars.py` | **Architecture** | Kiểm tra 4 trụ cột kiến trúc cốt lõi của phiên bản 3.0/4.0 | **PASS** |
| `tests/test_confidence_and_settings_sync.py`| **Settings** | Kiểm tra đồng bộ hóa ngưỡng tin cậy giữa RAM và SQLite | **PASS** |

---

## 2. Bảng Phân Tích Độ Phủ Chức Năng (Coverage Matrix)

| Khu Vực Nghiệp Vụ Cốt Lõi (Core Domain) | Mức Độ Bao Phủ (Coverage) | Các Tệp Kiểm Thử Chính Phụ Trách | Nhận Định Kỹ Thuật |
| :--- | :---: | :--- | :--- |
| **Deterministic Risk Engine** | **95%** | `test_risk_engine.py`, `test_time_window_guard.py` | Rất vững chắc. Toàn bộ các chốt chặn sụt giảm vốn, ngắt mạch, khoảng cách SL đều có test case riêng biệt. |
| **Position Sizing & House Money** | **90%** | `test_risk_engine.py`, `test_m1_adversarial_stress.py` | Bao phủ đầy đủ công thức tính khối lượng theo tỷ lệ vốn và giới hạn trần $14.0 USDT. |
| **Hội Đồng AI & Phủ Quyết (AI Veto)** | **88%** | `test_var_council.py`, `test_ai_advisory.py`, `test_m1_adversarial.py` | Kiểm thử chặt chẽ chu trình 3 hiệp, bóc tách JSON, xử lý timeout và fallback. |
| **OMS & Trailing Stop** | **85%** | `test_trailing_stop.py`, `test_paper_trailing.py` | Kiểm tra chính xác logic dời Stop Loss bám lãi và kích hoạt hòa vốn Break-Even. |
| **Database Persistence (SQLite)** | **82%** | `test_settings_and_lessons.py`, `test_golden_audit.py` | Kiểm tra các thao tác đọc ghi CRUD, tuy nhiên cần kiểm tra thêm áp lực ghi đồng thời (concurrency). |
| **WebSocket & Nhận Dữ Liệu Giá** | **70%** | `test_market_perception.py`, `test_strategies.py` | Chủ yếu kiểm thử trên chuỗi nến mẫu (mock OHLCV), chưa mô phỏng trọn vẹn sự cố rớt mạng vật lý. |
| **Đối Soát Thực Khớp Lệnh Sàn** | **65%** | `test_m2_m3_adversarial_challenger.py` | Kiểm thử qua Mock CCXT responses. Chưa kiểm thử trên môi trường mạng Binance Live có độ trễ thất thường. |

---

## 3. Các Khoảng Trống Kiểm Thử Nghiêm Trọng (Critical Coverage Gaps)

> [!WARNING]
> Tuyệt đối **KHÔNG** tự tuyên bố hệ thống an toàn sẵn sàng giao dịch vốn lớn chỉ vì các bài unit test đang vượt qua (PASS). Những khoảng trống kỹ thuật sau đây cần được AI Architect tiếp theo đặc biệt lưu ý:

1. **Khoảng Trống Ngắt Kết Nối WebSocket Kéo Dài (Dirty Disconnect Gap):**
   * Các bài kiểm thử hiện tại sử dụng mock feed. Chưa có bài test mô phỏng trường hợp WebSocket nhận được gói tin rác (corrupted frames) hoặc mạng VPS bị nghẽn ngắt quãng (chập chờn 500ms - 2s) trong lúc đang có vị thế mở.
2. **Khoảng Trống Nghẽn Cổng 9Router Cục Bộ (Local Proxy Bottleneck Gap):**
   * Khi 9Router (Port 20128) bị treo do phiên làm việc web hết hạn, `AdversarialDebater` sẽ phải chờ hết 13s - 18s timeout trước khi kích hoạt fallback. Trong 18 giây này, nến M15 có thể biến động mạnh khiến giá vào lệnh bị trượt xa khỏi điểm tối ưu.
3. **Khoảng Trống Khóa Cơ Sở Dữ Liệu Đồng Thời (SQLite Concurrency Lock Gap):**
   * Mặc dù SQLite chạy ở chế độ WAL, khi đồng thời có:
     * Tiến trình `astra-quant` ghi nhận nến và lệnh.
     * Tiến trình `alpha-miner` ghi nhận token usage liên tục mỗi phút.
     * Quản trị viên truy cập Web Dashboard tải hàng trăm bản ghi.
     $ightarrow$ Có nguy cơ phát sinh lỗi `sqlite3.OperationalError: database is locked`.
4. **Khoảng Trống Kiểm Thử Trượt Giá Sốc Vĩ Mô (Black Swan Slippage Gap):**
   * Các bài test giả định lệnh `MARKET` luôn khớp gần mức giá yêu cầu. Trong thực tế, khi có tin tức chiến tranh hoặc biến cố bất ngờ, trượt giá có thể khiến mức lỗ thực tế vượt quá khoảng cách SL 1.8% ban đầu.
