# 11. BẢNG KIỂM TOÁN SỐ LIỆU THỰC TẾ VS GIẢ LẬP (REAL VS MOCK / HARDCODED AUDIT)

Tài liệu này vạch trần chi tiết từng chỉ số trên giao diện người dùng và backend: chỉ số nào là dữ liệu THẬT (LIVE/DB), chỉ số nào được TÍNH TOÁN (CALCULATED), và chỉ số nào là GIẢ LẬP (MOCK) hoặc VIẾT CỨNG (HARDCODED/PLACEHOLDER).

---

## 1. Bảng Ma Trận Phân Loại Toàn Diện (Full Audit Matrix)

| Tính Năng / Chỉ Số (Feature / Metric) | Phân Loại Kỹ Thuật | Nguồn Thực Tế (Source Code / DB Origin) | Vị Trí Giao Diện (UI Location) | Nhận Định Kiểm Toán Chi Tiết (Audit Notes) |
| :--- | :---: | :--- | :--- | :--- |
| **Giá BTC, ETH, SOL thời gian thực** | **LIVE** | `BinanceWebSocketFeed` / CCXT REST | Cockpit, Quantum, Pixel Floor | **THẬT 100%:** Cập nhật liên tục từ WebSocket sàn Binance (`wss://fstream.binance.com/ws`). |
| **Số dư ký quỹ Futures (Margin Balance)** | **LIVE** | `binance_client.fetch_balance()` | Cockpit, Quantum Desk | **THẬT 100%:** Trích xuất trực tiếp từ API tài khoản Binance Futures của Boss. |
| **Vị thế đang mở (Open Positions)** | **LIVE / DB** | `BinanceExecutor.open_positions` & SQLite `execution_state` | Cockpit, Pixel Floor | **THẬT 100%:** Trực tiếp quản lý vị thế thực tế trên sàn (hiện tại có 1 vị thế `ETH/USDT` SHORT). |
| **Lịch sử lệnh & PnL từng lệnh** | **DB / CALCULATED**| SQLite bảng `trades` | Trades History, Analytics | **THẬT 100%:** Ghi nhận từ sự kiện khớp lệnh `FillEvent`, tính toán PnL ròng sau khi trừ phí sàn. |
| **Tỷ lệ Thắng (Win Rate) Backend** | **CALCULATED** | `data/storage.py` (`get_trades_analytics`) | API `/analytics/trades_overview` | **TÍNH TOÁN THẬT:** Dựa trên tổng số lệnh thắng / tổng số lệnh đã đóng trong bảng `trades`. |
| **Tỷ lệ Thắng trên Pixel Floor (`66.7%`)** | **PLACEHOLDER** | Viết cứng trong HTML: `id="game-panel-winrate"` | `pixel_floor.html` (dòng 2575) | **GIẢ LẬP / PLACEHOLDER:** Thẻ HTML viết sẵn `66.7%`, không được cập nhật động bằng JavaScript. |
| **Sharpe Ratio Backend** | **CALCULATED** | `core/backtest_engine.py` | API `/backtest/run` | **TÍNH TOÁN THẬT:** Tính toán độ lệch chuẩn và tỷ suất lợi nhuận trung bình trong các bài backtest. |
| **Sharpe Ratio trên Quantum Desk (`2.45`, `2.35`)** | **HARDCODED** | Viết cứng trong HTML: `id="qa-val-sharpe"`, `id="bm-sharpe"` | `quantum_cockpit.html` (L325, L711) | **VIẾT CỨNG:** Giá trị 2.45 và 2.35 nằm cố định trong mã HTML, không có hàm JS nào cập nhật. |
| **Sortino Ratio (`3.12`)** | **HARDCODED** | Viết cứng trong HTML: `id="qa-val-sortino"` | `quantum_cockpit.html` (dòng 720) | **PLACEHOLDER HOÀN TOÀN:** Không có công thức tính Sortino nào trong database hay backend API. |
| **Calmar Ratio (`2.84`)** | **HARDCODED** | Viết cứng trong HTML: `id="qa-val-calmar"` | `quantum_cockpit.html` (dòng 724) | **PLACEHOLDER HOÀN TOÀN:** Giá trị 2.84 là số cố định nhằm mục đích dựng khung giao diện UI. |
| **Sụt Giảm Ngày (Drawdown %)** | **CALCULATED** | `risk_engine/circuit_breaker.py` | Cockpit (`id="kpi-drawdown"`) | **TÍNH TOÁN THẬT:** Tính theo công thức `daily_realized_pnl / current_equity` từ các lệnh đóng hôm nay. |
| **Phân Bố Xác Suất Đuôi (Tail Probability)** | **HARDCODED** | Viết cứng: `rm-tail-mass = 3.8%`, `rm-implied-vol = 24.8%`, `rm-avg-entry = $80,970` | `quantum_cockpit.html` (L376-395) | **PLACEHOLDER:** Toàn bộ 6 thẻ chỉ số và nút chọn khung thời gian `switchRidgeTf` đều là mock tĩnh. |
| **Mạng Lưới Chuyển Giao Lệnh (Handoff Chord)** | **HARDCODED** | Bảng HTML tĩnh: Prof $\rightarrow$ Astra (342 lần, 0.91, +2.8%) | `quantum_cockpit.html` (L931-955) | **PLACEHOLDER:** Dữ liệu bảng viết cứng trong `<tbody>`, thẻ `<canvas id="chordCanvas">` để trống. |
| **Số Tác Tử Trực Tuyến (12/12 Agent Online)** | **HARDCODED / DB**| `AutonomousFleetCoordinator.AGENT_METADATA` | Pixel Floor, Quantum Desk | **BÁN THẬT:** Danh mục 12 tác tử là cấu hình tĩnh; trong mã nguồn chỉ có 3-5 tác tử gọi API LLM thực tế. |
| **Chế Độ Thị Trường (Market Regime)** | **LIVE** | `MarketRegimeClassifier` & `AdversarialDebater` | Cockpit, Quantum | **THẬT 100%:** Trả về từ suy luận LLM thời gian thực (`BULL_TREND`, `BEAR_TREND`, `RANGING`...). |
| **Độ Tin Cậy Lệnh (Confidence %)** | **LIVE** | Trích xuất từ JSON phán quyết của Trọng tài VAR | Cockpit, Audit Logs | **THẬT 100%:** Trích xuất từ trường `"confidence": 0.85` do mô hình LLM sinh ra trong mỗi phiên tranh biện. |
| **Số Lượng Token & Chi Phí USD** | **DB** | SQLite bảng `ai_token_usage` | Performance, Quota Modal | **THẬT 100%:** Bảng `ai_token_usage` ghi nhận hơn 3,249 dòng chi tiết từng request, token và chi phí. |
| **Bảng Hiệu Năng Mô Hình (MODEL_META)** | **HARDCODED FALLBACK** | Viết cứng trong `data/storage.py` (L1250) | `performance.html` | **KẾT HỢP:** Nếu DB rỗng, sử dụng metadata cứng (`latency: 45ms`, `success: 99.8%`, `veto_acc: 98.5%`). |
| **Mô Phỏng 10,000 Kịch Bản trong 0.48s** | **CALCULATED (RAM)** | `core/hyper_simulation_world.py` | API `/simulation/run` | **THUẬT TOÁN BỘ NHỚ:** Chạy vòng lặp `for` 10,000 lần trong RAM với hàm ngẫu nhiên `random.uniform()`. |
| **Dự Phóng Viện Tiên Tri (Market Oracle)** | **LIVE LLM** | `MarketOracleEngine.generate_macro_forecast()` | API `/simulation/oracle` | **THẬT 100%:** Gọi trực tiếp `cx/gpt-6-astra` hoặc `gcli/grok-4.7` để sinh bài luận dự phóng vĩ mô dài hạn. |

---

## 2. Kết Luận Kiểm Toán Dữ Liệu (Auditor Summary)

1. **Khối Lệnh & Tài Chính:** **100% DỮ LIỆU THẬT.** Toàn bộ các con số liên quan đến số dư Binance, vị thế mở, lệnh Stop Loss, lịch sử khớp lệnh và kiểm soát sụt giảm vốn Circuit Breaker đều là dữ liệu thực tế và tính toán toán học chính xác.
2. **Khối Hội Đồng AI:** **100% SUY LUẬN THẬT.** Quá trình tranh biện đối kháng 3 hiệp giữa Groq LPU, SuperGrok và GPT-6-Astra thực sự diễn ra qua API HTTP, sinh token và ghi nhận chi phí vào bảng `ai_token_usage`.
3. **Khối Trực Quan Hóa Đồ Họa Nâng Cao:** **MOCK / PLACEHOLDER.** Một số biểu đồ phức tạp như *Handoff Chord Diagram* và *Tail Probability Ridge* trên trang `quantum_cockpit.html` hiện tại chỉ đóng vai trò khung giao diện mẫu (UI wireframe) chứa các giá trị số cứng, chưa được nối luồng dữ liệu tính toán thời gian thực từ backend.
