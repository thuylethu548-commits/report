# 04. VÒNG ĐỜI LỆNH & ĐƯỜNG ỐNG GIAO DỊCH (TRADING PIPELINE)

Tài liệu này truy vết (trace) từng bước chu trình sống của một lệnh giao dịch từ khi nến biến động đến khi chốt lời/cắt lỗ, đối soát số dư và đúc kết bài học thực tế.

---

## 1. Truy Vết Vòng Đời Lệnh Hoàn Chỉnh (Step-by-Step Order Trace)

| Bước | Hành Động | Tệp Nguồn (File) | Hàm / Lớp (Function / Class) | Chi Tiết Kỹ Thuật |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Market Data Ingestion** | `data/websocket_feed.py` | `BinanceWebSocketFeed._listen_forever()` | Thu nhận WebSocket nến 15m và tick giá từ `wss://fstream.binance.com/ws`. Đóng gói thành `MarketEvent(symbol, price, ohlcv, timestamp)`. |
| **2** | **Feature Engineering** | `strategies/ema_trend.py` | `EMATrendStrategy.on_market()` | Tính toán chỉ báo kỹ thuật: EMA-20, EMA-50, RSI-14, ATR-14 từ danh sách nến đóng cửa gần nhất. |
| **3** | **Strategy Signal** | `strategies/ema_trend.py` | `EMATrendStrategy.on_market()` | Khi EMA-20 cắt lên EMA-50 và RSI > 50, sinh `SignalEvent(symbol="BTC/USDT", side=OrderSide.BUY, price=85350, stop_loss=83800, take_profit=88450)`. |
| **4** | **Hard Risk Checks** | `risk_engine/risk_manager.py` | `RiskManager.handle_signal()` | Kiểm tra 8 chốt chặn tiền định: Circuit Breaker, Max Positions (2), Anti-Duplicate, Stop-Loss hợp lệ, MTF Confluence. Nếu trượt bất kỳ chốt nào $\rightarrow$ Hủy ngay lập tức (0ms). |
| **5** | **AI Advisory Debate** | `ai_advisory/adversarial_debater.py` | `AdversarialDebater.debate_signal()` | **VAR 3 Hiệp:**<br>• Hiệp 1: Groq LPU 120B bảo vệ lệnh.<br>• Hiệp 2: 9Router SuperGrok 4.7 bóc bẫy giá.<br>• Hiệp 3: 9Router GPT-6-Astra phán quyết `APPROVED` hoặc `VETOED`. |
| **6** | **Position Sizing** | `risk_engine/risk_manager.py` | `RiskManager.handle_signal()` (Phase 3) | Tính quy mô vốn: `allocated_usdt = (current_equity * MAX_POSITION_PERCENT) * ai_mult`. Tính số coin: `quantity = round(allocated_usdt / price, 6)`. |
| **7** | **Order Intent Creation** | `risk_engine/risk_manager.py` | `RiskManager.handle_signal()` (Phase 4) | Tạo đối tượng `OrderEvent(order_id, symbol, side, order_type=MARKET, quantity, price, stop_loss)` và phát vào `EventBus`. Lưu trạng thái duyệt vào bảng `signals`. |
| **8** | **Exchange Validation** | `execution/binance_executor.py` | `BinanceExecutor._handle_order()` | Kiểm tra Idempotency (`_submitted_ids`), kiểm tra `entries_blocked`, làm tròn số lượng qua `exchange.amount_to_precision()`, kiểm tra min amount/cost sàn Binance. |
| **9** | **Market Entry Submit** | `execution/binance_executor.py` | `BinanceExecutor._handle_order()` | Gửi lệnh Market lên Binance Futures qua `client.create_order()` với Client Order ID: `astra-<hash>`. |
| **10** | **Acknowledgement** | `execution/binance_executor.py` | `BinanceExecutor._handle_order()` | Chờ phản hồi `status == 'closed'` và nhận `filled`, `average` fill price từ Binance. Nếu timeout $\rightarrow$ đưa symbol vào `_uncertain_symbols` và khóa hệ thống. |
| **11** | **Protective Stop Order** | `execution/binance_executor.py` | `BinanceExecutor._place_protective_stop()` | **LẬP TỨC** gửi lệnh bảo vệ Stop Loss lên sàn Binance: `create_order(symbol, order_type="STOP_MARKET", amount=quantity, params={"stopPrice": stop_loss, "reduceOnly": True, "workingType": "MARK_PRICE"})`. |
| **12** | **Position Registration** | `execution/trailing_stop.py` | `TrailingStopManager.register_position()` | Đăng ký vị thế vào bộ giám sát Trailing Stop với `initial_stop_loss`, `entry_price`, `quantity`, `take_profit`. |
| **13** | **State Persistence** | `execution/binance_executor.py` | `BinanceExecutor._persist()` | Lưu toàn bộ vị thế, protective order ID, và trạng thái trailing stop vào bảng `execution_state` trong SQLite để đảm bảo an toàn nếu bot khởi động lại. |
| **14** | **Trailing & Break-Even** | `execution/trailing_stop.py` | `TrailingStopManager.update()` | Mỗi khi có tick giá mới (`MarketEvent`), nếu giá tăng quá ngưỡng Break-Even (+1.5%), dời Stop Loss về giá vào lệnh (`entry_price`). Nếu giá tiếp tục tăng, dời trailing stop bám sát đỉnh lãi. Cập nhật protective stop trên Binance qua `_place_protective_stop()`. |
| **15** | **Position Close / Exit** | `execution/binance_executor.py` | `BinanceExecutor._handle_order()` | Khi chạm SL/TP trên sàn hoặc có tín hiệu đảo chiều: Khớp lệnh đóng vị thế với cờ `reduceOnly=True`. |
| **16** | **Fee & Commission** | `execution/binance_executor.py` | `BinanceExecutor._fill_fee()` | Thu thập phí giao dịch thực tế từ phản hồi CCXT hoặc gọi `client.fetch_order_fee()`. |
| **17** | **PnL Calculation** | `execution/binance_executor.py` | `BinanceExecutor._handle_order()` | Tính toán PnL ròng: `realized_pnl = direction * (exit_price - entry_price) * filled - fee_exit - allocated_fee_entry`. Cập nhật PnL ngày vào `CircuitBreaker`. |
| **18** | **Reconciliation** | `execution/binance_executor.py` | `BinanceExecutor.sync_open_positions()` | Worker nền chạy mỗi 20 giây: Gọi `client.fetch_positions()` so sánh trực tiếp với bộ nhớ RAM và SQLite. Đồng bộ hóa trạng thái lệnh đóng trên sàn. |
| **19** | **Post-Mortem Lesson** | `ai_advisory/vyce_client.py` | `VyceClient.generate_post_mortem()` | Nếu vị thế bị cắt lỗ hoặc đóng có PnL: Kích hoạt LLM phân tích pháp y nguyên nhân, đúc kết bài học lưu vào bảng `trading_lessons`. |
| **20** | **Telegram Alert** | `monitoring/telegram_bot.py` | `TelegramNotifier.on_fill()` | Gửi tin nhắn Markdown chi tiết về Telegram: Symbol, Giá vào/ra, Khối lượng, PnL USDT (kèm màu Xanh/Đỏ), Thời gian nắm giữ, Số dư ví mới. |

---

## 2. Xác Minh 18 Yếu Tố Rủi Ro & Thực Thi Đặc Biệt

### 1. `MAX_OPEN_POSITIONS` nằm ở đâu?
* **Định nghĩa:** `config/settings.py` (mặc định: 2), được cấu hình trong bảng `system_settings` của SQLite (`MAX_OPEN_POSITIONS = 2`).
* **Thực thi:** Được kiểm tra tại 2 điểm độc lập:
  1. `risk_engine/risk_manager.py` (dòng 254): `if is_new_entry and len(self.open_positions) >= settings.MAX_OPEN_POSITIONS: return None`.
  2. `execution/binance_executor.py` (dòng 199): `if len(self.open_positions) >= settings.MAX_OPEN_POSITIONS: raise ValueError("Maximum open positions reached")`.

### 2. `risk_per_trade` tính thế nào?
* **Vị trí code:** `risk_engine/risk_manager.py` (dòng 436-444).
* **Công thức thực tế:**
  $$Equity = \text{circuit\_breaker.current\_equity or STARTING\_BALANCE\_USDT} \quad (\approx 55.0 \text{ USDT})$$
  $$Max\_Alloc = Equity \times \text{MAX\_POSITION\_PERCENT} \quad (55.0 \times 0.25 = 13.75 \text{ USDT})$$
  $$Allocated\_USDT = Max\_Alloc \times \max(0.2, \min(1.0, AI\_Multiplier))$$
  *Nếu đang ở chế độ House Money (đã đạt mục tiêu ngày +$10.00), $AI\_Multiplier$ bị giới hạn tối đa $\le 0.20$, giảm tỷ trọng lệnh xuống còn $2.75$ USDT.*
* **Trần rủi ro cứng:** Cắt gọt tiếp tại `execution/binance_executor.py` (dòng 209):
  $$Quantity = \min\left(Quantity, \frac{\text{LIVE\_MAX\_USDT\_PER\_ORDER}}{\text{Price}}\right) \quad (\text{LIVE\_MAX\_USDT\_PER\_ORDER} = 14.0 \text{ USDT})$$

### 3. `leverage` lấy ở đâu?
* **Nguồn cấu hình:** `config/settings.py` qua biến `FUTURES_LEVERAGE` (hiện tại = $6$).
* **Cài đặt lên sàn:** Gọi qua `data/binance_client.py` bằng hàm `client.set_leverage(symbol, settings.FUTURES_LEVERAGE)` khi khởi tạo hoặc trước khi đặt lệnh.

### 4. `quantity` tính thế nào?
* **Tính toán ban đầu:** `quantity = round(allocated_usdt / signal.price, 6)` tại `risk_manager.py`.
* **Hiệu chỉnh theo sàn (Authoritative Filter):** Tại `execution/binance_executor.py` (dòng 212-215):
  ```python
  market_symbol = self.client.market_symbol(order.symbol)
  quantity = float(ex.amount_to_precision(market_symbol, quantity))
  ```
* **Kiểm tra giới hạn tối thiểu:** So sánh với `limits['amount']['min']` và `limits['cost']['min']`. Nếu số lượng tính ra nhỏ hơn min amount của Binance, bot từ chối vào lệnh chứ **TUYỆT ĐỐI KHÔNG LÀM TRÒN LÊN** để tránh vi phạm ngân sách rủi ro.

### 5. `stop_loss` tính thế nào?
* **Tại chiến lược:**
  * Lệnh MUA (BUY): $\text{SL} = \text{Price} - (\text{ATR-14} \times \text{STOP\_LOSS\_ATR\_MULTIPLIER})$ (Multiplier = 1.5).
  * Lệnh BÁN (SELL): $\text{SL} = \text{Price} + (\text{ATR-14} \times \text{STOP\_LOSS\_ATR\_MULTIPLIER})$.
* **Kiểm tra biên độ an toàn tuyệt đối:** Tại `binance_executor.py` (dòng 207-208):
  ```python
  if abs(order.price - order.stop_loss) / order.price > settings.STOP_LOSS_PERCENT + 1e-9:
      raise ValueError("Entry violates mandatory hard stop distance")
  ```
  *(Khoảng cách SL không bao giờ được vượt quá `STOP_LOSS_PERCENT` = 1.8% hoặc 3.0%).*

### 6. `break_even` hoạt động thế nào?
* **Mã nguồn:** `execution/trailing_stop.py` (`TrailingStopManager.update`).
* **Cơ chế:** Khi giá thị trường di chuyển theo chiều có lãi đạt ngưỡng $\ge +1.5\%$ (hoặc theo cấu hình chiến lược), cờ `break_even_triggered` bật thành `True`. Stop Loss được lập tức dời về mức giá hòa vốn (`entry_price + buffer`), đảm bảo vị thế không bao giờ chuyển từ thắng sang lỗ. Lệnh `STOP_MARKET` trên Binance được cập nhật tương ứng.

### 7. `daily loss circuit breaker` hoạt động thế nào?
* **Mã nguồn:** `risk_engine/circuit_breaker.py`.
* **Ngưỡng kích hoạt:**
  * Lỗ ngày chạm ngưỡng: `MAX_DAILY_LOSS_USD = 3.50 USDT`.
  * Hoặc sụt giảm vốn ngày chạm: `DAILY_MAX_DRAWDOWN_PERCENT = 0.07` (7%).
* **Hậu quả:** Cờ `is_tripped` bật `True`. Mọi tín hiệu từ chiến lược bị chặn ngay từ cổng kiểm tra đầu tiên (`RiskManager` dòng 217).

### 8. `duplicate order protection` (Chống lệnh trùng lặp)?
* **Tầng 1 (Anti-Duplicate Gate):** `risk_manager.py` (dòng 261-274): Khóa tối đa 1 vị thế cho mỗi đồng coin (`MAX_POSITIONS_PER_SYMBOL = 1`).
* **Tầng 2 (Memory Idempotency):** `binance_executor.py` (dòng 178-179): `if order.order_id in self._submitted_ids: return None`.
* **Tầng 3 (Binance Client Order ID):** Sinh Client Order ID tiền định duy nhất qua mã băm SHA-256:
  `newClientOrderId = "astra-" + hashlib.sha256(order.order_id.encode()).hexdigest()[:24]`. Sàn Binance tự động từ chối nếu có 2 lệnh trùng `newClientOrderId` trong 24 giờ.

### 9. `stale market-data protection` (Bảo vệ dữ liệu giá cũ)?
* `data/websocket_feed.py` theo dõi thời gian nhận tick cuối cùng (`last_tick_time`).
* Nếu quá 60 giây không nhận được gói tin WebSocket mới từ Binance, cờ mất kết nối được bật, tạm dừng tạo tín hiệu chiến lược và tự động kích hoạt tiến trình tái kết nối.

### 10. `WebSocket reconnect` (Tái kết nối WebSocket)?
* Triển khai tại `data/websocket_feed.py` trong vòng lặp `_listen_forever()` với thuật toán Exponential Backoff (1s, 2s, 4s, 8s, tối đa 30s) khi phát hiện mất kết nối socket hoặc lỗi mạng.

### 11. `Binance REST reconciliation` (Đối soát dữ liệu REST)?
* Worker nền `_periodic_sync_worker()` trong `execution/binance_executor.py` chạy độc lập mỗi **20 giây**:
  1. Gọi `client.fetch_positions()` từ Binance Futures REST API.
  2. So sánh danh sách vị thế thực tế trên sàn với `self.open_positions` trong RAM và bảng `execution_state` trong SQLite.
  3. Nếu phát hiện vị thế đã bị thanh lý hoặc cắt lỗ ngoài sàn: lập tức cập nhật trạng thái `CLOSED` trong DB, tính toán PnL, giải phóng bộ nhớ và kích hoạt phân tích bài học `post_mortem`.
  4. Nếu phát hiện sai lệch không giải trình được: bật `entries_blocked = True` để bảo vệ vốn.

### 12. `partial fills` (Khớp lệnh một phần)?
* Tại `execution/binance_executor.py` (dòng 242-245):
  * Hệ thống kiểm tra: `if filled <= 0 or result.get("status") not in ("closed", "canceled", "expired"):`
  * Nếu lệnh chỉ khớp một phần và trạng thái vẫn là `open`, hệ thống đánh dấu biểu tượng vào `_uncertain_symbols`, bật cờ `entries_blocked = True` và yêu cầu đối soát lại trước khi tiếp tục, tránh việc tính sai khối lượng vị thế.

### 13. `rejected orders` (Xử lý lệnh bị từ chối)?
* Nếu lệnh bị RiskGate từ chối: Ghi ngay vào bảng `signals` với `approved = 0` kèm chuỗi mô tả cụ thể trong `rejection_reason`.
* Nếu lệnh bị sàn Binance từ chối (CCXT Error): Bắt biệt lệ qua khối `try...except`, ghi log mức `ERROR`, không tạo vị thế ma trong bộ nhớ.

### 14. `funding fee` (Phí Funding)?
* Được giám sát bởi `FundingSentinel` để né các đợt Funding Squeeze trước khi vào lệnh.
* Khi đóng vị thế, nếu sàn trả về phí funding trong income history, phí này được hạch toán vào PnL ròng của lệnh.

### 15. `commission` (Phí hoa hồng giao dịch)?
* Tính toán chuẩn xác trong hàm `_fill_fee(result, symbol)` tại `binance_executor.py` (dòng 153-162):
  * Trích xuất trực tiếp phí sàn thu bằng USDT/BNB từ đối tượng phản hồi CCXT (`fee.cost`).
  * Trừ trực tiếp vào công thức PnL thực nhận: $\text{PnL} = \text{Gross PnL} - \text{Fee Exit} - \text{Fee Entry}$.

### 16. `slippage` (Độ trượt giá)?
* Vì hệ thống sử dụng lệnh `MARKET` để đảm bảo khớp tức thì trong điều kiện biến động nhanh, trượt giá được tính toán bằng độ lệch giữa giá tín hiệu (`signal.price`) và giá khớp trung bình thực tế do Binance trả về (`result['average']`).
* Nếu trượt giá vượt quá mức cho phép, hệ thống ghi nhận vào nhật ký phân tích hiệu quả khớp lệnh của tác tử Meme.

### 17. `liquidation distance` (Khoảng cách giá thanh lý)?
* Được tính toán tại `risk_engine/risk_manager.py` và `core/quantum_5d_engine.py` (chiều D5).
* Với đòn bẩy $6x$ và tỷ lệ ký quỹ ban đầu, khoảng cách giá thanh lý được đảm bảo cách xa giá hiện tại ít nhất $14.5\% - 16.0\%$, triệt tiêu hoàn toàn rủi ro cháy tài khoản trước khi chạm Stop Loss cứng (1.8%).

### 18. `correlation / exposure` (Quản lý tương quan & rủi ro chéo)?
* Hiện tại hệ thống áp dụng 2 cơ chế kiểm soát phơi nhiễm:
  1. Giới hạn cứng tối đa 2 vị thế toàn danh mục (`MAX_OPEN_POSITIONS = 2`).
  2. Khóa cứng 1 vị thế duy nhất trên 1 đồng coin (`MAX_POSITIONS_PER_SYMBOL = 1`).
* *Đánh giá trung thực về Tech Debt:* Ma trận tương quan đa tài sản động (Dynamic Multi-Asset Covariance Matrix) hiện đã được tính trong `Quantum5DTensorEngine` nhưng **chưa được tích hợp đầy đủ** vào công thức định cỡ lệnh thời gian thực của `RiskManager`.
