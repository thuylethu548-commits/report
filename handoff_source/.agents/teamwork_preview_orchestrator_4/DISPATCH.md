# Dispatch Log

## 2026-09-22T02:18:34Z
You are the Project Orchestrator for the autonomous trading system project.
Your identity: teamwork_preview_orchestrator
Working directory: c:\sunMy\trading_bot\.agents\teamwork_preview_orchestrator_4
Project root: c:\sunMy\trading_bot

Authoritative user request is recorded in:
c:\sunMy\trading_bot\.agents\ORIGINAL_REQUEST.md (under section 2026-09-22T02:15:20Z)

Please review the user request in ORIGINAL_REQUEST.md, decompose into milestones, organize specialists/subagents under .agents/, monitor implementation, verify all acceptance criteria and test suites (benchmark integrity mode), and deliver results according to protocol. Regularly update your progress.md and BRIEFING.md. When complete, submit your handoff report and notify me.

## 2026-09-22T02:33:47Z
[CHỈ THỊ BỔ SUNG TỪ GOOGLE DOC CỦA USER — ĐÃ GHI VÀO ORIGINAL_REQUEST.md (§2026-09-22T02:33:12Z)]

User yêu cầu tích hợp ngay vào PROJECT.md và toàn bộ lộ trình Milestones:
1. Target Test Case: 100 vị thế / 7 ngày với mức vốn cơ sở 50 USDT (tài khoản Binance Futures thực tế hiện có $55.44 USDT).
2. Tần suất vận hành: ~14 vị thế / ngày, quy mô lệnh an toàn $10-$14 USDT notional (ký quỹ 2 - 2.8 USDT/lệnh với đòn bẩy 5x).
3. Hội đồng Đa Tác tử Tranh biện (VAR): Phản biện đa chiều giữa các agent (Bull vs Bear vs Arbiter) lọc bẫy giả trước khi duyệt lệnh, ghi log hội thoại minh bạch như trader thực thụ.
4. Quản trị vị thế ("Thế gồng coin"): Dynamic Trailing Stop, dời Break-Even +0.2% khi lãi chạm +1.2%, House Money bảo vệ vốn khi đạt mục tiêu ngày +10 USDT (chốt lời từng phần, scale 0.2x).
5. Duy trì Hard Circuit Breaker độc lập: ngắt khẩn cấp nếu drawdown chạm -$3.50 USDT/ngày.

Hãy cập nhật ngay vào PROJECT.md, giao diện hiển thị, cấu hình bot và các kịch bản kiểm thử E2E!

## 2026-09-22T02:58:11Z
[CHỈ THỊ CẬP NHẬT TỐI CAO - 7-DAY ADAPTIVE TRADING TEST - ORIGINAL_REQUEST.md (§2026-09-22T02:57:56Z)]

Người dùng và ChatGPT đã chuẩn hóa chiến dịch:
1. TÊN CHIẾN DỊCH: "7-DAY ADAPTIVE TRADING TEST" (Initial capital = 50 USDT).
2. TRIẾT LÝ CỐT LÕI: "TRADE THE MARKET, NOT THE KPI."
   - Tuyệt đối KHÔNG ép số lượng lệnh hay target cứng.
   - Thích ứng thị trường: Cơ hội chất lượng -> trade; Thị trường nhiễu -> giảm trade; NO EDGE -> NO TRADE.
   - Nghiêm cấm: Không ép số lượng, không tăng leverage/risk để gỡ, không Martingale, không Revenge trade, không nới SL.
3. CHU TRÌNH BẮT BUỘC:
   MARKET SCAN → ANALYSIS → MULTI-AGENT DEBATE → CONFIDENCE → RISK CHECK → TRADE / NO TRADE → MONITORING → EXIT → POST-MORTEM.
4. GHI CHÉP KIỂM TOÁN (10 CÂU HỎI VÀNG):
   - WHY TRADE? / WHY THIS ASSET? / WHY THIS DIRECTION? / WHY NOW? / WHAT EVIDENCE?
   - WHAT COULD MAKE THIS WRONG? / WHAT DID THE OPPOSING AGENT SAY? / WHY WAS THE OPPOSING ARGUMENT ACCEPTED OR REJECTED?
   - WHAT WAS THE RISK? / WHAT ACTUALLY HAPPENED?
5. BÁO CÁO & ĐÁNH GIÁ:
   - DAILY REPORT & 7-DAY FINAL REPORT (PnL, Win rate, Avg R, Expectancy, Profit factor, Max DD, MAE/MFE, Disagreements, Lessons).
   - Đánh giá 6 trụ cột: Profitability + Risk Control + Decision Quality + Data Quality + Reasoning Quality + System Reliability.
6. GIAO DIỆN QUẢN TRỊ:
   - Panel View trên Admin hiển thị workflow tác tử và transcript tranh luận chi tiết cho người dùng kiểm tra mỗi tối.

Hãy tích hợp ngay các nguyên tắc này vào PROJECT.md, logic bot, database schema, và admin UI!
