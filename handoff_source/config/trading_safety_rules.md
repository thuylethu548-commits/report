# 🛡️ 6 THIẾT LUẬT QUẢN TRỊ RỦI RO BẤT DI BẤT DỊCH (ASTRA PERMANENT TRADING SAFETY RULES)

Tài liệu này là quy tắc tối cao (Ironclad Mandate) bắt buộc mọi thành phần trong hệ thống **Astra Quant Desk** (Bao gồm thuật toán kỹ thuật, Hội đồng Cố vấn AI, và con người vận hành) phải tuân thủ nghiêm ngặt trong mọi tình huống.

---

### Điều 1: Hạn Mức Rủi Ro Tối Đa Trên Mỗi Vị Thế (1.5% Hard Risk Cap)
- **Quy tắc**: Không bao giờ để một vị thế thua lỗ vượt quá **1.5%** giá trị danh nghĩa của tài sản.
- **Thực thi**: Lệnh Stop-Loss bắt buộc phải được tính toán tự động và gắn liền với lệnh mở ngay tại thời điểm gửi lên sàn. Nghiêm cấm gồng lỗ hoặc nới rộng Stop-Loss khi giá đang đi ngược hướng.

---

### Điều 2: Tỷ Lệ Phân Bổ Ký Quỹ An Toàn (Margin Sizing Limit)
- **Quy tắc**: Vốn ký quỹ (Margin) cho một lệnh duy nhất không bao giờ được vượt quá **10% - 15%** tổng vốn khả dụng trong ví.
- **Thực thi**: Nghiêm cấm hành vi All-in (tất tay) dù tín hiệu kỹ thuật hay AI có đánh giá độ tin cậy cao đến 99%. Luôn giữ dự trữ thanh khoản để đối phó với biến động thiên nga đen.

---

### Điều 3: Cầu Dao Ngắt Khẩn Cấp Cấp Độ Quỹ (Daily Circuit Breaker -5%)
- **Quy tắc**: Nếu tổng mức sụt giảm tài sản (Daily Drawdown) trong vòng 24 giờ chạm ngưỡng **-5.0%** tổng vốn:
  - Cầu dao `CircuitBreaker` tự động kích hoạt lập tức.
  - Đóng toàn bộ các vị thế đang mở theo giá thị trường.
  - Hủy toàn bộ lệnh chờ (Pending Orders).
  - Khóa quyền mở lệnh mới trong 24 giờ tiếp theo để bảo vệ 95% vốn gốc còn lại.

---

### Điều 4: Khóa Hòa Vốn (Break-Even Lock) & Trailing Stop
- **Quy tắc**: Một vị thế đã sinh lời thì tuyệt đối không được phép biến thành vị thế thua lỗ.
- **Thực thi**:
  - Khi lợi nhuận đạt $\ge +1.2\%$, Stop-Loss tự động dời lên mức `Entry + 0.1%` (hòa vốn + bù phí sàn).
  - Khi lợi nhuận đạt $\ge +2.0\%$, kích hoạt Trailing Stop bám theo đỉnh giá mới với khoảng cách 1.0x ATR.

---

### Điều 5: Dead-Trade Timer (Quy Tắc Đóng Lệnh Chết)
- **Quy tắc**: Không giam vốn trong các lệnh đi ngang không phát triển sóng.
- **Thực thi**: Nếu vị thế mở quá **120 phút (2 giờ)** mà chưa chạm Take-Profit nhưng đang có lãi chớm xanh ($\ge +0.2\%$), hệ thống kích hoạt `DEAD_TRADE_PROFIT_LOCK` kéo SL về điểm hòa vốn hoặc chủ động đóng lệnh hòa để giải phóng margin cho cơ hội tốt hơn.

---

### Điều 6: Bảo Mật Phi Lưu Ký Tuyệt Đối (Non-Custodial API Protocol)
- **Quy tắc**: Tiền của ai người đó giữ. Hệ thống chỉ thực thi tín hiệu toán học qua API, không bao giờ nhận giữ tiền của khách hàng hay người thân.
- **Thực thi**:
  - API Key chỉ được phép kích hoạt quyền: `Can Read` (Đọc) và `Enable Futures` (Giao dịch Hợp đồng).
  - **TUYỆT ĐỐI KHÔNG BẬT QUYỀN `Enable Withdrawals` (Rút tiền)**.
  - Toàn bộ API Key và Secret của người dùng phải được mã hóa chuẩn quân sự trước khi lưu vào cơ sở dữ liệu.
