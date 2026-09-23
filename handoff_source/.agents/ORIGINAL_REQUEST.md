# Original User Request

## 2026-09-17T05:15:07Z

Nâng cấp hệ thống giao dịch định lượng đa tác tử Astra Quant Desk với mô hình Claude-3.5-Sonnet (qua Vyce AI Proxy) đóng vai trò Cố Vấn Tối Cao (Veto/Approve tín hiệu kỹ thuật), tự động phân tích thị trường vĩ mô và tự động rút ra "Bài học xương máu" (Auto Post-Mortem) ghi vào SQLite khi có lệnh chạm Stop-Loss để bảo toàn vốn.

Working directory: c:\sunMy\trading_bot
Integrity mode: development

## Requirements

### R1. Live Vyce AI (Claude-3.5-Sonnet) Integration & Advisory Veto Engine
- Tích hợp mô hình `claude-3-5-sonnet` qua Vyce AI Proxy (`VYCE_BASE_URL` và `VYCE_API_KEY` đã cấu hình trên VPS).
- Đóng vai trò Cố Vấn Tối Cao (Advisory Gatekeeper): Khi các thuật toán kỹ thuật (EMA Trend, RSI Bollinger) sinh tín hiệu MUA/BÁN, AI đánh giá bối cảnh vĩ mô và chỉ cho phép lệnh đi tiếp nếu đồng thuận (hoặc phủ quyết nếu thị trường xấu/rủi ro cao).
- Tích hợp cơ chế Fallback an toàn (< 3.0s timeout): Nếu AI phản hồi chậm hoặc lỗi mạng, hệ thống tự kích hoạt fallback an toàn theo quy tắc định lượng để không gây nghẽn luồng giao dịch.

### R2. Tự Động Phân Tích & Ghi Nhận "Bài Học Xương Máu" (Auto Post-Mortem)
- Lắng nghe sự kiện khi một vị thế đóng do chạm Stop-Loss hoặc biến động trượt giá mạnh.
- Tự động gọi Claude-3.5-Sonnet để phân tích nguyên nhân kỹ thuật và bài học quản trị vốn.
- Tự động ghi nhận bài học vào bảng `trading_lessons` trong database SQLite (`trading_bot.db`).
- Dữ liệu hiển thị ngay lập tức trên giao diện `/admin/lessons` mà không cần can thiệp thủ công.

### R3. Điều Khiển & Hiển Thị Động Trên Dashboard
- Hiển thị nhận định mới nhất và chỉ số tự tin (confidence score) của Claude-3.5-Sonnet trực tiếp trên Admin Cockpit (`/admin`).
- Đồng bộ công tắc kích hoạt AI Advisory từ giao diện `/admin/settings` (Hot-Reload runtime, không cần khởi động lại server).

## Acceptance Criteria

### Automated & Unit Testing
- [ ] Toàn bộ bộ test hiện tại trong thư mục `tests/` cùng các bài test mới cho Claude-3.5-Sonnet advisory & auto post-mortem đạt 100% tỷ lệ pass.
- [ ] Có script kiểm thử kết nối trực tiếp đến endpoint Vyce AI trên môi trường VPS và nhận phản hồi hợp lệ.

### End-to-End System Verification
- [ ] Kích hoạt bot chạy trên cổng 8386, khi tín hiệu kỹ thuật xuất hiện, AI Advisory ghi nhận log phê duyệt/từ chối kèm lý do rõ ràng.
- [ ] Chạy kịch bản mô phỏng lệnh chạm Stop-Loss: bản ghi "Bài học xương máu" mới xuất hiện trong cơ sở dữ liệu SQLite và render chính xác trên trang `/admin/lessons`.
- [ ] Toàn bộ web server FastAPI và WebSocket/Polling duy trì độ trễ thấp, không bị treo giao diện trong quá trình AI gọi mạng bên ngoài.

## 2026-09-22T02:15:20Z

Nghiên cứu và chuẩn hóa hệ thống Đa Tác tử Tự chủ (Multi-Agent Teamwork) phục vụ phân tích thị trường, tranh biện phản biện đối kháng (VAR Hội đồng), tối ưu "thế gồng coin & quản trị lệnh" (Dynamic Trailing Stop, Break-Even, House Money Mode) và tự học từ kho bài học thực chiến/tâm lý giao dịch để tự động hóa ra quyết định với tỷ lệ thắng (Win Rate) cao.

Working directory: c:/sunMy/trading_bot
Integrity mode: benchmark

## Requirements

### R1. Bộ lọc Thị trường & Tổng hợp Cảnh báo Đa Tác tử (Multi-Agent Market Perception & Alert Synthesis)
Xây dựng pipeline thu thập và chuẩn hóa dữ liệu đa khung thời gian (15m, 1h, 4h), chỉ báo xu hướng (EMA Trend, RSI Bollinger), dữ liệu biến động khối lượng và các cảnh báo (alerts) kỹ thuật thành ngữ cảnh thị trường chuẩn xác trước khi chuyển tới hội đồng thẩm định.

### R2. Hội đồng Tranh biện Đối kháng Tự chủ (Autonomous Adversarial VAR Council & Consensus Engine)
Triển khai cơ chế phản biện 3 tầng giữa các tác tử độc lập (Tác tử Xu hướng - Bull Thesis, Tác tử Bóc bẫy rủi ro - Bear Devil's Advocate, và Trọng tài Lượng hóa - Supreme Arbiter) để sàng lọc bẫy giá, quét thanh khoản (liquidity hunt wicks) và tự động phê duyệt lệnh khi độ tin cậy >= 0.80 mà không cần con người can thiệp thủ công.

### R3. Giao thức "Thế gồng coin & Bảo toàn Lợi nhuận" (Dynamic Position Holding & Trailing Protocol)
Chuẩn hóa thuật toán quản trị vị thế đang mở:
- Tự động dời Stop-Loss về điểm hòa vốn (Break-Even + phí) khi vị thế đạt ngưỡng lợi nhuận tối thiểu (+1.2%).
- Kích hoạt Trailing Stop bám sát đỉnh/đáy cục bộ khi giá chạy mạnh theo xu hướng.
- Kích hoạt cơ chế House Money Mode: chốt lời từng phần tại mốc mục tiêu (+3.0% hoặc khi chạm mốc lợi nhuận ngày +10 USDT), sau đó chỉ dùng một phần nhỏ lợi nhuận đã bảo toàn (0.2x size) để tiếp tục gồng các bước sóng tiếp theo.

### R4. Tích hợp Kho tri thức Bài học Thực chiến & Tâm lý Giao dịch (Market Psychology & Community Lessons Grounding)
Kết nối các tác tử với cơ sở dữ liệu bài học thực chiến (các sai lầm tâm lý thường gặp: gồng lỗ buông xuôi, chốt non, FOMO đu đỉnh, bẫy đòn bẩy cao từ các phân tích cộng đồng đã trích xuất) để tự động đối chiếu trước mỗi quyết định vào lệnh.

### R5. Chốt chặn An toàn Lượng hóa Độc lập (Deterministic Risk Engine & Circuit Breaker)
Duy trì giới hạn an toàn cứng độc lập với AI:
- Giới hạn lỗ tối đa trong ngày không vượt quá -$3.50 USDT (Circuit Breaker ngắt khẩn cấp).
- Tối đa 2 vị thế đồng thời trên toàn danh mục, tối đa 1 vị thế cho mỗi cặp tiền.
- Chế độ dự phòng lượng hóa khẩn cấp (Quantitative Fallback) phản hồi dưới 100ms khi mất kết nối mạng hoặc AI phản hồi chậm.

## Acceptance Criteria

### Tính Độc lập & Chất lượng Tranh biện
- [ ] Hội đồng tác tử đối kháng nhận diện và phủ quyết chính xác tối thiểu 85% các kịch bản bẫy giá (bull/bear trap, fakeout) trong bộ kịch bản kiểm thử mà không làm sai lệch các tín hiệu chuẩn xu hướng.
- [ ] Phán quyết cuối cùng của Trọng tài luôn đính kèm luận điểm định lượng, điểm rủi ro (1-5) và hệ số phân bổ khối lượng (Size Multiplier).

### Vận hành Quản trị Vị thế ("Thế gồng coin")
- [ ] Vị thế mua/bán giả lập tự động kích hoạt Break-Even chính xác khi chạm mốc target +1.2%, ngăn chặn hoàn toàn rủi ro đảo chiều âm vốn.
- [ ] Trailing Stop cập nhật nấc dừng lỗ liên tục theo biến động giá mà không bị kẹt hay trễ lệnh.
- [ ] Khi đạt mục tiêu ngày (+10 USDT), hệ thống tự chuyển sang House Money Mode để bảo toàn lợi nhuận.

### Độ tin cậy & Kiểm thử Hệ thống
- [ ] 100% các bài kiểm tra tự động (test_risk_engine.py, test_paper_trader.py, test_trailing_stop.py) vượt qua hoàn hảo không có hồi quy (zero regressions).
- [ ] Hệ thống vận hành trơn tru ở cả 2 chế độ: Paper Simulation và Binance USD-M Live Futures.

## 2026-09-22T02:33:12Z

[CHỈ THỊ BỔ SUNG TỪ GOOGLE DOC CỦA USER]
Nội dung nguyên văn trích xuất từ tài liệu người dùng (https://docs.google.com/document/d/1SpCwXUR2onRlmjSzWQtsxh1b83KM1HY0t9PT5pdGvCw/edit):
"Nghiên cứu thị trường đi nha ,check ngày giờ hiện tại Việt nam và thế giới có tình hình gì biến động để thay đổi tỉ giá đồng coin không đoán xem trend long hay short giờ trade future thử xem , mình đang test case trade aim 100 vị thế/ 7 ngày để xem mức vốn 50u ban đầu thực sự hệ thống công ty Trade Universe của mình có hoạt động chuẩn tốt và tự đưa phán đoán dựa trên các thông tin không, nó có tự tìm kiếm phân tích và alert thông tin qua lại nói chuyện trò chuyện tranh luận và phản biện như những trader thực thụ?"

Yêu cầu tích hợp ngay vào PROJECT.md và lộ trình Milestone:
1. Target Test Case: 100 vị thế / 7 ngày với mức vốn cơ sở 50 USDT (hiện tại tài khoản Binance Futures đang có $55.44 USDT).
2. Tần suất vận hành: ~14 vị thế / ngày, quy mô lệnh an toàn $10-$14 USDT notional (ký quỹ 2-2.8 USDT/lệnh với đòn bẩy 5x).
3. Hội đồng Đa Tác tử Tranh biện (VAR): Phản biện đa chiều giữa các agent (Bull vs Bear vs Arbiter) lọc bẫy giả trước khi duyệt lệnh, ghi log hội thoại minh bạch.
4. Quản trị vị thế: Dynamic Trailing Stop, dời Break-Even +0.2% khi lãi +1.2%, House Money bảo vệ vốn khi đạt mục tiêu ngày +10 USDT.
5. Duy trì Hard Circuit Breaker: ngắt khẩn cấp nếu drawdown chạm -$3.50 USDT/ngày.

## 2026-09-22T02:57:56Z

[CHỈ THỊ CẬP NHẬT TỐI CAO - 7-DAY ADAPTIVE TRADING TEST]
Người dùng vừa cập nhật toàn diện tài liệu Google Doc và xác nhận với ChatGPT. Cập nhật ngay vào PROJECT.md và toàn bộ các tác tử trong hệ thống:

1. TÊN CHIẾN DỊCH: "7-DAY ADAPTIVE TRADING TEST" (Khởi động ngày 22/09/2026, initial capital = 50 USDT).
2. TRIẾT LÝ CỐT LÕI: "TRADE THE MARKET, NOT THE KPI."
   - KHÔNG ép số lượng lệnh hoặc target lợi nhuận cứng.
   - Thích ứng theo điều kiện thị trường: Có cơ hội chất lượng -> trade nhiều hơn; Thị trường nhiễu/low-opportunity -> giảm trade; Extreme volatility -> giảm size/tăng chọn lọc; NO EDGE -> NO TRADE.
   - Tuyệt đối nghiêm cấm: KHÔNG mở trade chỉ để đạt số lượng; KHÔNG tăng leverage/risk để gỡ; KHÔNG Martingale; KHÔNG Revenge trade; KHÔNG nới SL để cứu lệnh thua.
3. CHU TRÌNH BẮT BUỘC CHO MỖI CANDIDATE:
   MARKET SCAN → ANALYSIS → MULTI-AGENT DEBATE → CONFIDENCE → RISK CHECK → TRADE / NO TRADE → MONITORING → EXIT → POST-MORTEM.
4. GHI CHÉP KIỂM TOÁN CHO MỖI TRADE (10 CÂU HỎI VÀNG):
   - WHY TRADE?
   - WHY THIS ASSET?
   - WHY THIS DIRECTION?
   - WHY NOW?
   - WHAT EVIDENCE?
   - WHAT COULD MAKE THIS WRONG?
   - WHAT DID THE OPPOSING AGENT SAY?
   - WHY WAS THE OPPOSING ARGUMENT ACCEPTED OR REJECTED?
   - WHAT WAS THE RISK?
   - WHAT ACTUALLY HAPPENED?
5. BÁO CÁO:
   - Cuối mỗi ngày: DAILY REPORT.
   - Cuối 7 ngày: FINAL REPORT (PnL, Win rate, Avg R, Expectancy, Profit factor, Max DD, MAE/MFE, Disagreements, Lessons).
   - Đánh giá toàn diện 6 tiêu chí: PROFITABILITY + RISK CONTROL + DECISION QUALITY + DATA QUALITY + REASONING QUALITY + SYSTEM RELIABILITY.
6. GIAO DIỆN QUẢN TRỊ:
   - Cung cấp Panel View rõ ràng trên Admin hiển thị luồng làm việc (workflow) của các agent và nhật ký tranh luận chi tiết để người dùng kiểm tra mỗi tối.
